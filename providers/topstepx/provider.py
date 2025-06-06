# tradeforgepy/providers/topstepx/provider.py
import logging
import os
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from tradeforgepy.core.interfaces import (
    TradingPlatformAPI, RealTimeStream,
    GenericStreamEventCallback, StreamStatusCallback, StreamErrorCallback
)
from tradeforgepy.core.models_generic import (
    Account as GenericAccount, Contract as GenericContract,
    BarData as GenericBarData, HistoricalBarsRequest as GenericHistoricalBarsRequest,
    HistoricalBarsResponse as GenericHistoricalBarsResponse,
    PlaceOrderRequest as GenericPlaceOrderRequest, OrderPlacementResponse as GenericOrderPlacementResponse,
    Order as GenericOrder, ModifyOrderRequest as GenericModifyOrderRequest,
    GenericModificationResponse, GenericCancellationResponse,

    Position as GenericPosition, Trade as GenericTrade, GenericStreamEvent
)
from tradeforgepy.core.enums import AssetClass, StreamConnectionStatus, MarketDataType, UserDataType
from tradeforgepy.exceptions import (
    ConfigurationError, AuthenticationError, ConnectionError as TradeForgeConnectionError,
    OperationFailedError, NotFoundError, InvalidParameterError
)

from .client import TopStepXHttpClient
from . import mapper
from .schemas_ts import (
    TSSearchOrderRequest, TSSearchOpenOrderRequest,
    TSCloseContractPositionRequest, TSPartialCloseContractPositionRequest,
    TSSearchTradeRequest, TSModifyOrderRequest as TSTopStepModifyOrderRequest
)
from .streams import TopStepXMarketStreamInternal, TopStepXUserStreamInternal

logger = logging.getLogger(__name__)

class TopStepXProvider(TradingPlatformAPI, RealTimeStream):
    """
    Concrete implementation of the generic trading platform interfaces for TopStepX.
    This class handles both REST API calls and real-time SignalR streaming.
    """
    provider_name: str = "TopStepX"

    def __init__(self, username: Optional[str] = None, api_key: Optional[str] = None,
                 environment: Optional[str] = None,
                 connect_timeout: float = 10.0, read_timeout: float = 30.0):
        _username = username or os.getenv("TS_USERNAME")
        _api_key = api_key or os.getenv("TS_API_KEY")
        _environment = (environment or os.getenv("TS_ENVIRONMENT", "DEMO")).upper()

        if not _username or not _api_key:
            raise ConfigurationError("TopStepXProvider requires username and API key, either via arguments or TS_USERNAME/TS_API_KEY env vars.")
        
        self.http_client = TopStepXHttpClient(
            username=_username, api_key=_api_key, environment=_environment,
            connect_timeout=connect_timeout, read_timeout=read_timeout
        )
        self._is_connected_http = False
        
        # Internal stream handlers
        self.market_stream_handler: Optional[TopStepXMarketStreamInternal] = None
        self.user_stream_handler: Optional[TopStepXUserStreamInternal] = None
        
        # User-registered callbacks
        self._user_event_callback: Optional[GenericStreamEventCallback] = None
        self._user_status_callback: Optional[StreamStatusCallback] = None
        self._user_error_callback: Optional[StreamErrorCallback] = None
        
        self._stream_runner_task: Optional[asyncio.Task] = None

        logger.info(f"TopStepXProvider initialized for environment: {self.http_client.environment}")

    # --- TradingPlatformAPI & RealTimeStream Common Methods ---
    async def connect(self) -> None:
        """Establishes connection and authenticates the HTTP client."""
        if not self._is_connected_http:
            try:
                await self.http_client._authenticate()
                self._is_connected_http = True
                logger.info("TopStepXProvider HTTP client connected and authenticated successfully.")
            except Exception as e:
                self._is_connected_http = False
                logger.error(f"TopStepXProvider HTTP connection/authentication failed during connect(): {e}")
                raise TradeForgeConnectionError(f"HTTP Auth failed: {e}") from e
        
        # Stream connection is handled by RealTimeStream.run_forever() when called by the user.
        # This connect() method ensures the HTTP client (and its token) is ready for streams.

    async def disconnect(self) -> None:
        """Closes HTTP client and any active real-time streams."""
        logger.info("TopStepXProvider disconnecting...")
        if self._stream_runner_task and not self._stream_runner_task.done():
            self._stream_runner_task.cancel()
            try:
                await self._stream_runner_task
            except asyncio.CancelledError:
                logger.info("Provider's stream runner task cancelled.")
        
        if self.market_stream_handler: await self.market_stream_handler.disconnect()
        if self.user_stream_handler: await self.user_stream_handler.disconnect()
        
        await self.http_client.close_http_client()
        self._is_connected_http = False
        logger.info("TopStepXProvider disconnected (HTTP client and streams).")


    # --- TradingPlatformAPI HTTP/REST Methods Implementation ---

    async def get_accounts(self) -> List[GenericAccount]:
        if not self._is_connected_http: await self.connect()
        ts_response = await self.http_client.ts_get_accounts(only_active=True)
        return mapper.map_ts_accounts_to_generic(ts_response.accounts, self.provider_name)

    async def search_contracts(self, search_text: str, asset_class: Optional[AssetClass] = None) -> List[GenericContract]:
        if not self._is_connected_http: await self.connect()
        if asset_class and asset_class != AssetClass.FUTURES:
            logger.warning(f"TopStepXProvider: Asset class filter '{asset_class}' ignored; only FUTURES are supported.")
        ts_response = await self.http_client.ts_search_contracts(search_text=search_text, live=False)
        return mapper.map_ts_contracts_to_generic(ts_response.contracts, self.provider_name)

    async def get_contract_details(self, provider_contract_id: str) -> Optional[GenericContract]:
        if not self._is_connected_http: await self.connect()
        ts_response = await self.http_client.ts_get_contract_by_id(contract_id=provider_contract_id)
        if ts_response.contract:
            return mapper.map_ts_contract_to_generic(ts_response.contract, self.provider_name)
        raise NotFoundError(f"Contract with provider_id '{provider_contract_id}' not found on TopStepX.")

    async def get_historical_bars(self, request: GenericHistoricalBarsRequest) -> GenericHistoricalBarsResponse:
        if not self._is_connected_http: await self.connect()
        ts_unit = mapper.map_generic_bar_unit_to_ts(request.timeframe_unit)
        ts_request = TSRetrieveBarRequest(
            contractId=request.provider_contract_id,
            live=False, startTime=request.start_time_utc, endTime=request.end_time_utc,
            unit=ts_unit, unitNumber=request.timeframe_value,
            limit=1000, includePartialBar=False
        )
        ts_response = await self.http_client.ts_get_historical_bars(ts_request)
        generic_bars = [
            GenericBarData(
                timestamp_utc=b.t, open=float(b.o), high=float(b.h),
                low=float(b.l), close=float(b.c), volume=float(b.v),
                provider_name=self.provider_name, provider_specific_data=b.model_dump()
            ) for b in ts_response.bars
        ]
        return GenericHistoricalBarsResponse(request=request, bars=generic_bars, provider_name=self.provider_name)

    async def place_order(self, order_request: GenericPlaceOrderRequest) -> GenericOrderPlacementResponse:
        if not self._is_connected_http: await self.connect()
        try:
            ts_order_req_model = mapper.map_generic_place_order_to_ts_request(order_request)
            ts_response = await self.http_client.ts_place_order(ts_order_req_model)
            return GenericOrderPlacementResponse(
                order_id_acknowledged=ts_response.success and ts_response.orderId is not None,
                provider_order_id=str(ts_response.orderId) if ts_response.orderId else None,
                initial_order_status=mapper.map_ts_order_status_to_generic(ts_response.errorCode) if not ts_response.success else OrderStatus.PENDING_SUBMIT,
                message=ts_response.errorMessage if not ts_response.success else "Order submitted successfully.",
                provider_name=self.provider_name,
                provider_specific_data=ts_response.model_dump(exclude_none=True)
            )
        except (OperationFailedError, InvalidParameterError, TradeForgeConnectionError) as e:
            logger.error(f"Error placing TopStepX order: {e}")
            return GenericOrderPlacementResponse(order_id_acknowledged=False, message=str(e), provider_name=self.provider_name)

    async def cancel_order(self, provider_account_id: str, provider_order_id: str) -> GenericCancellationResponse:
        if not self._is_connected_http: await self.connect()
        acc_id, ord_id = int(provider_account_id), int(provider_order_id)
        ts_response = await self.http_client.ts_cancel_order(account_id=acc_id, order_id=ord_id)
        return GenericCancellationResponse(
            success=ts_response.success,
            message=ts_response.errorMessage if not ts_response.success else "Cancellation request submitted.",
            provider_name=self.provider_name,
            provider_specific_data=ts_response.model_dump(exclude_none=True)
        )

    async def modify_order(self, modify_request: GenericModifyOrderRequest) -> GenericModificationResponse:
        if not self._is_connected_http: await self.connect()
        ts_modify_req = TSTopStepModifyOrderRequest(
            accountId=int(modify_request.provider_account_id),
            orderId=int(modify_request.provider_order_id),
            size=int(modify_request.new_size) if modify_request.new_size is not None else None,
            limitPrice=Decimal(str(modify_request.new_limit_price)) if modify_request.new_limit_price is not None else None,
            stopPrice=Decimal(str(modify_request.new_stop_price)) if modify_request.new_stop_price is not None else None,
        )
        ts_response = await self.http_client.ts_modify_order(ts_modify_req)
        return GenericModificationResponse(
            success=ts_response.success,
            message=ts_response.errorMessage if not ts_response.success else "Modification request submitted.",
            provider_name=self.provider_name,
            provider_specific_data=ts_response.model_dump(exclude_none=True)
        )

    async def get_order_by_id(self, provider_account_id: str, provider_order_id: str) -> Optional[GenericOrder]:
        if not self._is_connected_http: await self.connect()
        acc_id, ord_id = int(provider_account_id), int(provider_order_id)
        end_time = datetime.now(UTC_TZ); start_time = end_time - timedelta(days=7)
        search_req = TSSearchOrderRequest(accountId=acc_id, startTimestamp=start_time, endTimestamp=end_time)
        ts_response = await self.http_client.ts_search_orders(search_req)
        for ts_order in ts_response.orders:
            if ts_order.id == ord_id:
                return mapper.map_ts_order_details_to_generic(ts_order, self.provider_name)
        return None

    async def get_open_orders(self, provider_account_id: str, provider_contract_id: Optional[str] = None) -> List[GenericOrder]:
        if not self._is_connected_http: await self.connect()
        search_req = TSSearchOpenOrderRequest(accountId=int(provider_account_id))
        ts_response = await self.http_client.ts_search_open_orders(search_req)
        generic_orders = mapper.map_ts_orders_to_generic(ts_response.orders, self.provider_name)
        if provider_contract_id:
            return [o for o in generic_orders if o.provider_contract_id == provider_contract_id]
        return generic_orders
    
    async def get_positions(self, provider_account_id: str) -> List[GenericPosition]:
        if not self._is_connected_http: await self.connect()
        ts_response = await self.http_client.ts_search_open_positions(int(provider_account_id))
        return mapper.map_ts_positions_to_generic(ts_response.positions, self.provider_name)

    async def close_position(self, provider_account_id: str, provider_contract_id: str, size_to_close: Optional[float] = None) -> GenericOrderPlacementResponse:
        if not self._is_connected_http: await self.connect()
        acc_id = int(provider_account_id)
        if size_to_close is not None:
            ts_response = await self.http_client.ts_partial_close_contract_position(acc_id, provider_contract_id, int(size_to_close))
        else:
            ts_response = await self.http_client.ts_close_contract_position(acc_id, provider_contract_id)
        return GenericOrderPlacementResponse(
            order_id_acknowledged=ts_response.success, provider_order_id=None,
            initial_order_status=OrderStatus.PENDING_SUBMIT if ts_response.success else OrderStatus.REJECTED,
            message=ts_response.errorMessage if not ts_response.success else "Close position request submitted.",
            provider_name=self.provider_name
        )

    async def get_trade_history(self, provider_account_id: str, provider_contract_id: Optional[str] = None, start_time_utc: Optional[datetime] = None, end_time_utc: Optional[datetime] = None, limit: Optional[int] = None) -> List[GenericTrade]:
        if not self._is_connected_http: await self.connect()
        _end = end_time_utc or datetime.now(UTC_TZ)
        _start = start_time_utc or (_end - timedelta(days=7))
        search_req = TSSearchTradeRequest(accountId=int(provider_account_id), startTimestamp=_start, endTimestamp=_end)
        ts_response = await self.http_client.ts_search_trades(search_req)
        generic_trades = mapper.map_ts_trades_to_generic(ts_response.trades, self.provider_name)
        if provider_contract_id:
            generic_trades = [t for t in generic_trades if t.provider_contract_id == provider_contract_id]
        if limit:
            generic_trades = generic_trades[-limit:]
        return generic_trades

    # --- RealTimeStream Interface Methods Implementation ---
    async def _internal_event_handler(self, event: GenericStreamEvent):
        if self._user_event_callback: await self._user_event_callback(event)

    async def _internal_status_handler(self, status: StreamConnectionStatus, reason: Optional[str]):
        logger.info(f"TopStepXProvider forwarding stream status: {status.value} (Reason: {reason})")
        if self._user_status_callback: await self._user_status_callback(status, reason)

    async def _internal_error_handler(self, error: Exception):
        logger.error(f"TopStepXProvider forwarding stream error: {error}", exc_info=True)
        if self._user_error_callback: await self._user_error_callback(error)

    async def _ensure_http_client_auth_for_streams(self):
        if not self._is_connected_http or not self.http_client._token:
            await self.connect()
            if not self.http_client._token:
                raise AuthenticationError("Failed to obtain token for stream initialization.")

    async def _init_stream_handlers_if_needed(self):
        await self._ensure_http_client_auth_for_streams()
        token = self.http_client._token
        if not token: raise AuthenticationError("Cannot initialize streams, no token.")

        if self.market_stream_handler is None:
            logger.info("Initializing TopStepXMarketStreamInternal...")
            self.market_stream_handler = TopStepXMarketStreamInternal(
                initial_token=token, environment_base_url=self.http_client.base_url,
                event_callback=self._internal_event_handler, status_callback=self._internal_status_handler,
                error_callback=self._internal_error_handler
            )
            self.market_stream_handler.mapper = mapper

        if self.user_stream_handler is None:
            logger.info("Initializing TopStepXUserStreamInternal...")
            self.user_stream_handler = TopStepXUserStreamInternal(
                initial_token=token, environment_base_url=self.http_client.base_url,
                event_callback=self._internal_event_handler, status_callback=self._internal_status_handler,
                error_callback=self._internal_error_handler
            )
            self.user_stream_handler.mapper = mapper

    async def subscribe_market_data(self, provider_contract_ids: List[str], data_types: List[MarketDataType]):
        if self.market_stream_handler is None: await self._init_stream_handlers_if_needed()
        if self.market_stream_handler:
            for contract_id in provider_contract_ids:
                await self.market_stream_handler.subscribe_contract(contract_id, data_types)
        else: raise TradeForgeConnectionError("Market stream handler not properly initialized.")

    async def unsubscribe_market_data(self, provider_contract_ids: List[str], data_types: List[MarketDataType]):
        if self.market_stream_handler:
            for contract_id in provider_contract_ids:
                await self.market_stream_handler.unsubscribe_contract(contract_id, data_types)
        else: logger.warning("Market stream handler not initialized; cannot unsubscribe.")

    async def subscribe_user_data(self, provider_account_ids: List[str], data_types: List[UserDataType]):
        if self.user_stream_handler is None: await self._init_stream_handlers_if_needed()
        if self.user_stream_handler:
            if UserDataType.ACCOUNT_UPDATE in data_types:
                await self.user_stream_handler.subscribe_global_accounts()
            
            specific_types = [dt for dt in data_types if dt != UserDataType.ACCOUNT_UPDATE]
            if specific_types:
                for acc_id in provider_account_ids:
                    await self.user_stream_handler.subscribe_account(acc_id, specific_types)
        else: raise TradeForgeConnectionError("User stream handler not properly initialized.")

    async def unsubscribe_user_data(self, provider_account_ids: List[str], data_types: List[UserDataType]):
        if self.user_stream_handler:
            if UserDataType.ACCOUNT_UPDATE in data_types:
                await self.user_stream_handler.unsubscribe_global_accounts()
            specific_types = [dt for dt in data_types if dt != UserDataType.ACCOUNT_UPDATE]
            if specific_types:
                for acc_id in provider_account_ids:
                    await self.user_stream_handler.unsubscribe_account(acc_id, specific_types)
        else: logger.warning("User stream handler not initialized; cannot unsubscribe.")

    def get_status(self) -> StreamConnectionStatus:
        market_status = self.market_stream_handler.current_status if self.market_stream_handler else StreamConnectionStatus.DISCONNECTED
        user_status = self.user_stream_handler.current_status if self.user_stream_handler else StreamConnectionStatus.DISCONNECTED
        if market_status == StreamConnectionStatus.ERROR or user_status == StreamConnectionStatus.ERROR:
            return StreamConnectionStatus.ERROR
        if market_status == StreamConnectionStatus.CONNECTING or user_status == StreamConnectionStatus.CONNECTING:
            return StreamConnectionStatus.CONNECTING
        # If at least one initialized stream is connected, we're broadly connected.
        if (self.market_stream_handler and market_status == StreamConnectionStatus.CONNECTED) or \
           (self.user_stream_handler and user_status == StreamConnectionStatus.CONNECTED):
            return StreamConnectionStatus.CONNECTED
        return StreamConnectionStatus.DISCONNECTED

    def on_event(self, callback: GenericStreamEventCallback):
        self._user_event_callback = callback
    def on_status_change(self, callback: StreamStatusCallback):
        self._user_status_callback = callback
    def on_error(self, callback: StreamErrorCallback):
        self._user_error_callback = callback

    async def run_forever(self) -> None:
        if self._stream_runner_task and not self._stream_runner_task.done():
            logger.warning("run_forever called, but a runner task already exists.")
            await self._stream_runner_task
            return

        # Initialize handlers if they haven't been by a subscribe call yet
        await self._init_stream_handlers_if_needed()

        tasks = []
        if self.market_stream_handler: tasks.append(self.market_stream_handler.connect_and_run_forever())
        if self.user_stream_handler: tasks.append(self.user_stream_handler.connect_and_run_forever())

        if not tasks:
            logger.warning("run_forever called, but no streams configured to run. Idling.")
            await asyncio.sleep(3600*24) # Block indefinitely
            return

        logger.info(f"TopStepXProvider running {len(tasks)} stream(s) concurrently.")
        try:
            self._stream_runner_task = asyncio.gather(*tasks)
            await self._stream_runner_task
        except asyncio.CancelledError:
            logger.info("TopStepXProvider stream runner task was cancelled.")
        except Exception as e_gather:
            logger.error(f"Error in provider's stream runner (gather): {e_gather}", exc_info=True)
            if self._user_error_callback: await self._user_error_callback(e_gather)
        finally:
            self._stream_runner_task = None