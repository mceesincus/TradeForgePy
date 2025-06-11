# fastapi_service/app/websockets/market_data.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import logging
import asyncio

from tradeforgepy.core.interfaces import TradingPlatformAPI
from tradeforgepy.core.models_generic import GenericStreamEvent
from tradeforgepy.core.enums import MarketDataType, UserDataType
from ..dependencies import get_provider, get_broadcaster
from ..broadcast import Broadcast

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/{contract_id}")
async def websocket_market_data_endpoint(
    websocket: WebSocket,
    contract_id: str,
    provider: TradingPlatformAPI = Depends(get_provider),
    broadcaster: Broadcast = Depends(get_broadcaster)
):
    """
    WebSocket endpoint for streaming live market data for a specific contract.
    Connect to this endpoint with a URL like: ws://127.0.0.1:8000/ws/CON.F.US.EP.M25
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for contract: {contract_id}")
    
    queue: asyncio.Queue[GenericStreamEvent] = asyncio.Queue()
    await broadcaster.subscribe(queue)
    
    # Check if this is the first client subscribing to this contract
    is_new_subscription = contract_id not in broadcaster.subscribed_contracts
    if is_new_subscription:
        logger.info(f"First client for {contract_id}. Subscribing to provider market data...")
        try:
            await provider.subscribe_market_data(
                provider_contract_ids=[contract_id],
                data_types=[MarketDataType.QUOTE, MarketDataType.DEPTH, MarketDataType.TRADE]
            )
            # Also subscribe to user data for the primary account to get all events
            # This part can be refined later if needed
            from tradeforgepy.config import settings
            if settings.TS_CAPTURE_ACCOUNT_ID:
                await provider.subscribe_user_data(
                    provider_account_ids=[settings.TS_CAPTURE_ACCOUNT_ID],
                    data_types=[UserDataType.ORDER_UPDATE, UserDataType.POSITION_UPDATE, UserDataType.USER_TRADE]
                )
            broadcaster.subscribed_contracts.add(contract_id)
        except Exception as e:
            logger.error(f"Failed to subscribe to provider for {contract_id}: {e}", exc_info=True)
            await websocket.close(code=1011, reason="Failed to subscribe to backend data stream.")
            return

    try:
        while True:
            # Wait for an event to arrive from the broadcaster's queue
            event = await queue.get()
            
            # Filter to only send events relevant to this specific websocket connection
            if event.provider_contract_id == contract_id or event.event_type in [UserDataType.ORDER_UPDATE, UserDataType.POSITION_UPDATE, UserDataType.USER_TRADE]:
                # Send the event data to the client as JSON
                await websocket.send_json(event.model_dump(mode='json'))

    except WebSocketDisconnect:
        logger.info(f"WebSocket client for {contract_id} disconnected.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket for {contract_id}: {e}", exc_info=True)
    finally:
        # Clean up the subscription
        logger.info(f"Cleaning up resources for client {contract_id}.")
        await broadcaster.unsubscribe(queue)
        # Note: A more advanced implementation would check if this was the *last* client
        # for a contract before unsubscribing from the provider to save bandwidth.
        # For now, we keep the provider subscription active for simplicity.