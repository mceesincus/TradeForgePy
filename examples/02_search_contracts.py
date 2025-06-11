# examples/02_search_contracts.py
import asyncio
import logging
import os
import sys

# --- Path Setup ---
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
    SEARCH_QUERY = "MES" # Search for E-mini S&P contracts
    logger.info(f"--- [Example 02: Search Contracts for '{SEARCH_QUERY}'] ---")
    provider = None
    try:
        provider = TopStepXProvider()
        await provider.connect()
        logger.info("Provider connected successfully.")

        contracts = await provider.search_contracts(search_text=SEARCH_QUERY)

        if not contracts:
            logger.warning(f"No contracts found for query '{SEARCH_QUERY}'.")
            return
            
        logger.info(f"Found {len(contracts)} contract(s). Details for the first one:")
        first_contract = contracts[0]
        print(first_contract.model_dump_json(indent=2))
        
        # Now get details for that specific contract by its ID
        logger.info(f"\nFetching full details for contract ID: {first_contract.provider_contract_id}")
        detailed_contract = await provider.get_contract_details(first_contract.provider_contract_id)
        if detailed_contract:
            print("\n--- Detailed Contract Info ---")
            print(detailed_contract.model_dump_json(indent=2))

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())