# fastapi_service/app/routers/accounts.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import logging

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import Account
from tradeforgepy.exceptions import TradeForgeError
from ..dependencies import get_provider

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/",
    response_model=List[Account],
    summary="Get All Tradable Accounts",
    description="Retrieves a list of all accounts that are currently enabled for trading from the provider."
)
async def get_all_accounts(
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches all tradable accounts.

    The `provider` dependency is injected by FastAPI. It's a connected
    and authenticated instance of our TradeForgePy provider.
    """
    try:
        accounts = await provider.get_accounts()
        return accounts
    except TradeForgeError as e:
        logger.error(f"API Error when fetching accounts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve accounts from provider: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when fetching accounts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")