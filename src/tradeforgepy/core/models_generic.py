# ==============================================================================
# tradeforgepy/tradeforgepy/core/models_generic.py
# ==============================================================================
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union, Literal as typing_Literal # Renamed Literal to avoid conflict
from datetime import datetime
from .enums import (
    AssetClass, OrderSide, OrderType, OrderTimeInForce, OrderStatus,
    BarTimeframeUnit, MarketDataType, UserDataType
)
from tradeforgepy.utils.time_utils import ensure_utc

class GenericBaseModel(BaseModel):
    provider_name: Optional[str] = Field(None, description="Name of the trading platform provider")
    provider_specific_data: Optional[Dict[str, Any]] = Field(
        None, description="Raw or additional data specific to the provider"
    )
    model_config = ConfigDict( # Pydantic v2 style config
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True
    )

class Account(GenericBaseModel):
    provider_account_id: str = Field(..., description="Provider's unique identifier for this account")
    account_name: Optional[str] = Field(None, description="User-friendly name for the account")
    balance: Optional[float] = Field(None, description="Total account balance")
    currency: Optional[str] = Field(None, description="Base currency of the account (e.g., USD)")
    buying_power: Optional[float] = Field(None, description="Available buying power")
    cash_balance: Optional[float] = Field(None, description="Cash component of the balance")
    margin_balance: Optional[float] = Field(None, description="Margin component of the balance, if applicable")
    can_trade: Optional[bool] = Field(None, description="Indicates if trading is enabled for this account")
    is_active: Optional[bool] = Field(None, description="Indicates if the account is generally active/enabled")

class Contract(GenericBaseModel):
    provider_contract_id: str = Field(..., description="Provider's unique identifier for this contract")
    symbol: str = Field(..., description="Common trading symbol (e.g., NQZ3, BTC/USD)")
    exchange: Optional[str] = Field(None, description="Exchange where the contract is traded (e.g., CME, NASDAQ)")
    asset_class: Optional[AssetClass] = Field(None, description="Asset class of the contract")
    description: Optional[str] = Field(None, description="Full description of the contract")
    tick_size: Optional[float] = Field(None, description="Minimum price increment")
    tick_value: Optional[float] = Field(None, description="Monetary value of one tick_size movement")
    price_currency: Optional[str] = Field(None, description="Currency in which the contract is priced")
    multiplier: Optional[float] = Field(1.0, description="Contract multiplier (e.g., for futures)")
    min_order_size: Optional[float] = Field(None, description="Minimum orderable quantity")
    max_order_size: Optional[float] = Field(None, description="Maximum orderable quantity")
    is_tradable: Optional[bool] = Field(None, description="Indicates if the contract is currently tradable")
    expiration_date_utc: Optional[datetime] = Field(None, description="Expiration date for derivatives (UTC)")
    underlying_symbol: Optional[str] = Field(None, description="Symbol of the underlying asset, if applicable")

    _ensure_expiration_utc = field_validator('expiration_date_utc', mode='before')(ensure_utc)

class BarData(GenericBaseModel):
    timestamp_utc: datetime = Field(..., description="Start timestamp of the bar (UTC)")
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = Field(None, description="Trading volume during the bar")

    _ensure_timestamp_utc = field_validator('timestamp_utc', mode='before')(ensure_utc)

class HistoricalBarsRequest(BaseModel):
    provider_contract_id: str
    timeframe_unit: BarTimeframeUnit
    timeframe_value: int = Field(..., gt=0)
    start_time_utc: datetime
    end_time_utc: datetime

    _ensure_datetimes_utc = field_validator('start_time_utc', 'end_time_utc', mode='before')(ensure_utc)

class HistoricalBarsResponse(GenericBaseModel):
    request: Optional[HistoricalBarsRequest] = Field(None, description="The request that generated this response")
    bars: List[BarData] = Field(default_factory=list)

class Order(GenericBaseModel):
    provider_order_id: str = Field(..., description="Provider's unique identifier for the order")
    provider_account_id: str = Field(..., description="Account ID associated with this order")
    provider_contract_id: str = Field(..., description="Contract ID this order is for")
    client_order_id: Optional[str] = Field(None, description="Optional client-generated order identifier")
    order_type: OrderType
    order_side: OrderSide
    original_size: float = Field(..., gt=0, description="Initial requested size of the order")
    status: OrderStatus
    limit_price: Optional[float] = Field(None, description="Limit price for LIMIT or STOP_LIMIT orders")
    stop_price: Optional[float] = Field(None, description="Stop price for STOP_MARKET or STOP_LIMIT orders")
    filled_size: float = Field(0.0, description="Quantity of the order that has been filled")
    average_fill_price: Optional[float] = Field(None, description="Average price at which the order was filled")
    time_in_force: Optional[OrderTimeInForce] = Field(None)
    created_at_utc: datetime = Field(..., description="Timestamp when the order was created/submitted (UTC)")
    updated_at_utc: Optional[datetime] = Field(None, description="Timestamp of the last update to the order (UTC)")
    commission: Optional[float] = Field(None)
    reason_text: Optional[str] = Field(None, description="Text reason for rejection, cancellation, etc.")

    _ensure_order_datetimes_utc = field_validator('created_at_utc', 'updated_at_utc', mode='before')(ensure_utc)


class PlaceOrderRequest(BaseModel): # This is a request model, not generic data
    provider_account_id: str
    provider_contract_id: str
    order_type: OrderType
    order_side: OrderSide
    size: float = Field(..., gt=0)
    limit_price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    time_in_force: OrderTimeInForce = OrderTimeInForce.DAY
    client_order_id: Optional[str] = None

class OrderPlacementResponse(GenericBaseModel):
    order_id_acknowledged: bool
    provider_order_id: Optional[str] = None
    initial_order_status: Optional[OrderStatus] = Field(None, alias="order_status") # For initial status if known
    message: Optional[str] = None

class ModifyOrderRequest(BaseModel):
    provider_account_id: str
    provider_order_id: str
    new_size: Optional[float] = Field(None, gt=0)
    new_limit_price: Optional[float] = Field(None, gt=0)
    new_stop_price: Optional[float] = Field(None, gt=0)
    # client_order_id: Optional[str] = None # If provider supports modifying this

class GenericModificationResponse(GenericBaseModel):
    success: bool
    provider_order_id: Optional[str] = None # Usually the same, but some might assign new
    message: Optional[str] = None

class GenericCancellationResponse(GenericBaseModel):
    success: bool
    message: Optional[str] = None

class Position(GenericBaseModel):
    provider_account_id: str
    provider_contract_id: str
    quantity: float # Positive for long, negative for short
    average_entry_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    # last_trade_price: Optional[float] = None
    # market_value: Optional[float] = None

class Trade(GenericBaseModel):
    provider_trade_id: str # Provider's unique ID for this specific fill/execution
    provider_order_id: Optional[str] = None # Order that generated this trade
    provider_account_id: str
    provider_contract_id: str
    price: float
    quantity: float # Always positive quantity for this specific fill
    side: OrderSide # Side of THIS specific trade execution
    timestamp_utc: datetime
    commission: Optional[float] = None
    # liquidity_indicator: Optional[str] = None # e.g., MAKER, TAKER
    pnl: Optional[float] = None # P&L realized by this specific trade if it closed/reduced a position

    _ensure_trade_dt_utc = field_validator('timestamp_utc', mode='before')(ensure_utc)

# --- Stream Event Models ---
class GenericStreamEvent(GenericBaseModel):
    event_type: Union[MarketDataType, UserDataType]
    timestamp_event_utc: datetime = Field(..., alias="timestamp_utc", description="Timestamp of the event occurrence (UTC)")
    provider_contract_id: Optional[str] = None
    provider_account_id: Optional[str] = None

    _ensure_event_dt_utc = field_validator('timestamp_event_utc', mode='before')(ensure_utc)

class QuoteEvent(GenericStreamEvent):
    event_type: typing_Literal[MarketDataType.QUOTE] = MarketDataType.QUOTE # Use the renamed Literal
    bid_price: Optional[float] = None
    bid_size: Optional[float] = None
    ask_price: Optional[float] = None
    ask_size: Optional[float] = None
    last_price: Optional[float] = None # Some providers include last trade in quote
    last_size: Optional[float] = None

class MarketTradeEvent(GenericStreamEvent): # Different from UserTrade event
    event_type: typing_Literal[MarketDataType.TRADE] = MarketDataType.TRADE
    price: float
    size: float
    aggressor_side: Optional[OrderSide] = None

class DepthLevel(BaseModel): # Not GenericBaseModel as it's a sub-component
    price: float
    size: float
    side: OrderSide # Is this level a bid or an ask

class DepthSnapshotEvent(GenericStreamEvent):
    event_type: typing_Literal[MarketDataType.DEPTH] = MarketDataType.DEPTH
    bids: List[DepthLevel] = Field(default_factory=list)
    asks: List[DepthLevel] = Field(default_factory=list)
    is_snapshot: bool = True # To differentiate from incremental updates if supported

class OrderUpdateEvent(GenericStreamEvent):
    event_type: typing_Literal[UserDataType.ORDER_UPDATE] = UserDataType.ORDER_UPDATE
    order_data: Order # The full generic Order model

class PositionUpdateEvent(GenericStreamEvent):
    event_type: typing_Literal[UserDataType.POSITION_UPDATE] = UserDataType.POSITION_UPDATE
    position_data: Position # The full generic Position model

class UserTradeEvent(GenericStreamEvent): # Fill for user
    event_type: typing_Literal[UserDataType.USER_TRADE] = UserDataType.USER_TRADE
    trade_data: Trade # The full generic Trade model

class AccountUpdateEvent(GenericStreamEvent):
    event_type: typing_Literal[UserDataType.ACCOUNT_UPDATE] = UserDataType.ACCOUNT_UPDATE
    account_data: Account # The full generic Account model