# fastapi_service/app/routers/trades.py
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import Trade
from tradeforgepy.exceptions import TradeForgeError
from ..dependencies import get_provider
from tradeforgepy.utils.time_utils import ensure_utc

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{account_id}",
    response_model=List[Trade],
    summary="Get Trade History for an Account",
    description="Retrieves a list of recent fills (trades) for a specific account, optionally filtered by contract and time range."
)
async def get_trade_history_for_account(
    account_id: str = Path(..., description="The provider's unique ID for the account."),
    contract_id: Optional[str] = Query(None, description="Optional. Filter trades for a specific contract ID."),
    start_time_utc: Optional[datetime] = Query(None, description="Optional. The start time for the data in ISO 8601 format (UTC). Defaults to 7 days ago."),
    end_time_utc: Optional[datetime] = Query(None, description="Optional. The end time for the data in ISO 8601 format (UTC). Defaults to now."),
    limit: Optional[int] = Query(None, gt=0, description="Optional. The maximum number of recent trades to return."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches the trade (fill) history for a given account.
    """
    # Use default time range if not provided, as the provider method requires it.
    _end_time = ensure_utc(end_time_utc) if end_time_utc else datetime.now(UTC_TZ)
    _start_time = ensure_utc(start_time_utc) if start_time_utc else _end_time - timedelta(days=7)
    
    try:
        return await provider.get_trade_history(
            provider_account_id=account_id,
            provider_contract_id=contract_id,
            start_time_utc=_start_time,
            end_time_utc=_end_time,
            limit=limit
        )
    except TradeForgeError as e:
        logger.error(f"API Error fetching trade history for account '{account_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))