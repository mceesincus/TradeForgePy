# fastapi_service/app/routers/positions.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import Position, OrderPlacementResponse
from tradeforgepy.exceptions import TradeForgeError
from ..dependencies import get_provider

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{account_id}",
    response_model=List[Position],
    summary="Get Open Positions for an Account",
    description="Retrieves a list of all currently open (non-flat) positions for a specific account."
)
async def get_open_positions(
    account_id: str = Path(..., description="The provider's unique ID for the account."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches all open positions for a given account ID.
    """
    try:
        return await provider.get_positions(provider_account_id=account_id)
    except TradeForgeError as e:
        logger.error(f"API Error fetching positions for account '{account_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{account_id}/{contract_id}/close",
    response_model=OrderPlacementResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Close or Reduce a Position",
    description="Submits a market order to close or partially reduce an existing position for a specific contract."
)
async def close_a_position(
    account_id: str = Path(..., description="The account ID where the position is held."),
    contract_id: str = Path(..., description="The provider's unique ID for the contract of the position to close."),
    size: Optional[float] = Query(None, gt=0, description="The number of lots to close. If not provided, the entire position will be closed."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Submits a request to close a position.
    - If `size` is specified, it attempts a partial close.
    - If `size` is omitted, it attempts to close the entire position.
    """
    try:
        response = await provider.close_position(
            provider_account_id=account_id,
            provider_contract_id=contract_id,
            size_to_close=size
        )
        if not response.order_id_acknowledged: # Check for success from the provider
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        return response
    except TradeForgeError as e:
        logger.error(f"API Error closing position for contract '{contract_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))