import os
import logging
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from .deebot_manager import DeebotManager, VacuumStatus

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

deebot_manager: Optional[DeebotManager] = None

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
    
    deebot_manager = DeebotManager(
        email=email,
        password=password,
        country=country,
        continent=continent
    )
    
    # Start API service without requiring successful device initialization
    # This allows us to test different configurations and troubleshoot
    logger.info(f"API service starting with region: {country}/{continent}")
    logger.info("Device initialization will be attempted on first API call")
    
    yield
    
    if deebot_manager:
        try:
            await deebot_manager.disconnect()
        except:
            pass

app = FastAPI(
    title="Robo-Bridge API",
    description="API for controlling Ecovacs Deebot vacuum cleaners",
    version="1.0.0",
    lifespan=lifespan
)

def get_deebot_manager() -> DeebotManager:
    if deebot_manager is None:
        raise HTTPException(status_code=503, detail="Deebot manager not initialized")
    return deebot_manager

@app.get("/health", response_model=HealthResponse)
async def health_check():
    if deebot_manager is None:
        return HealthResponse(
            status="unhealthy",
            devices_connected=0,
            message="Deebot manager not initialized"
        )
    
    try:
        # Try to initialize if not already done
        if not hasattr(deebot_manager, 'api_client') or deebot_manager.api_client is None:
            await deebot_manager.initialize()
        
        devices = await deebot_manager.get_devices()
        return HealthResponse(
            status="healthy",
            devices_connected=len(devices),
            message=f"Connected to {len(devices)} devices"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            devices_connected=0,
            message=str(e)
        )

@app.get("/devices", response_model=List[DeviceInfo])
async def get_devices(manager: DeebotManager = Depends(get_deebot_manager)):
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
        logger.error(f"Failed to get devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")

@app.get("/devices/{device_id}/status", response_model=DeviceInfo)
async def get_device_status(device_id: str, manager: DeebotManager = Depends(get_deebot_manager)):
    try:
        status = await manager.get_device_status(device_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
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
        logger.error(f"Failed to get device status for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve device status")

@app.post("/devices/{device_id}/start", response_model=CommandResponse)
async def start_cleaning(device_id: str, manager: DeebotManager = Depends(get_deebot_manager)):
    try:
        success = await manager.start_cleaning(device_id)
        return CommandResponse(
            success=success,
            message="Cleaning started successfully" if success else "Failed to start cleaning",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to start cleaning for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start cleaning")

@app.post("/devices/{device_id}/stop", response_model=CommandResponse)
async def stop_cleaning(device_id: str, manager: DeebotManager = Depends(get_deebot_manager)):
    try:
        success = await manager.stop_cleaning(device_id)
        return CommandResponse(
            success=success,
            message="Cleaning stopped successfully" if success else "Failed to stop cleaning",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to stop cleaning for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop cleaning")

@app.post("/devices/{device_id}/pause", response_model=CommandResponse)
async def pause_cleaning(device_id: str, manager: DeebotManager = Depends(get_deebot_manager)):
    try:
        success = await manager.pause_cleaning(device_id)
        return CommandResponse(
            success=success,
            message="Cleaning paused successfully" if success else "Failed to pause cleaning",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to pause cleaning for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause cleaning")

@app.post("/devices/{device_id}/dock", response_model=CommandResponse)
async def return_to_dock(device_id: str, manager: DeebotManager = Depends(get_deebot_manager)):
    try:
        success = await manager.return_to_dock(device_id)
        return CommandResponse(
            success=success,
            message="Return to dock command sent successfully" if success else "Failed to send return to dock command",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to return device {device_id} to dock: {e}")
        raise HTTPException(status_code=500, detail="Failed to return to dock")

@app.post("/devices/{device_id}/locate", response_model=CommandResponse)
async def locate_device(device_id: str, manager: DeebotManager = Depends(get_deebot_manager)):
    try:
        success = await manager.locate_device(device_id)
        return CommandResponse(
            success=success,
            message="Locate command sent successfully" if success else "Failed to send locate command",
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Failed to locate device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to locate device")

@app.post("/test-config")
async def test_configuration(country: str, continent: str):
    """Test different region configurations for Ecovacs authentication"""
    global deebot_manager
    
    if not deebot_manager:
        raise HTTPException(status_code=503, detail="Deebot manager not available")
    
    # Update region settings
    deebot_manager.country = country
    deebot_manager.continent = continent
    
    try:
        # Reset API client to force re-initialization with new settings
        deebot_manager.api_client = None
        deebot_manager.authenticator = None
        
        await deebot_manager.initialize()
        devices = await deebot_manager.get_devices()
        
        return {
            "success": True,
            "country": country,
            "continent": continent,
            "devices_found": len(devices),
            "message": f"Successfully connected with {country}/{continent}"
        }
    except Exception as e:
        return {
            "success": False,
            "country": country,
            "continent": continent,
            "error": str(e),
            "message": f"Failed to connect with {country}/{continent}"
        }

@app.get("/debug-auth")
async def debug_authentication():
    """Debug authentication details"""
    global deebot_manager
    
    if not deebot_manager:
        return {"error": "Deebot manager not available"}
    
    try:
        # Import deebot_client version info
        import deebot_client
        version = getattr(deebot_client, '__version__', 'unknown')
        
        return {
            "deebot_client_version": version,
            "country": deebot_manager.country,
            "continent": deebot_manager.continent,
            "email_domain": deebot_manager.email.split('@')[1],
            "has_authenticator": deebot_manager.authenticator is not None,
            "has_api_client": deebot_manager.api_client is not None,
            "devices_count": len(deebot_manager.devices)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {
        "message": "Robo-Bridge API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "test_config": "/test-config"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)