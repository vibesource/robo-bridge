#!/usr/bin/env python3
"""
Quick test script for deebot-t8 library
Run this to test if the library can discover your T8 Pure vacuum
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deebot_t8():
    load_dotenv()
    
    email = os.getenv("ECOVACS_EMAIL")
    password = os.getenv("ECOVACS_PASSWORD")
    country = os.getenv("ECOVACS_COUNTRY", "GB")
    continent = os.getenv("ECOVACS_CONTINENT", "EU")
    
    if not email or not password:
        logger.error("Missing ECOVACS_EMAIL or ECOVACS_PASSWORD in .env file")
        return
    
    logger.info(f"Testing deebot-t8 library with {email[:3]}***@{email.split('@')[1]}")
    logger.info(f"Region: {country}/{continent}")
    
    try:
        # Try to import the library first
        logger.info("Importing deebot-t8...")
        from deebot_t8 import PortalClient, DeebotAuthClient, ApiClient
        from deebot_t8.md5 import md5
        logger.info("✅ deebot-t8 library imported successfully")
        
        # Create portal client
        logger.info("Creating portal client...")
        device_id = "claude_test"  # Dummy device ID for auth
        portal_client = PortalClient(device_id, country, continent)
        logger.info("✅ Portal client created")
        
        # Create auth client
        logger.info("Creating auth client...")
        auth_client = DeebotAuthClient(portal_client, device_id, country)
        logger.info("✅ Auth client created")
        
        # Authenticate
        logger.info("Authenticating...")
        password_hash = md5(password.encode('utf-8'))
        credentials = auth_client.login(email, password_hash)
        logger.info("✅ Authentication successful")
        logger.info(f"Credentials: user_id={credentials.user_id}, expires_at={credentials.expires_at}")
        
        # Create API client
        logger.info("Creating API client...")
        api_client = ApiClient(portal_client, auth_client)
        logger.info("✅ API client created")
        
        # Get devices
        logger.info("Discovering devices...")
        devices = api_client.get_devices_list()
        
        if devices:
            logger.info(f"✅ SUCCESS: Found {len(devices)} devices!")
            for i, device in enumerate(devices):
                logger.info(f"  Device {i+1}: {device}")
                logger.info(f"    Type: {type(device)}")
                logger.info(f"    Attributes: {[attr for attr in dir(device) if not attr.startswith('_')]}")
        else:
            logger.warning("❌ No devices found with deebot-t8 library")
            logger.warning("This means either:")
            logger.warning("- Your T8 Pure is not supported by this library")
            logger.warning("- There are still regional/account issues")
            logger.warning("- The library has different device discovery behavior")
        
        # No cleanup needed for this API
        logger.info("✅ Test completed successfully")
        
    except ImportError as e:
        logger.error(f"❌ Failed to import deebot-t8: {e}")
        logger.error("Run: pip install deebot-t8")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_deebot_t8())