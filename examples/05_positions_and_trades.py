# examples/05_positions_and_trades.py
import asyncio
import logging
import os
import sys

# --- Path Setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tradeforgepy.providers.topstepx import TopStepXProvider
from tradeforgepy.exceptions import TradeForgeError
from tradeforgepy.config import settings

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    ACCOUNT_ID = settings.TS_CAPTURE_ACCOUNT_ID
    logger.info(f"--- [Example 05: Positions and Trades for Account {ACCOUNT_ID}] ---")
    provider = None
    try:
        provider = TopStepXProvider()
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
        trades = await provider.get_trade_history(ACCOUNT_ID)
        
        if not trades:
            logger.info("No trades found in the last 7 days.")
        else:
            logger.info(f"Found {len(trades)} trades. Showing the most recent one:")
            print(trades[0].model_dump_json(indent=2))

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())