# fastapi_service/app/routers/contracts.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import Contract
from tradeforgepy.exceptions import TradeForgeError, NotFoundError
from ..dependencies import get_provider

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/search",
    response_model=List[Contract],
    summary="Search for Tradable Contracts",
    description="Searches for contracts based on a text query (e.g., 'ES', 'NQ', 'BTC')."
)
async def search_for_contracts(
    query: str = Query(..., description="The search string for the contract, e.g., 'ES'."),
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Performs a search for contracts using the underlying provider's search functionality.
    """
    try:
        contracts = await provider.search_contracts(search_text=query)
        return contracts
    except TradeForgeError as e:
        logger.error(f"API Error when searching for contracts with query '{query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search for contracts: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when searching for contracts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")


@router.get(
    "/{provider_contract_id}",
    response_model=Contract,
    summary="Get Specific Contract Details",
    description="Retrieves the full details for a single contract using its unique provider ID."
)
async def get_single_contract(
    provider_contract_id: str,
    provider: TradingPlatformAPI = Depends(get_provider)
):
    """
    Fetches detailed information for a single contract.
    """
    try:
        contract = await provider.get_contract_details(provider_contract_id=provider_contract_id)
        if contract is None:
            # This case should be handled by the NotFoundError, but as a fallback.
            raise HTTPException(status_code=404, detail=f"Contract with ID '{provider_contract_id}' not found.")
        return contract
    except NotFoundError as e:
        logger.warning(f"Contract not found for ID '{provider_contract_id}': {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except TradeForgeError as e:
        logger.error(f"API Error when fetching contract '{provider_contract_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contract details: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when fetching contract '{provider_contract_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")