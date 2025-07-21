import os
import logging
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from .deebot_t8_manager import DeebotT8Manager, VacuumStatus

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandResponse(BaseModel):
    success: bool
    message: str
    device_id: str

class DeviceInfo(BaseModel):
    device_id: str
    name: str
    online: bool
    battery_level: Optional[int] = None
    cleaning_state: Optional[str] = None
    error_message: Optional[str] = None
    last_updated: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    devices_connected: int
    message: str
    library: str = "deebot-t8"

deebot_manager: Optional[DeebotT8Manager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global deebot_manager
    
    email = os.getenv("ECOVACS_EMAIL")
    password = os.getenv("ECOVACS_PASSWORD")
    country = os.getenv("ECOVACS_COUNTRY", "US")
    continent = os.getenv("ECOVACS_CONTINENT", "NA")
    
    if not email or not password:
        logger.error("ECOVACS_EMAIL and ECOVACS_PASSWORD environment variables are required")
        raise ValueError("Missing required environment variables")
    
    deebot_manager = DeebotT8Manager(
        email=email,
        password=password,
        country=country,
        continent=continent
    )
    
    logger.info(f"T8 API service starting with region: {country}/{continent}")
    logger.info("T8 device initialization will be attempted on first API call")
    
    yield
    
    if deebot_manager:
        try:
            await deebot_manager.disconnect()
        except:
            pass

app = FastAPI(
    title="Robo-Bridge T8 API",
    description="Alternative API using deebot-t8 library for Ecovacs T8 series vacuum cleaners",
    version="1.0.0-t8",
    lifespan=lifespan
)

def get_deebot_manager() -> DeebotT8Manager:
    if deebot_manager is None:
        raise HTTPException(status_code=503, detail="T8 Deebot manager not initialized")
    return deebot_manager

@app.get("/health", response_model=HealthResponse)
async def health_check():
    if deebot_manager is None:
        return HealthResponse(
            status="unhealthy",
            devices_connected=0,
            message="T8 Deebot manager not initialized",
            library="deebot-t8"
        )
    
    try:
        # Try to initialize if not already done
        if not hasattr(deebot_manager, 'client') or deebot_manager.client is None:
            await deebot_manager.initialize()
        
        devices = await deebot_manager.get_devices()
        return HealthResponse(
            status="healthy",
            devices_connected=len(devices),
            message=f"Connected to {len(devices)} T8 devices",
            library="deebot-t8"
        )
    except Exception as e:
        logger.error(f"T8 health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            devices_connected=0,
            message=f"T8 Error: {str(e)}",
            library="deebot-t8"
        )

@app.get("/devices", response_model=List[DeviceInfo])
async def get_devices(manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        devices = await manager.get_devices()
        return [
            DeviceInfo(
                device_id=device.device_id,
                name=device.name,
                online=device.online,
                battery_level=device.battery_level,
                cleaning_state=device.cleaning_state,
                error_message=device.error_message,
                last_updated=device.last_updated
            )
            for device in devices
        ]
    except Exception as e:
        logger.error(f"Failed to get T8 devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve T8 devices")

@app.get("/devices/{device_id}/status", response_model=DeviceInfo)
async def get_device_status(device_id: str, manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        status = await manager.get_device_status(device_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"T8 Device {device_id} not found")
        
        return DeviceInfo(
            device_id=status.device_id,
            name=status.name,
            online=status.online,
            battery_level=status.battery_level,
            cleaning_state=status.cleaning_state,
            error_message=status.error_message,
            last_updated=status.last_updated
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get T8 device status for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve T8 device status")

@app.post("/devices/{device_id}/start", response_model=CommandResponse)
async def start_cleaning(device_id: str, manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        success = await manager.start_cleaning(device_id)
        return CommandResponse(
            success=success,
            message="T8 cleaning started successfully" if success else "Failed to start T8 cleaning",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to start T8 cleaning for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start T8 cleaning")

@app.post("/devices/{device_id}/stop", response_model=CommandResponse)
async def stop_cleaning(device_id: str, manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        success = await manager.stop_cleaning(device_id)
        return CommandResponse(
            success=success,
            message="T8 cleaning stopped successfully" if success else "Failed to stop T8 cleaning",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to stop T8 cleaning for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop T8 cleaning")

@app.post("/devices/{device_id}/pause", response_model=CommandResponse)
async def pause_cleaning(device_id: str, manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        success = await manager.pause_cleaning(device_id)
        return CommandResponse(
            success=success,
            message="T8 cleaning paused successfully" if success else "Failed to pause T8 cleaning",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to pause T8 cleaning for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause T8 cleaning")

@app.post("/devices/{device_id}/dock", response_model=CommandResponse)
async def return_to_dock(device_id: str, manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        success = await manager.return_to_dock(device_id)
        return CommandResponse(
            success=success,
            message="T8 return to dock command sent successfully" if success else "Failed to send T8 return to dock command",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to return T8 device {device_id} to dock: {e}")
        raise HTTPException(status_code=500, detail="Failed to return T8 to dock")

@app.post("/devices/{device_id}/locate", response_model=CommandResponse)
async def locate_device(device_id: str, manager: DeebotT8Manager = Depends(get_deebot_manager)):
    try:
        success = await manager.locate_device(device_id)
        return CommandResponse(
            success=success,
            message="T8 locate command sent successfully" if success else "Failed to send T8 locate command",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to locate T8 device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to locate T8 device")

@app.get("/debug-t8")
async def debug_t8_library():
    """Debug T8 library details"""
    global deebot_manager
    
    if not deebot_manager:
        return {"error": "T8 Deebot manager not available"}
    
    try:
        # Import deebot_t8 version info if available
        try:
            import deebot_t8
            version = getattr(deebot_t8, '__version__', 'unknown')
        except:
            version = 'unknown'
        
        return {
            "library": "deebot-t8",
            "version": version,
            "country": deebot_manager.country,
            "continent": deebot_manager.continent,
            "email_domain": deebot_manager.email.split('@')[1],
            "has_client": deebot_manager.client is not None,
            "devices_count": len(deebot_manager.devices),
            "device_ids": list(deebot_manager.devices.keys())
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {
        "message": "Robo-Bridge T8 API",
        "version": "1.0.0-t8",
        "library": "deebot-t8",
        "docs": "/docs",
        "health": "/health",
        "debug": "/debug-t8"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port to avoid conflicts