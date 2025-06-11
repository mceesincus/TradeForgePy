# examples/01_get_accounts.py
import asyncio
import logging
import os
import sys

# --- Path Setup ---
# This allows the script to find the tradeforgepy library
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tradeforgepy.providers.topstepx import TopStepXProvider
from tradeforgepy.exceptions import TradeForgeError

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("--- [Example 01: Get Accounts] ---")
    provider = None
    try:
        # The provider automatically loads credentials from your .env file
        provider = TopStepXProvider()
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