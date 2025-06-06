# C:\work\TradeForgePy\examples\03_test_provider_streams.py
import asyncio
import logging
import os
from pydantic import ValidationError

# --- Robust Path Setup ---
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# -------------------------

from tradeforgepy.providers.topstepx.provider import TopStepXProvider
from tradeforgepy.core.models_generic import GenericStreamEvent
from tradeforgepy.core.enums import MarketDataType, UserDataType, StreamConnectionStatus
from tradeforgepy.config import settings
from tradeforgepy.exceptions import TradeForgeError

# --- Logging Setup ---
# Set the root logger to DEBUG to see all detailed logs from the library
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Optionally, tone down very verbose libraries if needed
logging.getLogger("pysignalr.client").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)

# Get a logger for this specific script
logger = logging.getLogger("StreamTestScript")
logger.setLevel(logging.INFO)


async def run_provider_stream_test():
    """Tests the TopStepXProvider's RealTimeStream methods."""
    logger.info("--- [Example 03] Running TopStepXProvider Stream Test ---")
    
    provider: TopStepXProvider | None = None

    try:
        # These will be loaded from your .env file by the settings object
        username = settings.TS_USERNAME
        api_key = settings.TS_API_KEY
        environment = settings.TS_ENVIRONMENT
        # IMPORTANT: Set these to a valid LIVE account and a liquid contract
        account_id_to_test = settings.TS_CAPTURE_ACCOUNT_ID
        contract_id_to_test = settings.TS_CAPTURE_CONTRACT_ID

        if not account_id_to_test:
            logger.error("Please set TS_CAPTURE_ACCOUNT_ID in your .env file for this test.")
            return

        logger.info(f"Using Account ID: {account_id_to_test}")
        logger.info(f"Using Contract ID: {contract_id_to_test}")

    except ValidationError as e:
        logger.error(
            "Configuration error. Please ensure required settings are in your .env file.\n"
            f"Details: {e}"
        )
        return

    # --- Define Event Handlers ---
    async def my_event_handler(event: GenericStreamEvent):
        """This function will be called for every event received from the stream."""
        logger.info(f"--> EVENT RECEIVED: {event.event_type.value}")
        # Pretty print the generic model we received
        print(event.model_dump_json(indent=2))

    async def my_status_handler(status: StreamConnectionStatus, reason: str):
        """This function will be called when the stream's connection status changes."""
        logger.info(f"--> STATUS CHANGE: {status.value} (Reason: {reason})")

    async def my_error_handler(error: Exception):
        """This function will be called when a stream error occurs."""
        logger.error(f"--> STREAM ERROR: {error}", exc_info=True)


    try:
        logger.info(f"Instantiating TopStepXProvider for '{environment}' environment...")
        provider = TopStepXProvider(
            username=username,
            api_key=api_key,
            environment=environment
        )

        # Register our handlers
        provider.on_event(my_event_handler)
        provider.on_status_change(my_status_handler)
        provider.on_error(my_error_handler)

        # Connect the provider (authenticates the HTTP client, preparing for streams)
        await provider.connect()

        # Subscribe to the data types we can now map
        logger.info(f"Subscribing to market data for {contract_id_to_test}...")
        await provider.subscribe_market_data(
            provider_contract_ids=[contract_id_to_test],
            data_types=[MarketDataType.QUOTE, MarketDataType.DEPTH]
        )
        
        logger.info(f"Subscribing to user data for account {account_id_to_test}...")
        await provider.subscribe_user_data(
            provider_account_ids=[account_id_to_test],
            data_types=[UserDataType.ACCOUNT_UPDATE]
        )

        # This will start the stream runners and block until cancelled.
        logger.info("Starting stream runner. Will run for 60 seconds... (Press Ctrl+C to stop sooner)")
        
        runner_task = asyncio.create_task(provider.run_forever())
        
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Sleep cancelled, stopping runner.")

        runner_task.cancel()
        await runner_task

    except TradeForgeError as e:
        logger.error(f"A TradeForgePy error occurred: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during the provider test: {e}", exc_info=True)
    finally:
        if provider:
            logger.info("Disconnecting provider...")
            await provider.disconnect()
            logger.info("Provider disconnected.")


if __name__ == "__main__":
    if not os.path.exists(os.path.join(project_root, '.env')):
         logger.warning("'.env' file not found. The script might fail if env vars not set.")
    
    # In Windows, the default event loop policy can cause issues with pysignalr's cleanup.
    # Setting this policy explicitly can prevent "Event loop is closed" errors on exit.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_provider_stream_test())
    except KeyboardInterrupt:
        logger.info("Script terminated by user.")