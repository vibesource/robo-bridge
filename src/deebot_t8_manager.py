import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from deebot_t8 import Client as DeebotT8Client
from deebot_t8.exceptions import AuthenticationException, CommandException

logger = logging.getLogger(__name__)

@dataclass
class VacuumStatus:
    device_id: str
    name: str
    online: bool
    battery_level: Optional[int] = None
    cleaning_state: Optional[str] = None
    error_message: Optional[str] = None
    last_updated: Optional[str] = None

class DeebotT8Manager:
    def __init__(self, email: str, password: str, country: str = "US", continent: str = "NA"):
        self.email = email
        self.password = password
        self.country = country
        self.continent = continent
        self.client = None
        self.devices: Dict[str, dict] = {}
        self.device_status: Dict[str, VacuumStatus] = {}
        
    async def initialize(self):
        try:
            logger.info(f"Initializing Deebot T8 manager for region: {self.country}/{self.continent}")
            logger.info(f"Email: {self.email[:3]}***@{self.email.split('@')[1]}")
            
            # Initialize the deebot-t8 client
            self.client = DeebotT8Client(
                username=self.email,
                password=self.password,
                country=self.country,
                continent=self.continent
            )
            
            logger.info("Authenticating with Ecovacs cloud...")
            await self.client.authenticate()
            logger.info("Authentication successful!")
            
            logger.info("Discovering devices...")
            await self._discover_devices()
            logger.info(f"Initialization complete - found {len(self.devices)} devices")
            
        except AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            logger.error("Check your email/password and region settings")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Deebot T8 manager: {e}")
            logger.error(f"Check your .env file credentials and ensure robots are online in Ecovacs app")
            import traceback
            logger.error(f"Full initialization traceback: {traceback.format_exc()}")
            raise
    
    async def _discover_devices(self):
        try:
            logger.info("Calling client.get_devices()...")
            devices = await self.client.get_devices()
            logger.info(f"T8 API returned devices list: {devices}")
            logger.info(f"Number of devices returned: {len(devices) if devices else 0}")
            
            if not devices or len(devices) == 0:
                logger.warning("No devices found with deebot-t8 library!")
                logger.warning("This could indicate:")
                logger.warning("- T8 Pure/U2 models not supported by this library")
                logger.warning("- Account/region configuration issues")
                logger.warning("- Library compatibility problems")
                return
            
            for i, device in enumerate(devices):
                logger.info(f"Processing T8 device {i+1}: {device}")
                logger.info(f"Device type: {type(device)}")
                logger.info(f"Device attributes: {dir(device)}")
                
                # Try to extract device information
                device_id = getattr(device, 'id', getattr(device, 'device_id', f'unknown_{i}'))
                device_name = getattr(device, 'name', getattr(device, 'nick', f'T8 Device {device_id}'))
                
                logger.info(f"Device ID: {device_id}, Name: {device_name}")
                
                self.devices[device_id] = device
                self.device_status[device_id] = VacuumStatus(
                    device_id=device_id,
                    name=device_name,
                    online=True  # Assume online if discovered
                )
                
            logger.info(f"Successfully processed {len(self.devices)} T8 devices")
            
        except Exception as e:
            logger.error(f"Failed to discover T8 devices: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {repr(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def get_devices(self) -> List[VacuumStatus]:
        return list(self.device_status.values())
    
    async def get_device_status(self, device_id: str) -> Optional[VacuumStatus]:
        if device_id not in self.devices:
            return None
        
        # Try to update status from device
        try:
            device = self.devices[device_id]
            # Note: deebot-t8 API methods may differ from deebot-client
            # We'll need to check the actual API once we test
            status = self.device_status[device_id]
            status.last_updated = str(asyncio.get_event_loop().time())
            return status
        except Exception as e:
            logger.error(f"Failed to get T8 device status for {device_id}: {e}")
            return self.device_status.get(device_id)
    
    async def start_cleaning(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"T8 Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            # Note: Actual method name may differ in deebot-t8
            await device.start_cleaning()
            logger.info(f"Started cleaning on T8 device {device_id}")
            return True
        except CommandException as e:
            logger.error(f"Command failed for T8 device {device_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to start cleaning on T8 device {device_id}: {e}")
            return False
    
    async def stop_cleaning(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"T8 Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.stop_cleaning()
            logger.info(f"Stopped cleaning on T8 device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop cleaning on T8 device {device_id}: {e}")
            return False
    
    async def return_to_dock(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"T8 Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.return_to_dock()
            logger.info(f"Sent return to dock command to T8 device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to return T8 device {device_id} to dock: {e}")
            return False
    
    async def pause_cleaning(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"T8 Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.pause_cleaning()
            logger.info(f"Paused cleaning on T8 device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause cleaning on T8 device {device_id}: {e}")
            return False
    
    async def locate_device(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"T8 Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.play_sound()
            logger.info(f"Sent locate command to T8 device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to locate T8 device {device_id}: {e}")
            return False
    
    async def disconnect(self):
        try:
            if self.client:
                await self.client.disconnect()
            logger.info("Disconnected from T8 client")
        except Exception as e:
            logger.error(f"Error during T8 disconnect: {e}")