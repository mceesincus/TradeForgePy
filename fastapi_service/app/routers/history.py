# fastapi_service/app/routers/history.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import HistoricalBarsRequest, HistoricalBarsResponse
from tradeforgepy.core.enums import BarTimeframeUnit
from tradeforgepy.exceptions import TradeForgeError
from ..dependencies import get_provider
from tradeforgepy.utils.time_utils import ensure_utc

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/{provider_contract_id}/bars",
    response_model=HistoricalBarsResponse,
    summary="Get Historical Bar Data",
    description="Retrieves historical OHLCV bar data for a specific contract."
)
async def get_bars(
    provider_contract_id: str,
    timeframe_unit: BarTimeframeUnit = Query(..., description="The unit of the bar timeframe (e.g., MINUTE, HOUR, DAY)."),
    timeframe_value: int = Query(..., gt=0, description="The value of the bar timeframe (e.g., 5 for a 5-minute bar)."),
    start_time_utc: datetime = Query(None, description="The start time for the data in ISO 8601 format (UTC). Defaults to 24 hours ago."),
    end_time_utc: datetime = Query(None, description="The end time for the data in ISO 8601 format (UTC). Defaults to now."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches historical bar data for a given contract.

    - **provider_contract_id**: The unique ID of the contract from the provider (e.g., `CON.F.US.EP.M25`).
    - **timeframe_unit**: The time unit for each bar (e.g., `MINUTE`).
    - **timeframe_value**: The number of time units per bar (e.g., `15` for 15-minute bars).
    - **start_time_utc / end_time_utc**: The date range for the request. If not provided, it defaults to the last 24 hours.
    """
    # Set default time range if not provided
    if end_time_utc is None:
        end_time_utc = datetime.now()
    if start_time_utc is None:
        start_time_utc = end_time_utc - timedelta(days=1)

    # Ensure datetimes are timezone-aware (UTC)
    start_time_utc = ensure_utc(start_time_utc)
    end_time_utc = ensure_utc(end_time_utc)
    
    # Create the generic request model
    request = HistoricalBarsRequest(
        provider_contract_id=provider_contract_id,
        timeframe_unit=timeframe_unit,
        timeframe_value=timeframe_value,
        start_time_utc=start_time_utc,
        end_time_utc=end_time_utc
    )
    
    try:
        # Call the provider's method
        response = await provider.get_historical_bars(request)
        return response
    except TradeForgeError as e:
        logger.error(f"API Error when fetching historical bars: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bars from provider: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when fetching historical bars: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")