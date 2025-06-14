# examples/03_get_historical_data.py
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# This allows the script to find the tradeforgepy library from the parent directory.
# For a real application, you would just 'pip install tradeforgepy' and this would not be needed.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tradeforgepy import TradeForgePy
from tradeforgepy.exceptions import TradeForgeError
from tradeforgepy.core.models_generic import HistoricalBarsRequest
from tradeforgepy.core.enums import BarTimeframeUnit
from tradeforgepy.config import settings

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    CONTRACT_ID = settings.DEFAULT_CAPTURE_CONTRACT_ID # From your .env file
    if not CONTRACT_ID:
        logger.error("Please set DEFAULT_CAPTURE_CONTRACT_ID in your .env file to run this example.")
        return
        
    logger.info(f"--- [Example 03: Get Historical Data for {CONTRACT_ID}] ---")
    provider = None
    try:
        provider = TradeForgePy.create_provider("TopStepX")
        await provider.connect()
        logger.info("Provider connected successfully.")

        # Prepare a request for the last 3 days of 15-minute bars
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=3)
        
        request = HistoricalBarsRequest(
            provider_contract_id=CONTRACT_ID,
            timeframe_unit=BarTimeframeUnit.MINUTE,
            timeframe_value=15,
            start_time_utc=start_time,
            end_time_utc=end_time
        )
        
        logger.info(f"Requesting 15-minute bars from {start_time.isoformat()} to {end_time.isoformat()}")
        response = await provider.get_historical_bars(request)
        
        if not response.bars:
            logger.warning("No bars were returned.")
            return
            
        logger.info(f"Received {len(response.bars)} bars. Showing first and last bar:")
        print("\n--- First Bar ---")
        print(response.bars[0].model_dump_json(indent=2))
        print("\n--- Last Bar ---")
        print(response.bars[-1].model_dump_json(indent=2))

    except TradeForgeError as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if provider:
            await provider.disconnect()
            logger.info("Provider disconnected.")

if __name__ == "__main__":
    asyncio.run(main())