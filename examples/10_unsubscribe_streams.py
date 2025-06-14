# examples/10_unsubscribe_streams.py
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
from tradeforgepy.core.enums import MarketDataType, StreamConnectionStatus
from tradeforgepy.config import settings
from tradeforgepy.exceptions import TradeForgeError

# --- Configuration ---
# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UnsubscribeExample")

# Get the default contract ID from settings (or use a known one)
CONTRACT_ID = settings.DEFAULT_CAPTURE_CONTRACT_ID

# --- Main Application Logic ---
async def main():
    """
    Demonstrates how to subscribe to and then unsubscribe from a real-time data stream.
    """
    if not CONTRACT_ID:
        logger.error("Please set DEFAULT_CAPTURE_CONTRACT_ID in your .env file to run this example.")
        return

    # 1. Initialize the provider via the main factory
    # This automatically loads credentials from the .env file
    provider = TradeForgePy.create_provider(provider_name="TopStepX")

    # 2. Define event handlers to see what's happening
    async def on_event(event):
        logger.info(f"Received Event: {event.event_type.value}")

    async def on_status_change(status: StreamConnectionStatus, reason: str):
        logger.info(f"Stream Status Changed: {status.value} - Reason: {reason}")

    async def on_error(error: Exception):
        logger.error(f"An error occurred in the stream: {error}", exc_info=True)

    # Register the callbacks with the provider instance
    provider.on_event(on_event)
    provider.on_status_change(on_status_change)
    provider.on_error(on_error)

    runner_task = None
    try:
        # 3. Connect the provider (both HTTP client and stream handlers)
        logger.info("Connecting to the provider...")
        await provider.connect()

        # Run the stream handlers in the background
        # This task will manage the WebSocket connection and automatically reconnect if needed
        runner_task = asyncio.create_task(provider.run_forever())
        
        # Give it a moment to establish the connection
        await asyncio.sleep(5) 

        # 4. Subscribe to market data (Quotes and Depth) for our contract
        data_types_to_sub = [MarketDataType.QUOTE, MarketDataType.DEPTH]
        logger.info(f"Subscribing to {data_types_to_sub} for contract {CONTRACT_ID}...")
        await provider.subscribe_market_data([CONTRACT_ID], data_types_to_sub)
        
        # 5. Let data stream for a while
        logger.info("--- Streaming data for 10 seconds... ---")
        await asyncio.sleep(10)
        
        # 6. Now, unsubscribe from the data
        logger.info(f"Unsubscribing from {data_types_to_sub} for contract {CONTRACT_ID}...")
        await provider.unsubscribe_market_data([CONTRACT_ID], data_types_to_sub)
        logger.info("Unsubscribe command sent.")
        
        # 7. Wait again to confirm data has stopped
        logger.info("--- Waiting for 10 seconds to confirm data has stopped... ---")
        await asyncio.sleep(10)
        
        logger.info("Example finished successfully.")

    except (TradeForgeError, Exception) as e:
        logger.error(f"An error occurred during the example run: {e}", exc_info=True)
    finally:
        # 8. Cleanly disconnect the provider
        logger.info("Disconnecting from the provider...")
        await provider.disconnect()
        if runner_task and not runner_task.done():
            runner_task.cancel()
        logger.info("Disconnected.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")