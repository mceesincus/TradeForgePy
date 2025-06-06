# C:\work\TradeForgePy\examples\01b_test_truly_direct.py
import asyncio
import logging
import os
# from dotenv import load_dotenv # COMPLETELY REMOVED to ensure no .env interference

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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_truly_direct_test():
    """Tests the standalone TopStepXHttpClient with hardcoded credentials to bypass .env issues."""
    logger.info("--- [Example 01b] Running Standalone TopStepXHttpClient Test with Hardcoded Credentials ---")

    # --- FORCING LIVE ENVIRONMENT FOR THIS TEST ---
    # Manually set credentials. Replace with your actual LIVE credentials.
    # This completely bypasses any issues with the .env file.
    #
    # !!!!! IMPORTANT !!!!!
    # Use your LIVE credentials and set environment to "LIVE",
    # OR use your DEMO credentials and set environment to "DEMO".
    # The key and environment MUST match.
    
    username_to_test = "cay7man" # e.g., "cay7man"
    api_key_to_test = "7K8AFijHapYr3/7DjSN7Le5H6NH67c0YEu9aXB610Os="
    environment_to_test = "LIVE" # Must be "LIVE" or "DEMO"

    # -----------------------------------------------

    if not username_to_test or "your_exact_username" in username_to_test:
        logger.error("Please edit the script (01b_test_truly_direct.py) and hardcode your LIVE/DEMO username and api_key.")
        return

    http_client: TopStepXHttpClient | None = None
    try:
        logger.info(f"Instantiating TopStepXHttpClient for FORCED '{environment_to_test}' environment...")
        http_client = TopStepXHttpClient(
            username=username_to_test,
            api_key=api_key_to_test,
            environment=environment_to_test
        )

        logger.info("Making API call to get accounts, which will trigger authentication...")
        account_response = await http_client.ts_get_accounts(only_active=False)

        logger.info(">>> AUTHENTICATION AND API CALL SUCCEEDED! <<<")
        print("\n--- Raw TS-Specific Response from ts_get_accounts ---")
        print(account_response.model_dump_json(indent=2))

        if account_response.accounts:
            logger.info(f"Found {len(account_response.accounts)} total accounts.")
        else:
            logger.info("No accounts found.")

        logger.info(f"\nSUCCESS: 01b_test_truly_direct.py completed successfully against {environment_to_test} environment!")

    except AuthenticationError as e:
        logger.error(f"AUTHENTICATION FAILED: The API rejected your credentials for the '{environment_to_test}' environment. Please verify them on the TopStepX website. Error: {e}", exc_info=True)
    except (TradeForgeConnectionError, OperationFailedError) as e:
        logger.error(f"An API-related error occurred: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if http_client:
            logger.info("Closing HTTP client session.")
            await http_client.close_http_client()


if __name__ == "__main__":
    asyncio.run(run_truly_direct_test())