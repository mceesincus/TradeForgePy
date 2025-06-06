# ==============================================================================
# tradeforgepy/tradeforgepy/core/interfaces.py
# ==============================================================================
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Any, Coroutine, Union, Dict
from datetime import datetime
from .models_generic import (
    Account, Contract, BarData, HistoricalBarsRequest, HistoricalBarsResponse,
    Order, PlaceOrderRequest, OrderPlacementResponse,
    ModifyOrderRequest, GenericModificationResponse, GenericCancellationResponse,
    Position, Trade, GenericStreamEvent
)
from .enums import AssetClass, StreamConnectionStatus, MarketDataType, UserDataType

# Callback type that receives generic stream events
GenericStreamEventCallback = Callable[[GenericStreamEvent], Coroutine[Any, Any, None]]
# Callback for status changes
StreamStatusCallback = Callable[[StreamConnectionStatus, Optional[str]], Coroutine[Any, Any, None]]
# Callback for errors
StreamErrorCallback = Callable[[Exception], Coroutine[Any, Any, None]]


class TradingPlatformAPI(ABC):
    provider_name: str

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def get_accounts(self) -> List[Account]:
        pass

    @abstractmethod
    async def search_contracts(self, search_text: str, asset_class: Optional[AssetClass] = None) -> List[Contract]:
        pass
    
    @abstractmethod
    async def get_contract_details(self, provider_contract_id: str) -> Optional[Contract]:
        pass

    @abstractmethod
    async def get_historical_bars(self, request: HistoricalBarsRequest) -> HistoricalBarsResponse:
        pass

    @abstractmethod
    async def place_order(self, order_request: PlaceOrderRequest) -> OrderPlacementResponse:
        pass
    
    @abstractmethod
    async def cancel_order(self, provider_account_id: str, provider_order_id: str) -> GenericCancellationResponse:
        pass

    @abstractmethod
    async def modify_order(self, modify_request: ModifyOrderRequest) -> GenericModificationResponse:
        pass # modify_request itself is a generic Pydantic model now

    @abstractmethod
    async def get_order_by_id(self, provider_account_id: str, provider_order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    async def get_open_orders(self, provider_account_id: str, provider_contract_id: Optional[str] = None) -> List[Order]:
        pass

    @abstractmethod
    async def get_positions(self, provider_account_id: str) -> List[Position]:
        pass

    @abstractmethod
    async def close_position(self,
                             provider_account_id: str,
                             provider_contract_id: str,
                             size_to_close: Optional[float] = None
                            ) -> OrderPlacementResponse: # Closing results in an order
        pass

    @abstractmethod
    async def get_trade_history(self,
                                provider_account_id: str,
                                provider_contract_id: Optional[str] = None,
                                start_time_utc: Optional[datetime] = None,
                                end_time_utc: Optional[datetime] = None,
                                limit: Optional[int] = None
                               ) -> List[Trade]:
        pass

class RealTimeStream(ABC):
    provider_name: str

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def subscribe_market_data(self, provider_contract_ids: List[str],
                                    data_types: List[MarketDataType]) -> None:
        pass

    @abstractmethod
    async def unsubscribe_market_data(self, provider_contract_ids: List[str],
                                      data_types: List[MarketDataType]) -> None:
        pass

    @abstractmethod
    async def subscribe_user_data(self, provider_account_ids: List[str],
                                  data_types: List[UserDataType]) -> None:
        pass

    @abstractmethod
    async def unsubscribe_user_data(self, provider_account_ids: List[str],
                                    data_types: List[UserDataType]) -> None:
        pass

    @abstractmethod
    def get_status(self) -> StreamConnectionStatus:
        """Gets the overall, combined status of all underlying streams."""
        pass

    @abstractmethod
    def get_market_stream_status(self) -> StreamConnectionStatus:
        """Gets the specific status of the market data stream."""
        pass

    @abstractmethod
    def get_user_stream_status(self) -> StreamConnectionStatus:
        """Gets the specific status of the user data (private) stream."""
        pass
    
    @abstractmethod
    def get_stream_statuses(self) -> Dict[str, StreamConnectionStatus]:
        """Gets a dictionary of all individual stream statuses."""
        pass

    @abstractmethod
    def on_event(self, callback: GenericStreamEventCallback) -> None:
        """Registers ONE primary callback to receive all subscribed generic stream events."""
        pass
    
    @abstractmethod
    def on_status_change(self, callback: StreamStatusCallback) -> None:
        pass

    @abstractmethod
    def on_error(self, callback: StreamErrorCallback) -> None:
        pass

    @abstractmethod
    async def run_forever(self) -> None:
        """Keeps the stream connection alive and processes incoming messages."""
        pass