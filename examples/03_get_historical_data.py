# examples/03_get_historical_data.py
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# --- Path Setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tradeforgepy.providers.topstepx import TopStepXProvider
from tradeforgepy.exceptions import TradeForgeError
from tradeforgepy.core.models_generic import HistoricalBarsRequest
from tradeforgepy.core.enums import BarTimeframeUnit
from tradeforgepy.config import settings

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    CONTRACT_ID = settings.TS_CAPTURE_CONTRACT_ID # From your .env file
    logger.info(f"--- [Example 03: Get Historical Data for {CONTRACT_ID}] ---")
    provider = None
    try:
        provider = TopStepXProvider()
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