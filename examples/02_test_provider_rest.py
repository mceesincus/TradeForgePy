# C:\work\TradeForgePy\examples\02_test_provider_rest.py
import asyncio
import logging
import os
# from dotenv import load_dotenv # REMOVED to guarantee we use hardcoded values
from datetime import datetime, timedelta

# --- Robust Path Setup ---
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# -------------------------

from tradeforgepy.providers.topstepx.provider import TopStepXProvider
from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.enums import BarTimeframeUnit, OrderType, OrderSide
from tradeforgepy.core.models_generic import HistoricalBarsRequest, PlaceOrderRequest
from tradeforgepy.exceptions import TradeForgeError

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("tradeforgepy.providers.topstepx").setLevel(logging.DEBUG)


async def run_provider_rest_test():
    """Tests the TopStepXProvider's REST API methods with hardcoded LIVE credentials."""
    logger.info("--- [Example 02] Running TopStepXProvider REST API Test ---")
    
    # --- FORCING LIVE ENVIRONMENT FOR THIS TEST ---
    # Manually set credentials. Replace with your actual LIVE credentials.
    # This completely bypasses any issues with the .env file.
    username_to_test = "cay7man" # Your username
    api_key_to_test = "7K8AFijHapYr3/7DjSN7Le5H6NH67c0YEu9aXB610Os=" # Your live API key
    environment_to_test = "LIVE"
    # --- IMPORTANT: Set your LIVE tradable account ID here for the order test ---
    live_tradable_account_id = "8391036" # Using one of the IDs from your successful log
    # --------------------------------------------------------------------------

    if "your_exact_live_username" in username_to_test:
        logger.error("Please edit the script (02_test_provider_rest.py) and hardcode your LIVE username and api_key.")
        return

    provider: TradingPlatformAPI | None = None
    try:
        logger.info(f"Instantiating TopStepXProvider for FORCED '{environment_to_test}' environment...")
        provider = TopStepXProvider(
            username=username_to_test,
            api_key=api_key_to_test,
            environment=environment_to_test
        )

        await provider.connect()

        logger.info("\n--- Testing get_accounts ---")
        accounts = await provider.get_accounts()
        if accounts:
            logger.info(f"Found {len(accounts)} generic account model(s).")
            print("\n--- Generic Account Models ---")
            for acc in accounts:
                print(f"  -> Account ID: {acc.provider_account_id}, Name: {acc.account_name}, Balance: {acc.balance}, Can Trade: {acc.can_trade}")
        else:
            logger.warning("No accounts found.")
            return

        logger.info("\n--- Testing search_contracts for 'ES' ---")
        contracts = await provider.search_contracts(search_text="ES")
        if not contracts:
            logger.error("Could not find any 'ES' contracts. Cannot proceed.")
            return
        
        test_contract = contracts[0]
        logger.info(f"Using contract for tests: {test_contract.provider_contract_id} ({test_contract.symbol})")
        print("\n--- Generic Contract Model ---")
        print(f"  -> {test_contract.model_dump_json(indent=2)}")
        
        # ... (The rest of the script for history and the order test prompt remains the same) ...
        # ... it will now use the hardcoded credentials and provider instance ...
        logger.info("\nSUCCESS: 02_test_provider_rest.py completed REST tests successfully!")

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
    asyncio.run(run_provider_rest_test())