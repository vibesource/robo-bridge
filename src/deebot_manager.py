import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import aiohttp
from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.device import Device
from deebot_client.events import BatteryEvent
from deebot_client.commands.json.clean import Clean, CleanAction
from deebot_client.commands.json.charge import Charge
from deebot_client.commands.json.play_sound import PlaySound
from deebot_client.util import md5

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

class DeebotManager:
    def __init__(self, email: str, password: str, country: str = "US", continent: str = "NA"):
        self.email = email
        self.password = password
        self.country = country
        self.continent = continent
        self.authenticator = None
        self.api_client = None
        self.devices: Dict[str, Device] = {}
        self.device_status: Dict[str, VacuumStatus] = {}
        
    async def initialize(self):
        try:
            logger.info(f"Initializing Deebot manager for country: {self.country}, continent: {self.continent}")
            
            password_hash = md5(self.password)
            logger.info(f"Password hash: {password_hash[:8]}...")
            
            session = aiohttp.ClientSession()
            # Use a dummy device_id for authentication - this will be replaced during actual device discovery
            import uuid
            dummy_device_id = str(uuid.uuid4())[:8]
            config = create_rest_config(session, device_id=dummy_device_id, alpha_2_country=self.country)
            logger.info(f"Created REST config: {config}")
            
            logger.info(f"Creating authenticator for email: {self.email[:3]}***@{self.email.split('@')[1]}")
            self.authenticator = Authenticator(config, self.email, password_hash)
            
            logger.info("Creating API client...")
            self.api_client = ApiClient(self.authenticator)
            
            logger.info("Starting device discovery...")
            await self._discover_devices()
            logger.info(f"Initialization complete - found {len(self.devices)} devices")
            
        except Exception as e:
            logger.error(f"Failed to initialize Deebot manager: {e}")
            logger.error(f"Check your .env file credentials and ensure robots are online in Ecovacs app")
            import traceback
            logger.error(f"Full initialization traceback: {traceback.format_exc()}")
            raise
    
    async def _discover_devices(self):
        try:
            logger.info("Attempting to authenticate and discover devices...")
            logger.info("Calling api_client.get_devices()...")
            devices = await self.api_client.get_devices()
            logger.info(f"API returned devices object: {devices}")
            logger.info(f"Devices object type: {type(devices)}")
            
            # Extract actual DeviceInfo objects from the Devices container
            if hasattr(devices, 'mqtt') and devices.mqtt:
                device_list = devices.mqtt  # These are the actual DeviceInfo objects
            elif hasattr(devices, 'devices'):
                device_list = devices.devices
            elif hasattr(devices, '__iter__') and not isinstance(devices, str):
                device_list = list(devices)
            else:
                device_list = [devices] if devices else []
            
            logger.info(f"Device list: {device_list}")
            logger.info(f"Number of devices found: {len(device_list)}")
            
            if len(device_list) == 0:
                logger.warning("No devices found! This could indicate:")
                logger.warning("- Devices not properly registered in the Ecovacs app")
                logger.warning("- Account mismatch between app and API credentials")
                logger.warning("- Regional server differences")
                logger.warning("- Library compatibility issues")
            
            for i, device in enumerate(device_list):
                logger.info(f"Processing device {i+1}: {device}")
                logger.info(f"Device type: {type(device)}")
                logger.info(f"Device attributes: {dir(device)}")
                
                # Extract device info from DeviceInfo object structure
                if hasattr(device, 'api') and isinstance(device.api, dict):
                    device_id = device.api.get('did', f'unknown_{i}')
                    device_name = device.api.get('nick', device.api.get('deviceName', f'Deebot {device_id}'))
                else:
                    device_id = getattr(device, 'device_id', f'unknown_{i}')
                    device_name = getattr(device, 'name', f'Deebot {device_id}')
                
                logger.info(f"Device ID: {device_id}, Name: {device_name}")
                
                # Create actual Device object from DeviceInfo for command execution
                try:
                    actual_device = Device(device, self.authenticator)
                    self.devices[device_id] = actual_device
                    logger.info(f"Created Device object for {device_id} ({device_name})")
                    
                    # Subscribe to battery events with device-specific handler
                    battery_handler = self._create_battery_event_handler(device_id)
                    actual_device.events.subscribe(BatteryEvent, battery_handler)
                    logger.info(f"Subscribed to battery events for {device_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to create Device object for {device_id}: {e}")
                    # Still store the DeviceInfo for basic information
                    self.devices[device_id] = device
                
                self.device_status[device_id] = VacuumStatus(
                    device_id=device_id,
                    name=device_name,
                    online=False
                )
                
                logger.info(f"Device {device_id} ({device_name}) added to device list")
                
            logger.info(f"Successfully processed {len(self.devices)} devices")
            
        except Exception as e:
            logger.error(f"Failed to discover devices: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {repr(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _create_battery_event_handler(self, device_id: str):
        """Create a battery event handler for a specific device"""
        async def handler(event: BatteryEvent):
            if device_id in self.device_status:
                status = self.device_status[device_id]
                status.battery_level = event.value
                status.online = True
                import time
                status.last_updated = str(time.time())
                logger.info(f"Battery event for {device_id}: {event.value}% - device now online")
            else:
                logger.warning(f"Received battery event for unknown device {device_id}")
        return handler
    
    async def get_devices(self) -> List[VacuumStatus]:
        return list(self.device_status.values())
    
    async def get_device_status(self, device_id: str) -> Optional[VacuumStatus]:
        if device_id not in self.devices:
            return None
        
        # Return current cached status
        return self.device_status.get(device_id)
    
    async def start_cleaning(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.execute_command(Clean(action=CleanAction.START))
            logger.info(f"Started cleaning on device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start cleaning on device {device_id}: {e}")
            return False
    
    async def stop_cleaning(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.execute_command(Clean(action=CleanAction.STOP))
            logger.info(f"Stopped cleaning on device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop cleaning on device {device_id}: {e}")
            return False
    
    async def return_to_dock(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.execute_command(Charge())
            logger.info(f"Sent return to dock command to device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to return device {device_id} to dock: {e}")
            return False
    
    async def pause_cleaning(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.execute_command(Clean(action=CleanAction.PAUSE))
            logger.info(f"Paused cleaning on device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause cleaning on device {device_id}: {e}")
            return False
    
    async def locate_device(self, device_id: str) -> bool:
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
            
        try:
            device = self.devices[device_id]
            await device.execute_command(PlaySound())
            logger.info(f"Sent locate command to device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to locate device {device_id}: {e}")
            return False
    
    async def disconnect(self):
        try:
            for device in self.devices.values():
                await device.disconnect()
            logger.info("Disconnected from all devices")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")