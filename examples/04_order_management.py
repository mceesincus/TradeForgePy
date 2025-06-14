# examples/04_order_management.py
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
from tradeforgepy.core.models_generic import PlaceOrderRequest
from tradeforgepy.core.enums import OrderType, OrderSide
from tradeforgepy.config import settings

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    ACCOUNT_ID = settings.DEFAULT_CAPTURE_ACCOUNT_ID
    CONTRACT_ID = settings.DEFAULT_CAPTURE_CONTRACT_ID
    logger.info(f"--- [Example 04: Order Management on Account {ACCOUNT_ID}] ---")
    
    if not ACCOUNT_ID or not CONTRACT_ID:
        logger.error("Please set DEFAULT_CAPTURE_ACCOUNT_ID and DEFAULT_CAPTURE_CONTRACT_ID in your .env file to run this example.")
        return

    provider = None
    try:
        provider = TradeForgePy.create_provider("TopStepX")
        await provider.connect()
        logger.info("Provider connected successfully.")

        # 1. Get open orders before we start
        open_orders = await provider.get_open_orders(ACCOUNT_ID)
        logger.info(f"Found {len(open_orders)} open order(s) initially.")

        # 2. Place a new Limit order (place it far from the market so it doesn't fill)
        order_request = PlaceOrderRequest(
            provider_account_id=ACCOUNT_ID,
            provider_contract_id=CONTRACT_ID,
            order_type=OrderType.LIMIT,
            order_side=OrderSide.BUY,
            size=1,
            limit_price=1000 # A price far from the current market
        )
        logger.info(f"Placing a new limit order to buy 1 {CONTRACT_ID} @ {order_request.limit_price}...")
        placement_response = await provider.place_order(order_request)
        
        if not placement_response.provider_order_id:
            logger.error(f"Failed to place order: {placement_response.message}")
            return
            
        order_id = placement_response.provider_order_id
        logger.info(f"Order placed successfully! Provider Order ID: {order_id}")
        
        await asyncio.sleep(2) # Give the system a moment to process

        # 3. Get details of that specific order
        logger.info(f"\nQuerying details for order {order_id}...")
        # Note: This method searches recent history. For a newly placed order,
        # specifying a small search window is more efficient.
        the_order = await provider.get_order_by_id(
            provider_account_id=ACCOUNT_ID,
            provider_order_id=order_id,
            days_to_search=1  # Be efficient: only search recent history for the new order.
        )
        if the_order:
            print(the_order.model_dump_json(indent=2))
        else:
            logger.warning(f"Could not find order {order_id} after placement.")

        # 4. Cancel the order
        logger.info(f"\nCancelling order {order_id}...")
        cancel_response = await provider.cancel_order(ACCOUNT_ID, order_id)
        if cancel_response.success:
            logger.info("Cancellation request sent successfully.")
        else:
            logger.error(f"Failed to cancel order: {cancel_response.message}")
        
        await asyncio.sleep(2)
        
        # 5. Verify it's no longer open
        final_open_orders = await provider.get_open_orders(ACCOUNT_ID)
        logger.info(f"\nFound {len(final_open_orders)} open order(s) at the end.")

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())