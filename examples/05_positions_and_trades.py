# examples/05_positions_and_trades.py
import asyncio
import logging
import os
import sys

# This allows the script to find the tradeforgepy library from the parent directory.
# For a real application, you would just 'pip install tradeforgepy' and this would not be needed.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tradeforgepy import TradeForgePy
from tradeforgepy.exceptions import TradeForgeError
from tradeforgepy.config import settings

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    ACCOUNT_ID = settings.DEFAULT_CAPTURE_ACCOUNT_ID
    
    if not ACCOUNT_ID:
        logger.error("Please set DEFAULT_CAPTURE_ACCOUNT_ID in your .env file to run this example.")
        return
        
    logger.info(f"--- [Example 05: Positions and Trades for Account {ACCOUNT_ID}] ---")
    provider = None
    try:
        provider = TradeForgePy.create_provider("TopStepX")
        await provider.connect()
        logger.info("Provider connected successfully.")

        # 1. Get current open positions
        logger.info("\nFetching current open positions...")
        positions = await provider.get_positions(ACCOUNT_ID)
        
        if not positions:
            logger.info("No open positions found.")
        else:
            logger.info(f"Found {len(positions)} open position(s):")
            for pos in positions:
                print(pos.model_dump_json(indent=2))

        # 2. Get trade history for the last 7 days
        logger.info("\nFetching trade (fill) history for the last 7 days...")
        trades = await provider.get_trade_history(
            provider_account_id=ACCOUNT_ID, 
            days_to_search=7
        )
        
        if not trades:
            logger.info("No trades found in the last 7 days.")
        else:
            logger.info(f"Found {len(trades)} trades. Showing the most recent one:")
            if trades:
                print(trades[0].model_dump_json(indent=2))

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())