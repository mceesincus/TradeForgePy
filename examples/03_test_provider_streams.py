# C:\work\TradeForgePy\examples\03_test_provider_streams.py
import asyncio
import logging
import os
import sys
from pydantic import ValidationError

# --- Robust Path Setup ---
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
from tradeforgepy.exceptions import TradeForgeError, ConnectionError as TradeForgeConnectionError

# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("pysignalr.client").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)
logger = logging.getLogger("StreamTestScript")
logger.setLevel(logging.INFO)


async def run_provider_stream_test():
    """Tests the TopStepXProvider's RealTimeStream methods with connection retries."""
    logger.info("--- [Example 03] Running TopStepXProvider Stream Test ---")
    
    provider: TopStepXProvider | None = None
    max_retries = 10  # Try to connect up to 10 times
    retry_delay = 30  # Wait 30 seconds between retries

    try:
        username = settings.TS_USERNAME
        api_key = settings.TS_API_KEY
        environment = settings.TS_ENVIRONMENT
        account_id_to_test = settings.TS_CAPTURE_ACCOUNT_ID
        contract_id_to_test = settings.TS_CAPTURE_CONTRACT_ID

        if not account_id_to_test:
            logger.error("Please set TS_CAPTURE_ACCOUNT_ID in your .env file for this test.")
            return

        logger.info(f"Using Account ID: {account_id_to_test}")
        logger.info(f"Using Contract ID: {contract_id_to_test}")

    except ValidationError as e:
        logger.error(f"Configuration error. See .env.example and fill your .env file.\nDetails: {e}")
        return

    # --- Define Event Handlers ---
    async def my_event_handler(event: GenericStreamEvent):
        logger.info(f"--> EVENT RECEIVED: {event.event_type.value}")
        print(event.model_dump_json(indent=2))

    async def my_status_handler(status: StreamConnectionStatus, reason: str):
        logger.info(f"--> STATUS CHANGE: {status.value} (Reason: {reason})")

    async def my_error_handler(error: Exception):
        logger.error(f"--> STREAM ERROR: {error}", exc_info=True)

    for attempt in range(max_retries):
        try:
            logger.info(f"Connection attempt {attempt + 1} of {max_retries}...")
            
            logger.info(f"Instantiating TopStepXProvider for '{environment}' environment...")
            provider = TopStepXProvider(
                username=username,
                api_key=api_key,
                environment=environment
            )

            provider.on_event(my_event_handler)
            provider.on_status_change(my_status_handler)
            provider.on_error(my_error_handler)

            await provider.connect()
            logger.info("Provider HTTP client connected successfully.")

            # If connection is successful, break the retry loop
            break

        except TradeForgeConnectionError as e:
            logger.warning(f"Connection attempt failed: {e}")
            if provider:
                await provider.disconnect() # Ensure cleanup before retry
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before next attempt...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Maximum connection retries reached. Exiting.")
                return
        except Exception as e:
            logger.error(f"An unexpected error occurred during connection setup: {e}", exc_info=True)
            if provider:
                await provider.disconnect()
            return

    # If the loop completed without a successful connection
    if not provider or not provider.http_client._token:
        logger.error("Failed to establish a connection after all retries.")
        return
        
    try:
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

        logger.info("Starting stream runner. Press Ctrl+C to stop.")
        
        # This will block here until the coroutine finishes or is cancelled.
        await provider.run_forever()

    except asyncio.CancelledError:
        logger.info("Main task was cancelled.")
    except TradeForgeError as e:
        logger.error(f"A TradeForgePy error occurred during streaming: {e}", exc_info=True)
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
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        # asyncio.run() is the standard, safe way to run the top-level coroutine.
        # It creates a new event loop, runs the task until it's complete,
        # and handles cleanup. It also propagates the KeyboardInterrupt.
        asyncio.run(run_provider_stream_test())
    except KeyboardInterrupt:
        logger.info("Script terminated by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"An unexpected error occurred at the top level: {e}", exc_info=True)