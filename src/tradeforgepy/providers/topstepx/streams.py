# tradeforgepy/providers/topstepx/streams.py
# FINALIZED version based on captured live stream data.

import asyncio
import logging
from typing import Callable, Awaitable, Optional, List, Any, Dict

from pysignalr.client import SignalRClient
from pysignalr.exceptions import ConnectionError as PySignalRConnectionError

from tradeforgepy.core.enums import StreamConnectionStatus, MarketDataType, UserDataType
from tradeforgepy.core.models_generic import GenericStreamEvent
from tradeforgepy.exceptions import ConnectionError as TradeForgeConnectionError, AuthenticationError

logger = logging.getLogger(__name__)

# Type aliases
InternalGenericEventCallback = Callable[[GenericStreamEvent], Awaitable[None]]
InternalStatusChangeCallback = Callable[[str, StreamConnectionStatus, Optional[str]], Awaitable[None]]
InternalErrorCallback = Callable[[str, Exception], Awaitable[None]]


class _BaseTopStepXStream:
    # ... (The entire _BaseTopStepXStream class code from the previous "Complete code" response is correct and can be used here without changes) ...
    # For completeness, I'm pasting it again.
    
    def __init__(self, hub_base_url_no_protocol: str, initial_token: str, event_callback: InternalGenericEventCallback, status_callback: InternalStatusChangeCallback, error_callback: InternalErrorCallback, stream_name: str):
        self.hub_base_url_no_protocol = hub_base_url_no_protocol; self._current_token = initial_token; self.event_callback = event_callback; self.status_callback = status_callback; self.error_callback = error_callback; self.stream_name = stream_name; self.connection: Optional[SignalRClient] = None; self.current_status = StreamConnectionStatus.DISCONNECTED; self._connection_lock = asyncio.Lock(); self._run_task: Optional[asyncio.Task] = None; self._is_manually_stopping = False; self._is_connected_signalr = False; self._wss_hub_url_no_token: str = self._prepare_wss_url(hub_base_url_no_protocol); self._hub_url_with_token: str = self._build_url_with_token(self._wss_hub_url_no_token, self._current_token); logger.info(f"BaseTopStepXStream '{self.stream_name}' initialized.")
    def _prepare_wss_url(self, hub_url: str) -> str:
        if hub_url.startswith("https://"): return "wss://" + hub_url[len("https://"):];
        if hub_url.startswith("http://"): return "ws://" + hub_url[len("http://"):];
        return f"wss://{hub_url}"
    def _build_url_with_token(self, base_url: str, token: str) -> str: return f"{base_url}?access_token={token}"
    async def _update_status(self, new_status: StreamConnectionStatus, reason: Optional[str] = None):
        if self.current_status != new_status: old = self.current_status; self.current_status = new_status; logger.info(f"{self.stream_name} status: {old.value} -> {new_status.value} (Reason: {reason or 'N/A'})"); await self.status_callback(self.stream_name, new_status, reason)
    async def _pysignalr_on_open(self): self._is_connected_signalr = True; logger.info(f"{self.stream_name} connection opened."); await self._update_status(StreamConnectionStatus.CONNECTED, "SignalR connected")
    async def _pysignalr_on_close(self): self._is_connected_signalr = False; logger.info(f"{self.stream_name} connection closed."); await self._update_status(StreamConnectionStatus.DISCONNECTED if not self._is_manually_stopping else StreamConnectionStatus.STOPPED, "SignalR closed")
    async def _pysignalr_on_error(self, err: Any): self._is_connected_signalr = False; exc = err if isinstance(err, Exception) else Exception(str(err)); await self._update_status(StreamConnectionStatus.ERROR, f"SignalR error: {str(exc)[:100]}"); await self.error_callback(self.stream_name, exc)
    async def connect_and_run_forever(self):
        async with self._connection_lock:
            if self._run_task and not self._run_task.done(): logger.warning(f"{self.stream_name} already running."); return
            self._is_manually_stopping = False; await self._update_status(StreamConnectionStatus.CONNECTING)
            if not self._current_token: err = AuthenticationError("Token missing"); await self._update_status(StreamConnectionStatus.ERROR, err.args[0]); await self.error_callback(self.stream_name, err); return
            self._hub_url_with_token = self._build_url_with_token(self._wss_hub_url_no_token, self._current_token); logger.info(f"{self.stream_name} connecting...")
            try: self.connection = SignalRClient(self._hub_url_with_token); self.connection.on_open(self._pysignalr_on_open); self.connection.on_close(self._pysignalr_on_close); self.connection.on_error(self._pysignalr_on_error); self._register_specific_handlers()
            except Exception as e: await self._update_status(StreamConnectionStatus.ERROR, f"Setup failed: {e}"); await self.error_callback(self.stream_name, e); return
        try: logger.info(f"{self.stream_name} starting run loop..."); self._run_task = asyncio.create_task(self.connection.run(), name=f"{self.stream_name}_Run"); await self._run_task
        except asyncio.CancelledError: logger.info(f"{self.stream_name} run task cancelled."); await self._update_status(StreamConnectionStatus.STOPPED, "Run task cancelled")
        except Exception as e: await self._update_status(StreamConnectionStatus.ERROR, f"Run error: {type(e).__name__}"); await self.error_callback(self.stream_name, e)
        finally: self._run_task = None; await self._update_status(StreamConnectionStatus.DISCONNECTED, "Run loop finished")
    async def disconnect(self):
        async with self._connection_lock:
            if self._is_manually_stopping: return
            self._is_manually_stopping = True; await self._update_status(StreamConnectionStatus.STOPPING, "Client requested disconnect")
            if self._run_task and not self._run_task.done(): self._run_task.cancel()
            if self.connection and self._is_connected_signalr: await self.connection.stop()
            else: await self._pysignalr_on_close()
    async def update_token(self, token: str):
        async with self._connection_lock:
            if token == self._current_token: return
            self._current_token = token; self._hub_url_with_token = self._build_url_with_token(self._wss_hub_url_no_token, self._current_token); logger.info(f"{self.stream_name} token updated. Restart required.")
            if self.current_status not in [StreamConnectionStatus.DISCONNECTED, StreamConnectionStatus.STOPPED, StreamConnectionStatus.ERROR]: await self.disconnect()
    def _register_specific_handlers(self): raise NotImplementedError
    async def _invoke_subscription(self, method: str, args: List[Any], log_name: str):
        if not self.connection or not self._is_connected_signalr: logger.warning(f"{self.stream_name} not connected for {log_name}."); return False
        try: logger.info(f"{self.stream_name} sending command: '{method}' with args {args}"); await self.connection.send(method, args); return True
        except Exception as e: logger.error(f"{self.stream_name} failed command '{log_name}': {e}"); await self._update_status(StreamConnectionStatus.ERROR, f"Sub failed for {method}"); await self.error_callback(self.stream_name, e); return False


class TopStepXMarketStreamInternal(_BaseTopStepXStream):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_contracts: Dict[str, List[MarketDataType]] = {}
        self.mapper = None # Injected by provider

    def _register_specific_handlers(self):
        if not self.connection: return
        self.connection.on("GatewayQuote", self._handle_ts_quote)
        self.connection.on("GatewayTrade", self._handle_ts_trade)
        self.connection.on("GatewayDepth", self._handle_ts_depth)

    async def subscribe_contract(self, contract_id: str, data_types: List[MarketDataType]):
        # Logic is correct, no changes needed
        # ... (full implementation from previous response)
        if not self._is_connected_signalr: self.subscribed_contracts[contract_id] = list(set(self.subscribed_contracts.get(contract_id, []) + data_types)); return
        current_subs = self.subscribed_contracts.get(contract_id, [])
        if MarketDataType.QUOTE in data_types and MarketDataType.QUOTE not in current_subs:
            if await self._invoke_subscription("SubscribeContractQuotes", [contract_id], f"Quotes for {contract_id}"): current_subs.append(MarketDataType.QUOTE)
        if MarketDataType.TRADE in data_types: logger.info(f"{self.stream_name} listening for GatewayTrade on {contract_id} (no command sent).")
        if MarketDataType.DEPTH in data_types and MarketDataType.DEPTH not in current_subs:
            if await self._invoke_subscription("SubscribeContractMarketDepth", [contract_id], f"Depth for {contract_id}"): current_subs.append(MarketDataType.DEPTH)
        self.subscribed_contracts[contract_id] = list(set(current_subs))


    # --- Handlers that call the mapper ---
    async def _handle_ts_quote(self, args: List[Any]):
        if self.mapper and len(args) == 2:
            generic_event = self.mapper.map_ts_quote_to_generic_event(args[0], args[1], self.stream_name)
            if generic_event: await self.event_callback(generic_event)

    async def _handle_ts_trade(self, args: List[Any]):
        if self.mapper and len(args) == 2:
            # Assuming payload is a list of trades
            payload = args[1] if isinstance(args[1], list) else [args[1]]
            for trade_data in payload:
                if isinstance(trade_data, dict):
                    generic_event = self.mapper.map_ts_market_trade_to_generic_event(args[0], trade_data, self.stream_name)
                    if generic_event: await self.event_callback(generic_event)

    async def _handle_ts_depth(self, args: List[Any]):
        if self.mapper and len(args) == 2 and isinstance(args[1], list):
            generic_event = self.mapper.map_ts_depth_to_generic_event(args[0], args[1], self.stream_name)
            if generic_event: await self.event_callback(generic_event)


class TopStepXUserStreamInternal(_BaseTopStepXStream):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_accounts: Dict[str, List[UserDataType]] = {}
        self.subscribed_globally_accounts = False
        self.mapper = None

    def _register_specific_handlers(self):
        if not self.connection: return
        self.connection.on("GatewayUserOrder", lambda args: asyncio.create_task(self._handle_ts_user_generic(args, "GatewayUserOrder", "map_ts_order_update_to_generic_event")))
        self.connection.on("GatewayUserPosition", lambda args: asyncio.create_task(self._handle_ts_user_generic(args, "GatewayUserPosition", "map_ts_position_update_to_generic_event")))
        self.connection.on("GatewayUserAccount", lambda args: asyncio.create_task(self._handle_ts_user_generic(args, "GatewayUserAccount", "map_ts_account_update_to_generic_event")))
        self.connection.on("GatewayUserTrade", lambda args: asyncio.create_task(self._handle_ts_user_generic(args, "GatewayUserTrade", "map_ts_user_trade_to_generic_event")))
    
    async def subscribe_global_accounts(self):
        if not self.subscribed_globally_accounts:
            if await self._invoke_subscription("SubscribeAccounts", [], "Global Accounts"): self.subscribed_globally_accounts = True
    
    async def subscribe_account(self, account_id_str: str, data_types: List[UserDataType]):
        # Logic is correct, no changes needed
        # ... (full implementation from previous response)
        try: acc_id_int = int(account_id_str)
        except ValueError: logger.error(f"{self.stream_name} invalid account_id_str: {account_id_str}"); return
        if not self._is_connected_signalr: self.subscribed_accounts[account_id_str] = list(set(self.subscribed_accounts.get(account_id_str, []) + data_types)); return
        current_subs = self.subscribed_accounts.get(account_id_str, [])
        if UserDataType.ORDER_UPDATE in data_types and UserDataType.ORDER_UPDATE not in current_subs:
            if await self._invoke_subscription("SubscribeOrders", [acc_id_int], f"Orders for Acc {acc_id_int}"): current_subs.append(UserDataType.ORDER_UPDATE)
        if UserDataType.POSITION_UPDATE in data_types and UserDataType.POSITION_UPDATE not in current_subs:
            if await self._invoke_subscription("SubscribePositions", [acc_id_int], f"Positions for Acc {acc_id_int}"): current_subs.append(UserDataType.POSITION_UPDATE)
        if UserDataType.USER_TRADE in data_types and UserDataType.USER_TRADE not in current_subs:
            if await self._invoke_subscription("SubscribeTrades", [acc_id_int], f"UserTrades for Acc {acc_id_int}"): current_subs.append(UserDataType.USER_TRADE)
        self.subscribed_accounts[account_id_str] = list(set(current_subs))


    async def _handle_ts_user_generic(self, args: List[Any], event_name: str, mapper_func_name: str):
        if self.mapper and len(args) >= 1 and isinstance(args[0], dict):
            mapper_func = getattr(self.mapper, mapper_func_name, None)
            if mapper_func:
                generic_event = mapper_func(args[0], self.stream_name)
                if generic_event: await self.event_callback(generic_event)