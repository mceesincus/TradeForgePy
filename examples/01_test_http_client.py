# C:\work\TradeForgePy\examples\01_test_http_client.py
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

from tradeforgepy.providers.topstepx.client import TopStepXHttpClient
from tradeforgepy.exceptions import AuthenticationError, ConnectionError as TradeForgeConnectionError, OperationFailedError
from tradeforgepy.config import settings # <-- IMPORT THE NEW SETTINGS OBJECT

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_http_client_test():
    """Tests the standalone TopStepXHttpClient using settings from .env file."""
    logger.info("--- [Example 01] Running Standalone TopStepXHttpClient Test ---")

    try:
        # Pydantic's BaseSettings automatically loads from .env upon import of `settings`
        # We can now access the values directly as attributes.
        username = settings.TS_USERNAME
        api_key = settings.TS_API_KEY
        environment = settings.TS_ENVIRONMENT
        logger.info(f"Loaded configuration for environment: {environment}")
    except ValidationError as e:
        logger.error(
            "Configuration error. Please ensure TS_USERNAME and TS_API_KEY are set in your .env file.\n"
            f"Details: {e}"
        )
        return

    http_client: TopStepXHttpClient | None = None
    try:
        logger.info(f"Instantiating TopStepXHttpClient for {environment} environment...")
        http_client = TopStepXHttpClient(
            username=username,
            api_key=api_key,
            environment=environment
        )

        logger.info("Making first API call to trigger authentication...")
        account_response = await http_client.ts_get_accounts(only_active=False)

        logger.info("Successfully received response from ts_get_accounts.")
        print("\n--- Raw TS-Specific Response from ts_get_accounts ---")
        print(account_response.model_dump_json(indent=2))

        if account_response.accounts:
            logger.info(f"Found {len(account_response.accounts)} total accounts.")
        else:
            logger.info("No accounts found.")

        logger.info("\nSUCCESS: 01_test_http_client.py completed successfully!")

    except (AuthenticationError, TradeForgeConnectionError, OperationFailedError) as e:
        logger.error(f"An API-related error occurred: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if http_client:
            logger.info("Closing HTTP client session.")
            await http_client.close_http_client()


if __name__ == "__main__":
    # Add a check to guide the user if the .env file is missing
    if not os.path.exists(os.path.join(project_root, '.env')):
         logger.warning("'.env' file not found in project root. The script might fail if environment variables are not set elsewhere.")
    asyncio.run(run_http_client_test())