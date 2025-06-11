# fastapi_service/app/dependencies.py
import asyncio
import logging
import os
import sys
from typing import Optional, AsyncGenerator

_current_file_path = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_file_path, '..', '..'))
_src_path = os.path.join(_project_root, 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from tradeforgepy.providers.topstepx import TopStepXProvider
from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.exceptions import TradeForgeError, ConnectionError as TradeForgeConnectionError
from tradeforgepy.config import settings
from .broadcast import Broadcast  # <-- IMPORT THE NEW BROADCASTER

logger = logging.getLogger(__name__)

# --- Singleton Instances ---
_provider_instance: Optional[TopStepXProvider] = None
_broadcast_instance: Optional[Broadcast] = None
_initialization_lock = asyncio.Lock()


async def get_provider() -> TradingPlatformAPI:
    """
    FastAPI dependency that provides a singleton instance of the TradingPlatformAPI.
    This function assumes the provider has already been initialized by the lifespan manager.
    """
    if _provider_instance is None:
        # This should ideally not happen if the lifespan manager runs correctly
        raise TradeForgeError("Trading provider has not been initialized.")
    return _provider_instance


def get_broadcaster() -> Broadcast:
    """
    FastAPI dependency that provides a singleton instance of the Broadcast utility.
    """
    if _broadcast_instance is None:
        # This should also not happen if the lifespan manager runs correctly
        raise TradeForgeError("Broadcaster has not been initialized.")
    return _broadcast_instance


async def initialize_singletons():
    """
    Initializes the provider and broadcaster singletons.
    This function is called once by the application's lifespan manager.
    """
    global _provider_instance, _broadcast_instance
    
    async with _initialization_lock:
        if _provider_instance is not None:
            return # Already initialized

        # Create the broadcaster first
        _broadcast_instance = Broadcast()
        
        # Now, initialize the provider with retry logic
        max_retries = 5
        retry_delay = 20
        for attempt in range(max_retries):
            logger.info(f"Initializing singleton TopStepXProvider instance (Attempt {attempt + 1}/{max_retries})...")
            try:
                provider = TopStepXProvider(
                    username=settings.TS_USERNAME,
                    api_key=settings.TS_API_KEY,
                    environment=settings.TS_ENVIRONMENT
                )
                await provider.connect()

                # CRITICAL: Set the provider's event callback to the broadcaster's publish method
                provider.on_event(_broadcast_instance.publish)
                
                # Start the provider's background tasks
                asyncio.create_task(provider.run_forever())
                
                _provider_instance = provider
                logger.info("TopStepXProvider initialized and connected successfully.")
                return # Exit the function on success

            except TradeForgeConnectionError as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical("Maximum connection retries reached.")
                    raise e
        
        # If the loop finishes without returning, it means all retries failed
        raise TradeForgeError("Failed to initialize provider after multiple retries.")