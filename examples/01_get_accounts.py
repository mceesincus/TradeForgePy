# examples/01_get_accounts.py
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

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("--- [Example 01: Get Accounts] ---")
    provider = None
    try:
        # The factory automatically loads and injects the correct settings
        provider = TradeForgePy.create_provider("TopStepX")
        await provider.connect()
        logger.info("Provider connected successfully.")

        accounts = await provider.get_accounts()

        if not accounts:
            logger.warning("No tradable accounts found.")
            return

        logger.info(f"Found {len(accounts)} tradable account(s):")
        for i, acc in enumerate(accounts):
            print(f"\n--- Account #{i+1} ---")
            print(acc.model_dump_json(indent=2))

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())