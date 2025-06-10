# fastapi_service/app/dependencies.py
import asyncio
import logging
import os
import sys
from typing import Optional, AsyncGenerator

# --- Robust Path Setup to find the library and config ---
_current_file_path = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_file_path, '..', '..'))
_src_path = os.path.join(_project_root, 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# --- Import from the library now that the path is set ---
from tradeforgepy.providers.topstepx import TopStepXProvider
from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.exceptions import TradeForgeError
from tradeforgepy.config import settings # <-- IMPORTANT IMPORT

logger = logging.getLogger(__name__)

# This will hold our single, shared instance of the provider
_provider_instance: Optional[TopStepXProvider] = None
_provider_lock = asyncio.Lock()

async def get_provider() -> AsyncGenerator[TradingPlatformAPI, None]:
    """
    FastAPI dependency that provides a singleton instance of the TradingPlatformAPI.
    
    It initializes the provider on the first request and ensures all subsequent
    requests share the same instance, preventing multiple connections.
    """
    global _provider_instance
    async with _provider_lock:
        if _provider_instance is None:
            logger.info("Initializing singleton TopStepXProvider instance...")
            try:
                # =================================================================
                # THIS IS THE CRITICAL FIX:
                # We now use the imported `settings` object to pass credentials.
                # =================================================================
                provider = TopStepXProvider(
                    username=settings.TS_USERNAME,
                    api_key=settings.TS_API_KEY,
                    environment=settings.TS_ENVIRONMENT
                )
                
                await provider.connect()
                
                # Run the stream handlers in the background
                asyncio.create_task(provider.run_forever())
                
                _provider_instance = provider
                logger.info("TopStepXProvider initialized and connected.")
            except TradeForgeError as e:
                logger.critical(f"Failed to initialize the trading provider: {e}", exc_info=True)
                raise
    
    yield _provider_instance