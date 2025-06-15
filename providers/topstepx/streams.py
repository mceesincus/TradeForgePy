# tradeforgepy/providers/topstepx/streams.py
import asyncio
import logging
from typing import Callable, Awaitable, Optional, List, Any, Dict, Set

from pysignalr.client import SignalRClient
from pysignalr.exceptions import ConnectionError as PySignalRConnectionError

from tradeforgepy.core.enums import StreamConnectionStatus, MarketDataType, UserDataType
from tradeforgepy.core.models_generic import GenericStreamEvent
from tradeforgepy.exceptions import ConnectionError as TradeForgeConnectionError, AuthenticationError

logger = logging.getLogger(__name__)

InternalGenericEventCallback = Callable[[GenericStreamEvent], Awaitable[None]]
InternalStatusChangeCallback = Callable[[str, StreamConnectionStatus, Optional[str]], Awaitable[None]]
InternalErrorCallback = Callable[[str, Exception], Awaitable[None]]

class _BaseTopStepXStream:
    _MAX_CONSECUTIVE_AUTH_FAILURES = 3

    def __init__(self, hub_url: str, initial_token: str, event_callback: InternalGenericEventCallback, 
                 status_callback: InternalStatusChangeCallback, error_callback: InternalErrorCallback, stream_name: str):
        self._raw_hub_url = hub_url
        self._current_token = initial_token
        self.event_callback = event_callback
        self.status_callback = status_callback
        self.error_callback = error_callback
        self.stream_name = stream_name
        self.connection: Optional[SignalRClient] = None
        self.current_status = StreamConnectionStatus.DISCONNECTED
        self._session_task: Optional[asyncio.Task] = None
        self._is_manually_stopping = False

        # --- Resilience Parameters ---
        self._reconnect_delay_sec = 2.0
        self._max_reconnect_delay_sec = 60.0
        self._consecutive_auth_failures = 0
        
        logger.info(f"BaseTopStepXStream '{self.stream_name}' initialized for URL: {self._raw_hub_url}")

    def _build_url_with_token(self) -> str:
        base_url = f"wss://{self._raw_hub_url}" if not self._raw_hub_url.startswith("wss://") else self._raw_hub_url
        return f"{base_url}?access_token={self._current_token}"

    async def _update_status(self, new_status: StreamConnectionStatus, reason: Optional[str] = None):
        if self.current_status != new_status:
            old_status = self.current_status
            self.current_status = new_status
            logger.info(f"{self.stream_name} status: {old_status.value} -> {new_status.value} (Reason: {reason or 'N/A'})")
            await self.status_callback(self.stream_name, new_status, reason)

    async def _on_open_and_subscribe(self):
        await self._update_status(StreamConnectionStatus.CONNECTED, "SignalR connection established")
        # Reset counters on successful connection
        self._reconnect_delay_sec = 2.0
        self._consecutive_auth_failures = 0
        logger.info(f"{self.stream_name} connection successful. Resilience counters reset.")
        await self._send_pending_subscriptions()

    async def _pysignalr_on_close(self):
        reason = "Manual stop" if self._is_manually_stopping else "Connection closed by server"
        status = StreamConnectionStatus.STOPPED if self._is_manually_stopping else StreamConnectionStatus.DISCONNECTED
        await self._update_status(status, reason)

    async def _pysignalr_on_error(self, err: Any):
        exc = err if isinstance(err, Exception) else PySignalRConnectionError(str(err))
        await self._update_status(StreamConnectionStatus.ERROR, f"SignalR error: {str(exc)[:100]}")
        await self.error_callback(self.stream_name, exc)

    async def run_forever(self):
        """ The public, resilient entry point for running a stream connection. """
        self._is_manually_stopping = False
        logger.info(f"'{self.stream_name}' starting resilient run loop...")

        while not self._is_manually_stopping:
            try:
                # This will block until the connection session ends for any reason.
                await self._run_single_session()

                # If the session completes without an exception, any failure chain is broken.
                self._consecutive_auth_failures = 0

                if self._is_manually_stopping:
                    logger.info(f"'{self.stream_name}' resilient loop stopped manually.")
                    break
                
                # Backoff logic for a normal disconnect
                logger.warning(f"'{self.stream_name}' session ended. Attempting reconnect in {self._reconnect_delay_sec:.1f}s...")
                await asyncio.sleep(self._reconnect_delay_sec)
                self._reconnect_delay_sec = min(self._reconnect_delay_sec * 2, self._max_reconnect_delay_sec)

            except AuthenticationError as e:
                self._consecutive_auth_failures += 1
                logger.error(f"Authentication failure #{self._consecutive_auth_failures} for '{self.stream_name}': {e}")
                await self.error_callback(self.stream_name, e)

                if self._consecutive_auth_failures >= self._MAX_CONSECUTIVE_AUTH_FAILURES:
                    final_msg = "Too many consecutive authentication failures."
                    logger.critical(
                        f"'{self.stream_name}' has failed authentication {self._consecutive_auth_failures} times. "
                        f"Stopping reconnects. Reason: {final_msg}"
                    )
                    await self._update_status(StreamConnectionStatus.ERROR, final_msg)
                    self._is_manually_stopping = True  # Break the loop permanently
                else:
                    # Still within threshold, apply backoff and retry
                    logger.warning(f"Attempting reconnect after auth failure in {self._reconnect_delay_sec:.1f}s...")
                    await asyncio.sleep(self._reconnect_delay_sec)
                    self._reconnect_delay_sec = min(self._reconnect_delay_sec * 2, self._max_reconnect_delay_sec)
            
            except asyncio.CancelledError:
                logger.info(f"'{self.stream_name}' resilient run task was cancelled.")
                self._is_manually_stopping = True # Ensure loop terminates

            except Exception as e:
                # Any other exception is treated as transient and does not increment the auth failure counter.
                logger.error(f"A transient error occurred in '{self.stream_name}' resilient loop: {e}", exc_info=True)
                await self.error_callback(self.stream_name, e)
                
                # Apply backoff and retry
                logger.warning(f"Attempting reconnect after transient error in {self._reconnect_delay_sec:.1f}s...")
                await asyncio.sleep(self._reconnect_delay_sec)
                self._reconnect_delay_sec = min(self._reconnect_delay_sec * 2, self._max_reconnect_delay_sec)


    async def _run_single_session(self):
        """ Manages a single connection attempt and its lifetime. """
        if self._session_task and not self._session_task.done():
            self._session_task.cancel()

        await self._update_status(StreamConnectionStatus.CONNECTING)

        if not self._current_token:
            err = AuthenticationError("Cannot start stream: token is missing.")
            await self._update_status(StreamConnectionStatus.ERROR, err.args[0])
            # Do not call self.error_callback here, as raising will do it in run_forever
            raise err

        hub_url_with_token = self._build_url_with_token()
        self.connection = SignalRClient(hub_url_with_token)
        self.connection.on_open(self._on_open_and_subscribe)
        self.connection.on_close(self._pysignalr_on_close)
        self.connection.on_error(self._pysignalr_on_error)
        self._register_specific_handlers()
        
        try:
            logger.info(f"'{self.stream_name}' starting new connection session...")
            # PysignalR's run() method can raise exceptions on connection failure.
            # These are caught by the run_forever loop.
            self._session_task = asyncio.create_task(self.connection.run(), name=f"{self.stream_name}_Session")
            await self._session_task
        except asyncio.CancelledError:
            logger.info(f"'{self.stream_name}' session task cancelled.")
        except Exception as e:
            # Re-raising allows the resilient loop to handle all exceptions uniformly.
            raise e
        finally:
            self._session_task = None
            if not self._is_manually_stopping:
                await self._update_status(StreamConnectionStatus.DISCONNECTED, "Session finished unexpectedly")

    async def disconnect(self):
        if self._is_manually_stopping: return
        self._is_manually_stopping = True
        await self._update_status(StreamConnectionStatus.STOPPING, "Client requested disconnect")

        if self._session_task and not self._session_task.done():
            self._session_task.cancel()
        
        # Also cancel any supervised handler tasks that might be running
        if hasattr(self, '_handler_tasks') and isinstance(self._handler_tasks, set):
            # Create a list from the set to avoid issues with changing set size during iteration
            for task in list(self._handler_tasks):
                task.cancel()
        
        # Explicitly stop the connection if it exists
        if self.connection:
            try:
                await self.connection.stop()
            except Exception as e:
                logger.warning(f"Exception during explicit connection stop for '{self.stream_name}': {e}")
                
        await self._update_status(StreamConnectionStatus.STOPPED, "Client disconnect complete")

    def _register_specific_handlers(self): raise NotImplementedError
    async def _send_pending_subscriptions(self): raise NotImplementedError

    async def _invoke_subscription_command(self, method: str, args: List[Any], log_name: str) -> bool:
        if self.current_status != StreamConnectionStatus.CONNECTED: logger.warning(f"Cannot subscribe '{log_name}' on {self.stream_name}: not connected."); return False
        try:
            logger.info(f"{self.stream_name} sending command: '{method}' with args {args}")
            await self.connection.send(method, args); return True
        except Exception as e:
            await self._update_status(StreamConnectionStatus.ERROR, f"Subscription failed for {method}"); await self.error_callback(self.stream_name, e); return False

class TopStepXMarketStreamInternal(_BaseTopStepXStream):
    def __init__(self, *args, mapper: Any, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_subscriptions: Dict[str, Set[MarketDataType]] = {}
        self.mapper = mapper
        self._subscription_lock = asyncio.Lock()

    def _register_specific_handlers(self):
        if not self.connection: return
        self.connection.on("GatewayQuote", self._handle_ts_quote)
        self.connection.on("GatewayTrade", self._handle_ts_trade)
        self.connection.on("GatewayDepth", self._handle_ts_depth)

    async def _send_pending_subscriptions(self):
        async with self._subscription_lock:
            # Create a copy of items to iterate over, as the dict can change.
            pending_items = list(self.pending_subscriptions.items())
        
        for contract_id, data_types in pending_items:
            if MarketDataType.QUOTE in data_types: await self._invoke_subscription_command("SubscribeContractQuotes", [contract_id], f"Quotes for {contract_id}")
            if MarketDataType.DEPTH in data_types: await self._invoke_subscription_command("SubscribeContractMarketDepth", [contract_id], f"Depth for {contract_id}")

    async def subscribe_contract(self, contract_id: str, data_types: List[MarketDataType]):
        async with self._subscription_lock:
            if contract_id not in self.pending_subscriptions: self.pending_subscriptions[contract_id] = set()
            self.pending_subscriptions[contract_id].update(dt for dt in data_types if dt != MarketDataType.TRADE) # TRADE is implicit
        
        if self.current_status == StreamConnectionStatus.CONNECTED:
            await self._send_pending_subscriptions()

    async def unsubscribe_contract(self, contract_id: str, data_types: List[MarketDataType]):
        async with self._subscription_lock:
            if contract_id not in self.pending_subscriptions:
                logger.warning(f"Cannot unsubscribe from {contract_id}: not subscribed.")
                return

            types_to_remove = set()
            for data_type in data_types:
                command = None
                if data_type == MarketDataType.QUOTE:
                    command = "UnsubscribeContractQuotes"
                elif data_type == MarketDataType.DEPTH:
                    command = "UnsubscribeContractMarketDepth"
                
                if command:
                    if data_type in self.pending_subscriptions.get(contract_id, set()):
                        log_msg = f"Unsubscribe {data_type.value} for {contract_id}"
                        success = await self._invoke_subscription_command(command, [contract_id], log_msg)
                        if success:
                            types_to_remove.add(data_type)
                    else:
                        logger.debug(f"Skipping unsubscribe for {data_type.value} on {contract_id}: not in pending subscriptions.")

            if types_to_remove:
                self.pending_subscriptions[contract_id].difference_update(types_to_remove)
                logger.info(f"Updated pending subscriptions for {contract_id}: removed {types_to_remove}")
                
                if not self.pending_subscriptions[contract_id]:
                    del self.pending_subscriptions[contract_id]
                    logger.info(f"Removed contract {contract_id} from all market subscriptions.")

    async def _handle_ts_quote(self, args: List[Any]):
        if self.mapper and len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            event = self.mapper.map_ts_quote_to_generic_event(args[0], args[1], self.stream_name)
            if event: await self.event_callback(event)

    async def _handle_ts_trade(self, args: List[Any]):
        if self.mapper and len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            event = self.mapper.map_ts_market_trade_to_generic_event(args[0], args[1], self.stream_name)
            if event: await self.event_callback(event)

    async def _handle_ts_depth(self, args: List[Any]):
        if self.mapper and len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], list):
            event = self.mapper.map_ts_depth_to_generic_event(args[0], args[1], self.stream_name)
            if event: await self.event_callback(event)

class TopStepXUserStreamInternal(_BaseTopStepXStream):
    def __init__(self, *args, mapper: Any, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_account_subscriptions: Dict[str, Set[UserDataType]] = {}
        self.pending_global_subscription = False
        self.mapper = mapper
        self._subscription_lock = asyncio.Lock()
        self._handler_tasks: Set[asyncio.Task] = set()

    async def _launch_and_supervise_handler(self, coro: Awaitable[None]):
        """
        Creates, runs, and supervises a background task for a specific event handler.
        If the handler task fails with an exception, it logs the error and
        triggers a cancellation of the main stream session to force a reconnect.
        """
        try:
            # Create a task to run the actual handler logic (e.g., mapping data).
            task = asyncio.create_task(coro)
            # Add the task to our tracking set for cleanup during disconnect.
            self._handler_tasks.add(task)
            # When the task is done (completes or fails), remove it from the set.
            task.add_done_callback(self._handler_tasks.discard)
            
            # Await the task. This is the key part that allows us to catch its exception.
            await task
        except asyncio.CancelledError:
            # Don't treat cancellation as a critical failure.
            pass
        except Exception as e:
            # An unhandled exception occurred within the handler coroutine.
            # This is a critical failure for this stream.
            logger.error(f"Unhandled exception in stream handler task for '{self.stream_name}': {e}", exc_info=True)
            # Report the specific error via the main error callback.
            await self.error_callback(self.stream_name, e)
            
            # Trigger a full, clean reconnect by cancelling the main session task.
            # This prevents the stream from continuing in a broken, partial state.
            if self._session_task and not self._session_task.done():
                logger.warning(f"Cancelling main stream session for '{self.stream_name}' due to handler task failure.")
                self._session_task.cancel()

    def _register_specific_handlers(self):
        if not self.connection: return

        # This helper function ensures that our supervisor itself is launched
        # in the background, allowing the `on` registration to complete instantly.
        def create_supervised_task(handler_coro: Awaitable[None]):
            asyncio.create_task(self._launch_and_supervise_handler(handler_coro))
        
        # Replace the direct "fire-and-forget" task creation with our supervised version.
        self.connection.on("GatewayUserOrder", 
            lambda args: create_supervised_task(self._handle_generic_user_event(args, "map_ts_order_update_to_generic_event")))
        self.connection.on("GatewayUserPosition", 
            lambda args: create_supervised_task(self._handle_generic_user_event(args, "map_ts_position_update_to_generic_event")))
        self.connection.on("GatewayUserAccount", 
            lambda args: create_supervised_task(self._handle_generic_user_event(args, "map_ts_account_update_to_generic_event")))
        self.connection.on("GatewayUserTrade", 
            lambda args: create_supervised_task(self._handle_generic_user_event(args, "map_ts_user_trade_to_generic_event")))

    async def _send_pending_subscriptions(self):
        async with self._subscription_lock:
            # Create a copy of state to iterate over
            is_global_sub = self.pending_global_subscription
            pending_accs = list(self.pending_account_subscriptions.items())

        if is_global_sub:
            await self._invoke_subscription_command("SubscribeAccounts", [], "Global Accounts")
        
        for acc_id_str, data_types in pending_accs:
            try:
                acc_id_int = int(acc_id_str)
                # Resubscribe based on the stored desired state.
                if UserDataType.ORDER_UPDATE in data_types: await self._invoke_subscription_command("SubscribeOrders", [acc_id_int], f"Orders for Acc {acc_id_int}")
                if UserDataType.POSITION_UPDATE in data_types: await self._invoke_subscription_command("SubscribePositions", [acc_id_int], f"Positions for Acc {acc_id_int}")
                if UserDataType.USER_TRADE in data_types: await self._invoke_subscription_command("SubscribeTrades", [acc_id_int], f"UserTrades for Acc {acc_id_int}")
            except ValueError:
                continue
    
    async def subscribe_global_accounts(self):
        async with self._subscription_lock:
            self.pending_global_subscription = True
        if self.current_status == StreamConnectionStatus.CONNECTED:
            await self._send_pending_subscriptions()
    
    async def subscribe_account(self, account_id_str: str, data_types: List[UserDataType]):
        async with self._subscription_lock:
            if account_id_str not in self.pending_account_subscriptions: self.pending_account_subscriptions[account_id_str] = set()
            self.pending_account_subscriptions[account_id_str].update(data_types)
        if self.current_status == StreamConnectionStatus.CONNECTED:
            await self._send_pending_subscriptions()
    
    async def unsubscribe_account(self, account_id_str: str, data_types: List[UserDataType]):
        async with self._subscription_lock:
            if account_id_str not in self.pending_account_subscriptions:
                logger.warning(f"Cannot unsubscribe from account {account_id_str}: not subscribed.")
                return

            try:
                acc_id_int = int(account_id_str)
            except ValueError:
                logger.error(f"Invalid account ID format for unsubscription: {account_id_str}")
                return
            
            types_to_remove = set()
            for data_type in data_types:
                command = None
                if data_type == UserDataType.ORDER_UPDATE:
                    command = "UnsubscribeOrders"
                elif data_type == UserDataType.POSITION_UPDATE:
                    command = "UnsubscribePositions"
                elif data_type == UserDataType.USER_TRADE:
                    command = "UnsubscribeTrades"
                
                if command:
                    if data_type in self.pending_account_subscriptions.get(account_id_str, set()):
                        log_msg = f"Unsubscribe {data_type.value} for Acc {acc_id_int}"
                        success = await self._invoke_subscription_command(command, [acc_id_int], log_msg)
                        if success:
                            types_to_remove.add(data_type)
                    else:
                        logger.debug(f"Skipping unsubscribe for {data_type.value} on account {acc_id_int}: not in pending subscriptions.")
            
            if types_to_remove:
                self.pending_account_subscriptions[account_id_str].difference_update(types_to_remove)
                logger.info(f"Updated pending subscriptions for account {account_id_str}: removed {types_to_remove}")

                if not self.pending_account_subscriptions[account_id_str]:
                    del self.pending_account_subscriptions[account_id_str]
                    logger.info(f"Removed account {account_id_str} from all specific subscriptions.")

    async def unsubscribe_global_accounts(self):
        async with self._subscription_lock:
            if not self.pending_global_subscription:
                logger.warning("Cannot unsubscribe from global accounts: not subscribed.")
                return
            
            success = await self._invoke_subscription_command("UnsubscribeAccounts", [], "Global Accounts Unsubscribe")
            if success:
                self.pending_global_subscription = False
                logger.info("Successfully unsubscribed from global accounts.")

    async def _handle_generic_user_event(self, args: List[Any], mapper_func_name: str):
        if self.mapper and len(args) >= 1 and isinstance(args[0], dict):
            mapper_func = getattr(self.mapper, mapper_func_name, None)
            if mapper_func:
                event = mapper_func(args[0], self.stream_name)
                if event: await self.event_callback(event)