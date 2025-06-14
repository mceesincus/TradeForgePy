# examples/06_full_stream.py
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
from tradeforgepy.core.models_generic import GenericStreamEvent
from tradeforgepy.core.enums import MarketDataType, UserDataType, StreamConnectionStatus
from tradeforgepy.config import settings
from tradeforgepy.exceptions import TradeForgeError

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("--- [Example 06: Real-Time Full Stream] ---")
    
    account_id = settings.DEFAULT_CAPTURE_ACCOUNT_ID
    contract_id = settings.DEFAULT_CAPTURE_CONTRACT_ID

    if not account_id or not contract_id:
        logger.error("Please set DEFAULT_CAPTURE_ACCOUNT_ID and DEFAULT_CAPTURE_CONTRACT_ID in your .env file to run this example.")
        return

    provider = TradeForgePy.create_provider("TopStepX")

    async def on_event(event: GenericStreamEvent):
        """A simple handler to print received events."""
        print("\n" + "="*20 + f" EVENT: {event.event_type.value} " + "="*20)
        print(event.model_dump_json(indent=2))
        print("="*55)

    async def on_status(status: StreamConnectionStatus, reason: str):
        logger.info(f"STATUS CHANGE: {status.value} - Reason: {reason}")
        
    async def on_error(error: Exception):
        logger.error(f"STREAM ERROR: {error}", exc_info=True)

    try:
        provider.on_event(on_event)
        provider.on_status_change(on_status)
        provider.on_error(on_error)

        await provider.connect()

        # Subscribe to everything
        logger.info(f"Subscribing to all market data for {contract_id}...")
        await provider.subscribe_market_data(
            provider_contract_ids=[contract_id],
            data_types=[MarketDataType.QUOTE, MarketDataType.DEPTH, MarketDataType.TRADE]
        )
        logger.info(f"Subscribing to all user data for account {account_id}...")
        await provider.subscribe_user_data(
            provider_account_ids=[account_id],
            data_types=[
                UserDataType.ACCOUNT_UPDATE,
                UserDataType.ORDER_UPDATE,
                UserDataType.POSITION_UPDATE,
                UserDataType.USER_TRADE
            ]
        )

        logger.info("Streams are running. Perform actions on the platform or watch for market data. Press Ctrl+C to exit.")
        await provider.run_forever()

    except asyncio.CancelledError:
        logger.info("Script cancelled.")
    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        logger.info("Disconnecting provider...")
        await provider.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")