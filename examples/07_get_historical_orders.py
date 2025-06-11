# examples/07_get_historical_orders.py
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

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
    logger.info(f"--- [Example 07: Get Historical Orders for Account {ACCOUNT_ID}] ---")
    provider = None
    try:
        provider = TopStepXProvider()
        await provider.connect()
        logger.info("Provider connected successfully.")

        # Define the time range for the history query (e.g., the last 3 days)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=3)
        
        logger.info(f"Requesting order history from {start_time.isoformat()} to {end_time.isoformat()}...")
        
        # Use the new get_order_history method
        orders = await provider.get_order_history(
            provider_account_id=ACCOUNT_ID,
            start_time_utc=start_time,
            end_time_utc=end_time
        )
        
        if not orders:
            logger.warning("No orders found in the specified time range.")
            return
            
        logger.info(f"Found {len(orders)} historical orders. Showing details for up to the first 3:")
        for i, order in enumerate(orders[:3]):
            print(f"\n--- Historical Order #{i+1} (Status: {order.status.value}) ---")
            print(order.model_dump_json(indent=2))

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())