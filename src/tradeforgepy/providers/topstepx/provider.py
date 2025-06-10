# tradeforgepy/providers/topstepx/provider.py
import logging
import os
import asyncio
from typing import List, Optional, Dict
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
    Position as GenericPosition, Trade as GenericTrade, GenericStreamEvent, OrderStatus
)
from tradeforgepy.core.enums import AssetClass, StreamConnectionStatus, MarketDataType, UserDataType
from tradeforgepy.exceptions import (
    ConfigurationError, AuthenticationError, ConnectionError as TradeForgeConnectionError,
    OperationFailedError, NotFoundError, InvalidParameterError
)
from tradeforgepy.utils.time_utils import UTC_TZ

from .client import TopStepXHttpClient
from . import mapper
from .schemas_ts import (
    TSRetrieveBarRequest, TSSearchOrderRequest, TSSearchOpenOrderRequest,
    TSCloseContractPositionRequest, TSPartialCloseContractPositionRequest,
    TSSearchTradeRequest, TSModifyOrderRequest as TSTopStepModifyOrderRequest
)
from .streams import TopStepXMarketStreamInternal, TopStepXUserStreamInternal

logger = logging.getLogger(__name__)

# --- Correct, Hardcoded Stream URLs ---
TS_MARKET_HUB_DEMO = "gateway-rtc-demo.s2f.projectx.com/hubs/market"
TS_MARKET_HUB_LIVE = "rtc.topstepx.com/hubs/market"
TS_USER_HUB_DEMO = "gateway-rtc-demo.s2f.projectx.com/hubs/user"
TS_USER_HUB_LIVE = "rtc.topstepx.com/hubs/user"

class TopStepXProvider(TradingPlatformAPI, RealTimeStream):
    provider_name: str = "TopStepX"

    def __init__(self, username: Optional[str] = None, api_key: Optional[str] = None,
                 environment: Optional[str] = None,
                 connect_timeout: float = 10.0, read_timeout: float = 30.0):
        _username = username or os.getenv("TS_USERNAME")
        _api_key = api_key or os.getenv("TS_API_KEY")
        self.environment = (environment or os.getenv("TS_ENVIRONMENT", "DEMO")).upper()

        if not _username or not _api_key:
            raise ConfigurationError("TopStepXProvider requires username and API key.")
        
        self.http_client = TopStepXHttpClient(
            username=_username, api_key=_api_key, environment=self.environment,
            connect_timeout=connect_timeout, read_timeout=read_timeout
        )
        self._is_connected_http = False
        
        self.market_stream_handler: Optional[TopStepXMarketStreamInternal] = None
        self.user_stream_handler: Optional[TopStepXUserStreamInternal] = None
        
        self._user_event_callback: Optional[GenericStreamEventCallback] = None
        self._user_status_callback: Optional[StreamStatusCallback] = None
        self._user_error_callback: Optional[StreamErrorCallback] = None
        
        self._run_forever_task: Optional[asyncio.Task] = None

        logger.info(f"TopStepXProvider initialized for environment: {self.environment}")

    async def connect(self) -> None:
        if not self._is_connected_http:
            try:
                await self.http_client._authenticate()
                self._is_connected_http = True
                logger.info("TopStepXProvider HTTP client connected and authenticated successfully.")
            except Exception as e:
                self._is_connected_http = False
                logger.error(f"TopStepXProvider HTTP connection/authentication failed: {e}")
                raise TradeForgeConnectionError(f"HTTP Auth failed: {e}") from e

    async def disconnect(self) -> None:
        logger.info("TopStepXProvider disconnecting...")
        if self._run_forever_task and not self._run_forever_task.done():
            self._run_forever_task.cancel()
            try:
                await self._run_forever_task
            except asyncio.CancelledError:
                logger.info("Provider's main run_forever task was cancelled.")
        
        disconnect_tasks = []
        if self.market_stream_handler:
            disconnect_tasks.append(self.market_stream_handler.disconnect())
        if self.user_stream_handler:
            disconnect_tasks.append(self.user_stream_handler.disconnect())
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        await self.http_client.close_http_client()
        self._is_connected_http = False
        logger.info("TopStepXProvider disconnected.")
    
    # ... All REST API methods are correct and unchanged ...
    async def get_accounts(self) -> List[GenericAccount]:
        if not self._is_connected_http: await self.connect()
        ts_response = await self.http_client.ts_get_accounts(only_active=True)
        return mapper.map_ts_accounts_to_generic(ts_response.accounts, self.provider_name)

    async def search_contracts(self, search_text: str, asset_class: Optional[AssetClass] = None) -> List[GenericContract]:
        if not self._is_connected_http: await self.connect()
        is_live = self.environment == 'LIVE'
        ts_response = await self.http_client.ts_search_contracts(search_text=search_text, live=is_live)
        return mapper.map_ts_contracts_to_generic(ts_response.contracts, self.provider_name)

    async def get_contract_details(self, provider_contract_id: str) -> Optional[GenericContract]:
        if not self._is_connected_http: await self.connect()
        ts_response = await self.http_client.ts_get_contract_by_id(contract_id=provider_contract_id)
        if ts_response.contract:
            return mapper.map_ts_contract_to_generic(ts_response.contract, self.provider_name)
        raise NotFoundError(f"Contract with provider_id '{provider_contract_id}' not found on TopStepX.")

    async def get_historical_bars(self, request: GenericHistoricalBarsRequest) -> GenericHistoricalBarsResponse:
        if not self._is_connected_http: await self.connect()
        is_live = self.environment == 'LIVE'
        ts_unit = mapper.map_generic_bar_unit_to_ts(request.timeframe_unit)
        ts_request = TSRetrieveBarRequest(
            contractId=request.provider_contract_id,
            live=is_live, startTime=request.start_time_utc, endTime=request.end_time_utc,
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
            initial_status = OrderStatus.PENDING_SUBMIT if ts_response.success else OrderStatus.REJECTED
            return GenericOrderPlacementResponse(
                order_id_acknowledged=ts_response.success and ts_response.orderId is not None,
                provider_order_id=str(ts_response.orderId) if ts_response.orderId else None,
                initial_order_status=initial_status,
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
            provider_order_id=modify_request.provider_order_id,
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
            generic_trades = sorted(generic_trades, key=lambda t: t.timestamp_utc, reverse=True)
            generic_trades = generic_trades[:limit]
        return generic_trades

    async def _internal_event_handler(self, event: GenericStreamEvent):
        if self._user_event_callback: await self._user_event_callback(event)

    async def _internal_status_handler(self, stream_name: str, status: StreamConnectionStatus, reason: Optional[str]):
        if self._user_status_callback:
            overall_status = self.get_status()
            await self._user_status_callback(overall_status, f"{stream_name}: {reason or status.value}")

    async def _internal_error_handler(self, stream_name: str, error: Exception):
        if self._user_error_callback: await self._user_error_callback(error)

    async def _init_stream_handlers_if_needed(self):
        # The connect() method ensures we are authenticated.
        if not self._is_connected_http or not self.http_client._token:
             raise AuthenticationError("Must be connected via provider.connect() before initializing streams.")
        
        token = self.http_client._token
        
        market_hub_url = TS_MARKET_HUB_LIVE if self.environment == 'LIVE' else TS_MARKET_HUB_DEMO
        user_hub_url = TS_USER_HUB_LIVE if self.environment == 'LIVE' else TS_USER_HUB_DEMO

        if self.market_stream_handler is None:
            self.market_stream_handler = TopStepXMarketStreamInternal(
                hub_url=market_hub_url, initial_token=token,
                event_callback=self._internal_event_handler, 
                status_callback=self._internal_status_handler,
                error_callback=self._internal_error_handler,
                stream_name="MarketStream"
            )
            self.market_stream_handler.mapper = mapper

        if self.user_stream_handler is None:
            self.user_stream_handler = TopStepXUserStreamInternal(
                hub_url=user_hub_url, initial_token=token,
                event_callback=self._internal_event_handler,
                status_callback=self._internal_status_handler,
                error_callback=self._internal_error_handler,
                stream_name="UserStream"
            )
            self.user_stream_handler.mapper = mapper

    async def subscribe_market_data(self, provider_contract_ids: List[str], data_types: List[MarketDataType]):
        if not self.market_stream_handler: await self._init_stream_handlers_if_needed()
        if self.market_stream_handler:
            for contract_id in provider_contract_ids:
                # Let the handler manage when to send the subscription
                await self.market_stream_handler.subscribe_contract(contract_id, data_types)
        else: raise TradeForgeConnectionError("Market stream handler not initialized.")

    async def unsubscribe_market_data(self, provider_contract_ids: List[str], data_types: List[MarketDataType]):
        if self.market_stream_handler:
            for contract_id in provider_contract_ids:
                await self.market_stream_handler.unsubscribe_contract(contract_id, data_types)

    async def subscribe_user_data(self, provider_account_ids: List[str], data_types: List[UserDataType]):
        if not self.user_stream_handler: await self._init_stream_handlers_if_needed()
        if self.user_stream_handler:
            if UserDataType.ACCOUNT_UPDATE in data_types:
                await self.user_stream_handler.subscribe_global_accounts()
            
            specific_types = [dt for dt in data_types if dt != UserDataType.ACCOUNT_UPDATE]
            if specific_types:
                for acc_id in provider_account_ids:
                    await self.user_stream_handler.subscribe_account(acc_id, specific_types)

    async def unsubscribe_user_data(self, provider_account_ids: List[str], data_types: List[UserDataType]):
        if self.user_stream_handler:
            if UserDataType.ACCOUNT_UPDATE in data_types:
                await self.user_stream_handler.unsubscribe_global_accounts()
            specific_types = [dt for dt in data_types if dt != UserDataType.ACCOUNT_UPDATE]
            if specific_types:
                for acc_id in provider_account_ids:
                    await self.user_stream_handler.unsubscribe_account(acc_id, specific_types)

    def get_status(self) -> StreamConnectionStatus:
        statuses = self.get_stream_statuses().values()
        if not statuses: return StreamConnectionStatus.DISCONNECTED
        if StreamConnectionStatus.ERROR in statuses: return StreamConnectionStatus.ERROR
        if StreamConnectionStatus.CONNECTING in statuses: return StreamConnectionStatus.CONNECTING
        initialized_handlers = [h for h in [self.market_stream_handler, self.user_stream_handler] if h is not None]
        if not initialized_handlers: return StreamConnectionStatus.DISCONNECTED
        if all(h.current_status == StreamConnectionStatus.CONNECTED for h in initialized_handlers):
            return StreamConnectionStatus.CONNECTED
        if any(h.current_status == StreamConnectionStatus.CONNECTED for h in initialized_handlers):
            return StreamConnectionStatus.CONNECTING
        return StreamConnectionStatus.DISCONNECTED

    def get_market_stream_status(self) -> StreamConnectionStatus:
        return self.market_stream_handler.current_status if self.market_stream_handler else StreamConnectionStatus.DISCONNECTED

    def get_user_stream_status(self) -> StreamConnectionStatus:
        return self.user_stream_handler.current_status if self.user_stream_handler else StreamConnectionStatus.DISCONNECTED

    def get_stream_statuses(self) -> Dict[str, StreamConnectionStatus]:
        return {
            'market': self.get_market_stream_status(),
            'user': self.get_user_stream_status()
        }

    def on_event(self, callback: GenericStreamEventCallback): self._user_event_callback = callback
    def on_status_change(self, callback: StreamStatusCallback): self._user_status_callback = callback
    def on_error(self, callback: StreamErrorCallback): self._user_error_callback = callback

    async def run_forever(self) -> None:
        if self._run_forever_task and not self._run_forever_task.done():
            logger.warning("run_forever called, but a runner task already exists.")
            await self._run_forever_task
            return

        await self._init_stream_handlers_if_needed()

        tasks = []
        if self.market_stream_handler:
            tasks.append(self.market_stream_handler.connect_and_run_forever())
        if self.user_stream_handler:
            tasks.append(self.user_stream_handler.connect_and_run_forever())

        if not tasks:
            logger.warning("run_forever called, but no streams configured to run. Idling.")
            await asyncio.Event().wait()
            return

        logger.info(f"TopStepXProvider running {len(tasks)} stream(s) concurrently.")
        try:
            self._run_forever_task = asyncio.gather(*tasks)
            await self._run_forever_task
        except asyncio.CancelledError:
            logger.info("TopStepXProvider stream runner task was cancelled.")
        except Exception as e:
            logger.error(f"Error in provider's stream runner (gather): {e}", exc_info=True)
            if self._user_error_callback:
                await self._user_error_callback(e)
        finally:
            self._run_forever_task = None