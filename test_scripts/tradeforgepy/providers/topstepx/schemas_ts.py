# tradeforgepy/providers/topstepx/schemas_ts.py
"""
Pydantic models for TopStepX specific API request payloads and response structures.
These models are used internally by the TopStepX provider.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union, Literal
from datetime import datetime

# --- TopStepX Common Base Response ---
class TSBaseResponse(BaseModel):
    success: bool
    error_message: Optional[str] = Field(None, alias="errorMessage")
    error_code: Optional[Any] = Field(None, alias="errorCode") # API might send int or string

    class Config:
        populate_by_name = True

# --- TopStepX Authentication Models ---
class TSAuthLoginKeyRequest(BaseModel):
    user_name: str = Field(..., alias="userName")
    api_key: str = Field(..., alias="apiKey")

class TSAuthLoginAppRequest(BaseModel): # If you need app login later
    user_name: str = Field(..., alias="userName")
    password: str
    app_id: str = Field(..., alias="appId")
    verify_key: str = Field(..., alias="verifyKey")

class TSAuthResponse(TSBaseResponse): # Inherits success, errorMessage, errorCode
    token: Optional[str] = None

class TSAuthValidateResponse(TSBaseResponse):
    new_token: Optional[str] = Field(None, alias="newToken")

# --- TopStepX Account Models ---
class TSAccountSearchRequest(BaseModel):
    only_active_accounts: bool = Field(True, alias="onlyActiveAccounts")

class TSAccount(BaseModel):
    id: int
    name: Optional[str] = None
    balance: Optional[float] = None
    can_trade: Optional[bool] = Field(None, alias="canTrade")
    is_visible: Optional[bool] = Field(None, alias="isVisible")

    class Config:
        populate_by_name = True

class TSAccountSearchResponse(TSBaseResponse):
    accounts: List[TSAccount] = Field(default_factory=list)

# --- TopStepX Contract Models ---
class TSContractSearchRequest(BaseModel):
    search_text: str = Field(..., alias="searchText")
    live: bool = False

class TSContractSearchByIdRequest(BaseModel):
    contract_id: str = Field(..., alias="contractId")

class TSContract(BaseModel):
    id: str # This is the provider_contract_id, e.g., "CON.F.US.NQ.M25"
    name: Optional[str] = None # e.g., "NQM5"
    description: Optional[str] = None # e.g., "E-MINI NASDAQ 100 June 2025"
    tick_size: Optional[float] = Field(None, alias="tickSize")
    tick_value: Optional[float] = Field(None, alias="tickValue")
    currency: Optional[str] = None
    instrument_id: Optional[int] = Field(None, alias="instrumentId", description="Numeric ID, often used for history")

    class Config:
        populate_by_name = True

class TSContractSearchResponse(TSBaseResponse):
    contracts: List[TSContract] = Field(default_factory=list)

# --- TopStepX Historical Data Models ---
class TSHistoricalBarsRequest(BaseModel):
    account_id: Optional[int] = Field(None, alias="accountId") # Often optional for history
    contract_id: Union[str, int] = Field(..., alias="contractId") # TS accepts string or their numeric ID
    live: bool = False
    start_time: str = Field(..., alias="startTime") # ISO 8601 string
    end_time: str = Field(..., alias="endTime")   # ISO 8601 string
    unit: int # 1=Sec, 2=Min, 3=Hour, 4=Day (TopStepX specific codes)
    unit_number: int = Field(..., alias="unitNumber", gt=0)
    limit: int = Field(..., gt=0, le=1000) # TopStepX often has a limit like 1000
    include_partial_bar: bool = Field(False, alias="includePartialBar")

class TSBarData(BaseModel): # Matches TopStepX bar structure
    t: datetime # Timestamp of the bar start
    o: float    # Open
    h: float    # High
    l: float    # Low
    c: float    # Close
    v: float    # Volume

class TSHistoricalBarsResponse(TSBaseResponse):
    bars: List[TSBarData] = Field(default_factory=list)

# --- TopStepX Order Models ---
class TSOrderBase(BaseModel): # Common fields for placing orders
    account_id: int = Field(..., alias="accountId", gt=0)
    contract_id: str = Field(..., alias="contractId")
    type: int # 1=Limit, 2=Market, 3=Stop, 5=TrailingStop (TopStepX specific)
    side: int # 0=Buy (Bid), 1=Sell (Ask) (TopStepX specific)
    size: int = Field(..., gt=0)
    custom_tag: Optional[str] = Field(None, alias="customTag", max_length=50)
    linked_order_id: Optional[int] = Field(None, alias="linkedOrderld") # Note the 'ld' typo from API doc

    class Config:
        populate_by_name = True

class TSPlaceMarketOrderRequest(TSOrderBase):
    type: Literal[2] = Field(2) # Market order code

class TSPlaceLimitOrderRequest(TSOrderBase):
    type: Literal[1] = Field(1) # Limit order code
    limit_price: float = Field(..., alias="limitPrice", gt=0)

class TSPlaceStopOrderRequest(TSOrderBase): # Assuming Stop Market
    type: Literal[3] = Field(3) # Stop order code
    stop_price: float = Field(..., alias="stopPrice", gt=0)

class TSOrderPlacementResponse(TSBaseResponse):
    order_id: Optional[int] = Field(None, alias="orderId")

class TSCancelOrderRequest(BaseModel):
    account_id: int = Field(..., alias="accountId", gt=0)
    order_id: int = Field(..., alias="orderId", gt=0)

class TSCancelOrderResponse(TSBaseResponse):
    # Often just success/failure, but can add fields if API returns more
    pass

class TSModifyOrderRequest(BaseModel):
    account_id: int = Field(..., alias="accountId", gt=0)
    order_id: int = Field(..., alias="orderId", gt=0)
    size: Optional[int] = Field(None, gt=0)
    limit_price: Optional[float] = Field(None, alias="limitPrice", gt=0)
    stop_price: Optional[float] = Field(None, alias="stopPrice", gt=0)
    # trail_price: Optional[float] = Field(None, alias="trailPrice", gt=0) # If API supports modifying trail

    class Config:
        populate_by_name = True

class TSModifyOrderResponse(TSBaseResponse):
    pass

class TSOrderSearchRequest(BaseModel):
    account_id: int = Field(..., alias="accountId", gt=0)
    start_timestamp: str = Field(..., alias="startTimestamp") # ISO 8601
    end_timestamp: Optional[str] = Field(None, alias="endTimestamp") # ISO 8601

class TSOrderDetails(BaseModel): # Mirrors structure from TopStepX /api/Order/search response
    id: int
    account_id: int = Field(..., alias="accountId")
    contract_id: str = Field(..., alias="contractId")
    status: int # TopStepX specific status code
    type: int
    side: int
    size: int # Original order size
    cum_quantity: Optional[int] = Field(None, alias="cumQuantity") # Filled quantity
    leaves_quantity: Optional[int] = Field(None, alias="leavesQuantity") # Remaining quantity
    avg_px: Optional[float] = Field(None, alias="avgPx")
    limit_price: Optional[float] = Field(None, alias="limitPrice")
    stop_price: Optional[float] = Field(None, alias="stopPrice")
    # trail_price: Optional[float] = Field(None, alias="trailPrice")
    creation_timestamp: datetime = Field(..., alias="creationTimestamp")
    update_timestamp: Optional[datetime] = Field(None, alias="updateTimestamp")
    # text: Optional[str] = None # For rejection messages, etc.

    class Config:
        populate_by_name = True

class TSOrderSearchResponse(TSBaseResponse):
    orders: List[TSOrderDetails] = Field(default_factory=list)

# --- TopStepX Position Models ---
class TSCloseContractPositionRequest(BaseModel):
    account_id: int = Field(..., alias="accountId", gt=0)
    contract_id: str = Field(..., alias="contractId")

class TSPartialCloseContractPositionRequest(TSCloseContractPositionRequest):
    size: int = Field(..., gt=0, description="Number of lots to close")

class TSPositionManagementResponse(TSBaseResponse):
    message: Optional[str] = None # "Position closed successfully"

class TSSearchOpenPositionsRequest(BaseModel):
    account_id: int = Field(..., alias="accountId", gt=0)

class TSPosition(BaseModel): # Mirrors TopStepX /api/Position/searchOpen
    account_id: int = Field(..., alias="accountId")
    contract_id: str = Field(..., alias="contractId")
    size: int
    average_price: Optional[float] = Field(None, alias="averagePrice")
    unrealized_pnl: Optional[float] = Field(None, alias="unrealizedPnl")
    # Fields from API docs example (page 22) for searchOpen
    user: Optional[int] = None # User ID associated with the position.
    creation_timestamp: Optional[datetime] = Field(None, alias="creationTimestamp")
    type: Optional[int] = None # Type of position (e.g., 0 for Buy/Long, 1 for Sell/Short - API specific).

    class Config:
        populate_by_name = True

class TSSearchOpenPositionsResponse(TSBaseResponse):
    positions: List[TSPosition] = Field(default_factory=list)

# --- TopStepX Trade Models ---
class TSTradeSearchRequest(BaseModel):
    account_id: int = Field(..., alias="accountId", gt=0)
    start_timestamp: str = Field(..., alias="startTimestamp")
    end_timestamp: Optional[str] = Field(None, alias="endTimestamp")

class TSTrade(BaseModel): # Mirrors TopStepX /api/Trade/search
    id: int # Trade ID
    order_id: int = Field(..., alias="orderId") # Order ID that generated this trade
    account_id: int = Field(..., alias="accountId")
    contract_id: str = Field(..., alias="contractId")
    creation_timestamp: datetime = Field(..., alias="creationTimestamp")
    price: float
    size: int
    side: int # 0=Buy, 1=Sell
    profit_and_loss: Optional[float] = Field(None, alias="profitAndLoss")
    fees: Optional[float] = None
    voided: Optional[bool] = None

    class Config:
        populate_by_name = True

class TSTradeSearchResponse(TSBaseResponse):
    trades: List[TSTrade] = Field(default_factory=list)