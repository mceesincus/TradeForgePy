# tradeforgepy/providers/topstepx/schemas_ts.py
# Refined based on openapi.json and datamodel-code-generator output
# Manually mapped x-enumNames to Enum members for better readability.

from __future__ import annotations # For Pydantic v1 compatibility if needed, good practice

from datetime import datetime
from decimal import Decimal # Generated models used Decimal, which is good for currency
from enum import IntEnum # Using IntEnum for integer-based enums from spec
from typing import List, Optional, Any # Removed Union, Literal as enums cover these

from pydantic import BaseModel, Field, ConfigDict

# --- Common Pydantic Model Configuration ---
MODEL_CONFIG_TS = ConfigDict(
    populate_by_name=True, # Allows using Pythonic names if aliases are set for API names
    extra='ignore',        # Ignore extra fields from API not defined in model
    arbitrary_types_allowed=True
)

# --- TopStepX Base Response (matches the structure in your openapi.json) ---
# The generated output had individual success/errorCode/errorMessage in each response.
# It's cleaner to have a base class if the structure is consistent.
# However, the generated output already did this by making specific ErrorCode enums
# and including success/errorCode/errorMessage in each response model. We'll stick to that
# generated pattern for now to minimize divergence from what the tool produced,
# but a common base could be considered for further refactoring if desired.


# --- Enumerations from OpenAPI Spec ---

class SearchAccountErrorCode(IntEnum):
    SUCCESS = 0

class LoginErrorCode(IntEnum):
    SUCCESS = 0
    USER_NOT_FOUND = 1
    PASSWORD_VERIFICATION_FAILED = 2
    INVALID_CREDENTIALS = 3
    APP_NOT_FOUND = 4
    APP_VERIFICATION_FAILED = 5
    INVALID_DEVICE = 6
    AGREEMENTS_NOT_SIGNED = 7
    UNKNOWN_ERROR = 8
    API_SUBSCRIPTION_NOT_FOUND = 9

class LogoutErrorCode(IntEnum):
    SUCCESS = 0
    INVALID_SESSION = 1
    UNKNOWN_ERROR = 2

class ValidateErrorCode(IntEnum):
    SUCCESS = 0
    INVALID_SESSION = 1
    SESSION_NOT_FOUND = 2
    EXPIRED_TOKEN = 3
    UNKNOWN_ERROR = 4

class SearchContractErrorCode(IntEnum):
    SUCCESS = 0

class SearchContractByIdErrorCode(IntEnum):
    SUCCESS = 0
    CONTRACT_NOT_FOUND = 1

class RetrieveBarErrorCode(IntEnum):
    SUCCESS = 0
    CONTRACT_NOT_FOUND = 1

class AggregateBarUnit(IntEnum):
    UNSPECIFIED = 0
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    DAY = 4
    WEEK = 5
    MONTH = 6

class SearchOrderErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1

class OrderStatusTS(IntEnum): # Renamed to OrderStatusTS to avoid conflict with generic
    NONE = 0      # Note: OpenAPI spec used "None", Python uses "NONE" for keywords
    OPEN = 1      # "Open" in spec often means Working/New for other APIs
    FILLED = 2
    CANCELLED = 3
    EXPIRED = 4
    REJECTED = 5
    PENDING = 6   # "Pending" can mean different things (Pending New, Pending Cancel)

class OrderTypeTS(IntEnum): # Renamed
    UNKNOWN = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3 # Note: OCR doc page 5 had 3=Stop. Swagger says 3=StopLimit. Trust Swagger.
    STOP = 4       # Swagger has 4=Stop (likely Stop Market).
    TRAILING_STOP = 5
    JOIN_BID = 6
    JOIN_ASK = 7

class OrderSideTS(IntEnum): # Renamed
    BID = 0 # Buy
    ASK = 1 # Sell

class PlaceOrderErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1
    ORDER_REJECTED = 2
    INSUFFICIENT_FUNDS = 3
    ACCOUNT_VIOLATION = 4
    OUTSIDE_TRADING_HOURS = 5
    ORDER_PENDING = 6
    UNKNOWN_ERROR = 7
    CONTRACT_NOT_FOUND = 8
    CONTRACT_NOT_ACTIVE = 9
    ACCOUNT_REJECTED = 10

class CancelOrderErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1
    ORDER_NOT_FOUND = 2
    REJECTED = 3
    PENDING = 4
    UNKNOWN_ERROR = 5
    ACCOUNT_REJECTED = 6

class ModifyOrderErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1
    ORDER_NOT_FOUND = 2
    REJECTED = 3
    PENDING = 4
    UNKNOWN_ERROR = 5
    ACCOUNT_REJECTED = 6
    CONTRACT_NOT_FOUND = 7 # Added based on spec

class SearchPositionErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1

class PositionTypeTS(IntEnum): # Renamed
    UNDEFINED = 0
    LONG = 1
    SHORT = 2

class ClosePositionErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1
    POSITION_NOT_FOUND = 2
    CONTRACT_NOT_FOUND = 3
    CONTRACT_NOT_ACTIVE = 4
    ORDER_REJECTED = 5
    ORDER_PENDING = 6
    UNKNOWN_ERROR = 7
    ACCOUNT_REJECTED = 8

class PartialClosePositionErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1
    POSITION_NOT_FOUND = 2
    CONTRACT_NOT_FOUND = 3
    CONTRACT_NOT_ACTIVE = 4
    INVALID_CLOSE_SIZE = 5
    ORDER_REJECTED = 6
    ORDER_PENDING = 7
    UNKNOWN_ERROR = 8
    ACCOUNT_REJECTED = 9

class SearchTradeErrorCode(IntEnum):
    SUCCESS = 0
    ACCOUNT_NOT_FOUND = 1


# --- Model Definitions from OpenAPI Spec ---

class TSTradingAccountModel(BaseModel): # Renamed to avoid conflict if generic is imported
    id: int
    name: str
    balance: Decimal
    canTrade: bool
    isVisible: bool
    simulated: bool
    model_config = MODEL_CONFIG_TS

class TSContractModel(BaseModel): # Renamed
    id: str
    name: str
    description: str
    tickSize: Decimal
    tickValue: Decimal
    activeContract: bool
    model_config = MODEL_CONFIG_TS

class TSAggregateBarModel(BaseModel): # Renamed
    t: datetime
    o: Decimal
    h: Decimal
    l: Decimal
    c: Decimal
    v: int # format "int64" in spec, Python int handles large integers
    model_config = MODEL_CONFIG_TS

class TSOrderModel(BaseModel): # Renamed
    id: int
    accountId: int
    contractId: str
    creationTimestamp: datetime
    updateTimestamp: Optional[datetime] = None
    status: OrderStatusTS # Use our renamed Enum
    type: OrderTypeTS     # Use our renamed Enum
    side: OrderSideTS     # Use our renamed Enum
    size: int
    limitPrice: Optional[Decimal] = None
    stopPrice: Optional[Decimal] = None
    fillVolume: int # This is likely cumQuantity / filled size
    model_config = MODEL_CONFIG_TS

class TSPositionModel(BaseModel): # Renamed
    id: int # Position ID, distinct from account/contract
    accountId: int
    contractId: str
    creationTimestamp: datetime
    type: PositionTypeTS # Use our renamed Enum
    size: int
    averagePrice: Decimal # Spec says required, generator might make optional if not in example
    model_config = MODEL_CONFIG_TS

class TSHalfTradeModel(BaseModel): # Renamed
    id: int
    accountId: int
    contractId: str
    creationTimestamp: datetime
    price: Decimal
    profitAndLoss: Optional[Decimal] = None
    fees: Decimal
    side: OrderSideTS # Use our renamed Enum
    size: int
    voided: bool
    orderId: int
    model_config = MODEL_CONFIG_TS

# --- Request Models ---

class TSSearchAccountRequest(BaseModel): # Renamed
    onlyActiveAccounts: bool
    model_config = MODEL_CONFIG_TS

class TSLoginAppRequest(BaseModel): # Renamed
    userName: str
    password: str
    deviceId: str # Not in our OCR, but in Swagger
    appId: str
    verifyKey: str
    model_config = MODEL_CONFIG_TS

class TSLoginApiKeyRequest(BaseModel): # Renamed
    userName: str
    apiKey: str
    model_config = MODEL_CONFIG_TS

class TSSearchContractRequest(BaseModel): # Renamed
    searchText: Optional[str] = None # Swagger shows not required, OCR had it required
    live: bool
    model_config = MODEL_CONFIG_TS

class TSSearchContractByIdRequest(BaseModel): # Renamed
    contractId: str
    model_config = MODEL_CONFIG_TS

class TSRetrieveBarRequest(BaseModel): # Renamed
    # accountId: Optional[int] = None # Added based on OCR page 8, though not in Swagger for this specific request
    contractId: str # Swagger implies string here, though OCR page 8 implies int/string
    live: bool
    startTime: datetime
    endTime: datetime
    unit: AggregateBarUnit # Use our Enum
    unitNumber: int
    limit: int
    includePartialBar: bool
    model_config = MODEL_CONFIG_TS

class TSSearchOrderRequest(BaseModel): # Renamed
    accountId: int
    startTimestamp: datetime
    endTimestamp: Optional[datetime] = None
    model_config = MODEL_CONFIG_TS

class TSSearchOpenOrderRequest(BaseModel): # Renamed
    accountId: int
    model_config = MODEL_CONFIG_TS

class TSPlaceOrderRequest(BaseModel): # Renamed
    accountId: int
    contractId: str
    type: OrderTypeTS # Use our Enum
    side: OrderSideTS # Use our Enum
    size: int
    limitPrice: Optional[Decimal] = None
    stopPrice: Optional[Decimal] = None
    trailPrice: Optional[Decimal] = None # From Swagger
    customTag: Optional[str] = None
    linkedOrderId: Optional[int] = None # Swagger uses linkedOrderId
    model_config = MODEL_CONFIG_TS

class TSCancelOrderRequest(BaseModel): # Renamed
    accountId: int
    orderId: int
    model_config = MODEL_CONFIG_TS

class TSModifyOrderRequest(BaseModel): # Renamed
    accountId: int
    orderId: int
    size: Optional[int] = None
    limitPrice: Optional[Decimal] = None
    stopPrice: Optional[Decimal] = None
    trailPrice: Optional[Decimal] = None # From Swagger
    model_config = MODEL_CONFIG_TS

class TSSearchPositionRequest(BaseModel): # Renamed
    accountId: int
    model_config = MODEL_CONFIG_TS

class TSCloseContractPositionRequest(BaseModel): # Renamed
    accountId: int
    contractId: str
    model_config = MODEL_CONFIG_TS

class TSPartialCloseContractPositionRequest(BaseModel): # Renamed
    accountId: int
    contractId: str
    size: int
    model_config = MODEL_CONFIG_TS

class TSSearchTradeRequest(BaseModel): # Renamed
    accountId: int
    startTimestamp: Optional[datetime] = None # Swagger shows optional
    endTimestamp: Optional[datetime] = None   # Swagger shows optional
    model_config = MODEL_CONFIG_TS


# --- Response Models ---

class TSSearchAccountResponse(BaseModel): # Renamed
    success: bool
    errorCode: SearchAccountErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    accounts: Optional[List[TSTradingAccountModel]] = Field(default_factory=list) # Default to empty list
    model_config = MODEL_CONFIG_TS

class TSLoginResponse(BaseModel): # Renamed
    success: bool
    errorCode: LoginErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    token: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSLogoutResponse(BaseModel): # Renamed
    success: bool
    errorCode: LogoutErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSValidateResponse(BaseModel): # Renamed
    success: bool
    errorCode: ValidateErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    newToken: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSSearchContractResponse(BaseModel): # Renamed
    success: bool
    errorCode: SearchContractErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    contracts: Optional[List[TSContractModel]] = Field(default_factory=list)
    model_config = MODEL_CONFIG_TS

class TSSearchContractByIdResponse(BaseModel): # Renamed
    success: bool
    errorCode: SearchContractByIdErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    contract: Optional[TSContractModel] = None # Can be null if not found
    model_config = MODEL_CONFIG_TS

class TSRetrieveBarResponse(BaseModel): # Renamed
    success: bool
    errorCode: RetrieveBarErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    bars: Optional[List[TSAggregateBarModel]] = Field(default_factory=list)
    model_config = MODEL_CONFIG_TS

class TSSearchOrderResponse(BaseModel): # Renamed
    success: bool
    errorCode: SearchOrderErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    orders: Optional[List[TSOrderModel]] = Field(default_factory=list)
    model_config = MODEL_CONFIG_TS

class TSPlaceOrderResponse(BaseModel): # Renamed
    success: bool
    errorCode: PlaceOrderErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    orderId: Optional[int] = None
    model_config = MODEL_CONFIG_TS

class TSCancelOrderResponse(BaseModel): # Renamed
    success: bool
    errorCode: CancelOrderErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSModifyOrderResponse(BaseModel): # Renamed
    success: bool
    errorCode: ModifyOrderErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSSearchPositionResponse(BaseModel): # Renamed
    success: bool
    errorCode: SearchPositionErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    positions: Optional[List[TSPositionModel]] = Field(default_factory=list)
    model_config = MODEL_CONFIG_TS

class TSClosePositionResponse(BaseModel): # Renamed
    success: bool
    errorCode: ClosePositionErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSPartialClosePositionResponse(BaseModel): # Renamed
    success: bool
    errorCode: PartialClosePositionErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    model_config = MODEL_CONFIG_TS

class TSSearchHalfTradeResponse(BaseModel): # Renamed
    success: bool
    errorCode: SearchTradeErrorCode # Use our Enum
    errorMessage: Optional[str] = None
    trades: Optional[List[TSHalfTradeModel]] = Field(default_factory=list)
    model_config = MODEL_CONFIG_TS