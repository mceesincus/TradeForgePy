# fastapi_service/app/routers/orders.py
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import (
    Order, PlaceOrderRequest, OrderPlacementResponse, ModifyOrderRequest,
    GenericModificationResponse, GenericCancellationResponse
)
from tradeforgepy.exceptions import TradeForgeError, NotFoundError
from ..dependencies import get_provider
from pydantic import BaseModel, Field
from tradeforgepy.utils.time_utils import ensure_utc, UTC_TZ


logger = logging.getLogger(__name__)
router = APIRouter()

# --- Request Body Models for specific actions ---
class OrderModificationPayload(BaseModel):
    """A Pydantic model for the body of a modify order request."""
    new_size: Optional[float] = Field(None, gt=0, description="The new desired size of the order.")
    new_limit_price: Optional[float] = Field(None, gt=0, description="The new limit price for a limit order.")
    new_stop_price: Optional[float] = Field(None, gt=0, description="The new stop price for a stop order.")


# --- Endpoints ---

@router.post(
    "/",
    response_model=OrderPlacementResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Place a New Order",
    description="Submits a new order to the trading provider. The request body should be a generic PlaceOrderRequest model."
)
async def place_new_order(
    order_request: PlaceOrderRequest = Body(...),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Places a new order based on the provided request details.
    """
    try:
        response = await provider.place_order(order_request)
        if not response.order_id_acknowledged:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        return response
    except TradeForgeError as e:
        logger.error(f"API Error during order placement: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/open/{account_id}",
    response_model=List[Order],
    summary="Get Open Orders for an Account",
    description="Retrieves a list of all currently open (working) orders for a specific account."
)
async def get_account_open_orders(
    account_id: str = Path(..., description="The provider's unique ID for the account."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches all open orders for a given account ID.
    """
    try:
        return await provider.get_open_orders(provider_account_id=account_id)
    except TradeForgeError as e:
        logger.error(f"API Error fetching open orders for account '{account_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/history/{account_id}",
    response_model=List[Order],
    summary="Get Order History for an Account",
    description="Retrieves all orders (including filled, cancelled, etc.) for an account within a time range."
)
async def get_account_order_history(
    account_id: str = Path(..., description="The provider's unique ID for the account."),
    start_time_utc: Optional[datetime] = Query(None, description="The start time for the history in ISO 8601 format (UTC). Defaults to 24 hours ago."),
    end_time_utc: Optional[datetime] = Query(None, description="The end time for the history in ISO 8601 format (UTC). Defaults to now."),
    contract_id: Optional[str] = Query(None, description="Optional. Filter history for a specific contract ID."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches the historical orders for a given account.
    """
    _end_time = ensure_utc(end_time_utc) if end_time_utc else datetime.now(UTC_TZ)
    _start_time = ensure_utc(start_time_utc) if start_time_utc else _end_time - timedelta(days=1)
    
    try:
        return await provider.get_order_history(
            provider_account_id=account_id,
            start_time_utc=_start_time,
            end_time_utc=_end_time,
            provider_contract_id=contract_id
        )
    except TradeForgeError as e:
        logger.error(f"API Error fetching order history for account '{account_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{account_id}/{order_id}",
    response_model=Order,
    summary="Get a Specific Order",
    description="Retrieves the full details and status of a single order by its ID."
)
async def get_specific_order(
    account_id: str = Path(..., description="The account ID the order belongs to."),
    order_id: str = Path(..., description="The provider's unique ID for the order."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches a single order by its account and order ID.
    """
    try:
        order = await provider.get_order_by_id(provider_account_id=account_id, provider_order_id=order_id)
        if order is None:
            raise NotFoundError(f"Order '{order_id}' not found in account '{account_id}'.")
        return order
    except NotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TradeForgeError as e:
        logger.error(f"API Error fetching order '{order_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{account_id}/{order_id}/cancel",
    response_model=GenericCancellationResponse,
    summary="Cancel an Order",
    description="Submits a request to cancel an open order."
)
async def cancel_specific_order(
    account_id: str = Path(..., description="The account ID the order belongs to."),
    order_id: str = Path(..., description="The provider's unique ID for the order to cancel."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Cancels a specific open order.
    """
    try:
        response = await provider.cancel_order(provider_account_id=account_id, provider_order_id=order_id)
        if not response.success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        return response
    except TradeForgeError as e:
        logger.error(f"API Error cancelling order '{order_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{account_id}/{order_id}/modify",
    response_model=GenericModificationResponse,
    summary="Modify an Order",
    description="Submits a request to modify an open order's size or price."
)
async def modify_specific_order(
    payload: OrderModificationPayload,
    account_id: str = Path(..., description="The account ID the order belongs to."),
    order_id: str = Path(..., description="The provider's unique ID for the order to modify."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Modifies a specific open order. The request body should contain the new parameters.
    """
    modify_request = ModifyOrderRequest(
        provider_account_id=account_id,
        provider_order_id=order_id,
        new_size=payload.new_size,
        new_limit_price=payload.new_limit_price,
        new_stop_price=payload.new_stop_price
    )
    
    try:
        response = await provider.modify_order(modify_request)
        if not response.success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        return response
    except TradeForgeError as e:
        logger.error(f"API Error modifying order '{order_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))