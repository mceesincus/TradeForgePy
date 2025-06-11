# fastapi_service/app/main.py
import logging
import sys
import os
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager

# --- Robust Path Setup for Library ---
_current_file_path = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_file_path, '..', '..'))
_src_path = os.path.join(_project_root, 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# --- Application Imports ---
# get_provider is still used by the endpoints, but initialize_singletons is for startup
from .dependencies import get_provider, initialize_singletons
from .routers import accounts, history, contracts, orders, positions, trades
from .websockets import market_data
from tradeforgepy.core.interfaces import TradingPlatformAPI

# ... (Logging setup is correct and unchanged) ...
log_dir = os.path.join(_project_root, "captured_data_logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f"fastapi_service_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan. Connects the provider on startup
    and disconnects it on shutdown.
    """
    logger.info("Application starting up...")
    try:
        # Call the new initialization function on startup
        await initialize_singletons()
        # Retrieve the initialized provider instance for shutdown
        app.state.provider = await get_provider()
        logger.info("Trading provider and broadcaster successfully initialized during startup.")
    except Exception as e:
        logger.critical(f"FATAL: Could not initialize singletons on startup. {e}", exc_info=True)
        app.state.provider = None
    
    yield # The application is now running
    
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
app.include_router(history.router, prefix="/history", tags=["Historical Data"])
app.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
app.include_router(orders.router, prefix="/orders", tags=["Order Management"])
app.include_router(positions.router, prefix="/positions", tags=["Position Management"])
app.include_router(trades.router, prefix="/trades", tags=["Trade History"])

# Include the WebSocket routers
app.include_router(market_data.router, prefix="/ws", tags=["Market Data Streams"])

@app.get("/", tags=["Status"])
async def read_root():
    return {"status": "ok", "message": "Welcome to the TradeForgePy API Service"}