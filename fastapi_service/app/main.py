# fastapi_service/app/main.py
import logging
import sys
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

# --- Robust Path Setup for Library ---
_current_file_path = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_file_path, '..', '..'))
_src_path = os.path.join(_project_root, 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from .dependencies import get_provider
from .routers import accounts
from .websockets import market_data
from tradeforgepy.core.interfaces import TradingPlatformAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application's lifespan."""
    logger.info("Application starting up...")
    provider_instance: TradingPlatformAPI | None = None
    try:
        provider_generator = get_provider()
        provider_instance = await anext(provider_generator)
        app.state.provider = provider_instance
        logger.info("Trading provider successfully initialized during startup.")
    except Exception as e:
        logger.critical(f"FATAL: Could not initialize trading provider on startup. {e}", exc_info=True)
        app.state.provider = None
    
    yield
    
    logger.info("Application shutting down...")
    if hasattr(app.state, 'provider') and app.state.provider:
        await app.state.provider.disconnect()
        logger.info("Trading provider disconnected.")

app = FastAPI(
    title="TradeForgePy API Service",
    description="Exposes the TradeForgePy library's functionality via a web API.",
    version="0.1.0",
    lifespan=lifespan
)

# Include the REST API routers
app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])

# --- CORRECTED ROUTER ---
# The market_data router itself defines the /ws path, so we don't add a prefix here.
app.include_router(market_data.router, tags=["Market Data Streams"])

@app.get("/", tags=["Status"])
async def read_root():
    return {"status": "ok", "message": "Welcome to the TradeForgePy API Service"}