# tradeforgepy/providers/topstepx/schemas_ts.py
# REFINED and CORRECTED version

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

# Updated model config to automatically handle datetime and Decimal -> str/float conversion for JSON
MODEL_CONFIG_TS = ConfigDict(
    populate_by_name=True,
    extra='ignore',
    arbitrary_types_allowed=True,
    json_encoders={
        datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        Decimal: lambda v: float(v) # Convert Decimals to float for JSON
    }
)

# --- Enumerations from OpenAPI Spec (with corrections) ---
class TSSearchAccountErrorCode(IntEnum): SUCCESS = 0
class TSLoginErrorCode(IntEnum):
    SUCCESS = 0; USER_NOT_FOUND = 1; PASSWORD_VERIFICATION_FAILED = 2; INVALID_CREDENTIALS = 3
    APP_NOT_FOUND = 4; APP_VERIFICATION_FAILED = 5; INVALID_DEVICE = 6; AGREEMENTS_NOT_SIGNED = 7
    UNKNOWN_ERROR = 8; API_SUBSCRIPTION_NOT_FOUND = 9; ACCOUNT_REJECTED = 10
class TSLogoutErrorCode(IntEnum): SUCCESS = 0; INVALID_SESSION = 1; UNKNOWN_ERROR = 2
class TSValidateErrorCode(IntEnum): SUCCESS = 0; INVALID_SESSION = 1; SESSION_NOT_FOUND = 2; EXPIRED_TOKEN = 3; UNKNOWN_ERROR = 4
class TSSearchContractErrorCode(IntEnum): SUCCESS = 0
class TSSearchContractByIdErrorCode(IntEnum): SUCCESS = 0; CONTRACT_NOT_FOUND = 1
class TSRetrieveBarErrorCode(IntEnum): SUCCESS = 0; CONTRACT_NOT_FOUND = 1
class TSAggregateBarUnit(IntEnum): UNSPECIFIED = 0; SECOND = 1; MINUTE = 2; HOUR = 3; DAY = 4; WEEK = 5; MONTH = 6
class TSSearchOrderErrorCode(IntEnum): SUCCESS = 0; ACCOUNT_NOT_FOUND = 1
class TSOrderStatus(IntEnum): NONE = 0; OPEN = 1; FILLED = 2; CANCELLED = 3; EXPIRED = 4; REJECTED = 5; PENDING = 6
class TSTraderOrderType(IntEnum): UNKNOWN = 0; LIMIT = 1; MARKET = 2; STOP_LIMIT = 3; STOP = 4; TRAILING_STOP = 5; JOIN_BID = 6; JOIN_ASK = 7
class TSOrderSide(IntEnum): BID = 0; ASK = 1
class TSPlaceOrderErrorCode(IntEnum):
    SUCCESS = 0; ACCOUNT_NOT_FOUND = 1; ORDER_REJECTED = 2; INSUFFICIENT_FUNDS = 3; ACCOUNT_VIOLATION = 4
    OUTSIDE_TRADING_HOURS = 5; ORDER_PENDING = 6; UNKNOWN_ERROR = 7; CONTRACT_NOT_FOUND = 8
    CONTRACT_NOT_ACTIVE = 9; ACCOUNT_REJECTED = 10
class TSCancelOrderErrorCode(IntEnum): SUCCESS = 0; ACCOUNT_NOT_FOUND = 1; ORDER_NOT_FOUND = 2; REJECTED = 3; PENDING = 4; UNKNOWN_ERROR = 5; ACCOUNT_REJECTED = 6
class TSModifyOrderErrorCode(IntEnum): SUCCESS = 0; ACCOUNT_NOT_FOUND = 1; ORDER_NOT_FOUND = 2; REJECTED = 3; PENDING = 4; UNKNOWN_ERROR = 5; ACCOUNT_REJECTED = 6; CONTRACT_NOT_FOUND = 7
class TSSearchPositionErrorCode(IntEnum): SUCCESS = 0; ACCOUNT_NOT_FOUND = 1
class TSPositionType(IntEnum): UNDEFINED = 0; LONG = 1; SHORT = 2
class TSClosePositionErrorCode(IntEnum):
    SUCCESS = 0; ACCOUNT_NOT_FOUND = 1; POSITION_NOT_FOUND = 2; CONTRACT_NOT_FOUND = 3; CONTRACT_NOT_ACTIVE = 4
    ORDER_REJECTED = 5; ORDER_PENDING = 6; UNKNOWN_ERROR = 7; ACCOUNT_REJECTED = 8
class TSPartialClosePositionErrorCode(IntEnum):
    SUCCESS = 0; ACCOUNT_NOT_FOUND = 1; POSITION_NOT_FOUND = 2; CONTRACT_NOT_FOUND = 3; CONTRACT_NOT_ACTIVE = 4
    INVALID_CLOSE_SIZE = 5; ORDER_REJECTED = 6; ORDER_PENDING = 7; UNKNOWN_ERROR = 8; ACCOUNT_REJECTED = 9
class TSSearchTradeErrorCode(IntEnum): SUCCESS = 0; ACCOUNT_NOT_FOUND = 1

# --- Model Definitions ---
class TSTradingAccountModel(BaseModel): model_config = MODEL_CONFIG_TS; id: int; name: str; balance: Decimal; canTrade: bool; isVisible: bool; simulated: bool
class TSContractModel(BaseModel): model_config = MODEL_CONFIG_TS; id: str; name: str; description: str; tickSize: Decimal; tickValue: Decimal; activeContract: bool
class TSAggregateBarModel(BaseModel): model_config = MODEL_CONFIG_TS; t: datetime; o: Decimal; h: Decimal; l: Decimal; c: Decimal; v: int
class TSOrderModel(BaseModel): model_config = MODEL_CONFIG_TS; id: int; accountId: int; contractId: str; creationTimestamp: datetime; updateTimestamp: Optional[datetime] = None; status: TSOrderStatus; type: TSTraderOrderType; side: TSOrderSide; size: int; limitPrice: Optional[Decimal] = None; stopPrice: Optional[Decimal] = None; fillVolume: int
class TSPositionModel(BaseModel): model_config = MODEL_CONFIG_TS; id: int; accountId: int; contractId: str; creationTimestamp: datetime; type: TSPositionType; size: int; averagePrice: Decimal
class TSHalfTradeModel(BaseModel): model_config = MODEL_CONFIG_TS; id: int; accountId: int; contractId: str; creationTimestamp: datetime; price: Decimal; profitAndLoss: Optional[Decimal] = None; fees: Decimal; side: TSOrderSide; size: int; voided: bool; orderId: int
class TSSearchAccountRequest(BaseModel): model_config = MODEL_CONFIG_TS; onlyActiveAccounts: bool
class TSLoginApiKeyRequest(BaseModel): model_config = MODEL_CONFIG_TS; userName: str; apiKey: str
class TSSearchContractRequest(BaseModel): model_config = MODEL_CONFIG_TS; searchText: Optional[str] = None; live: bool
class TSSearchContractByIdRequest(BaseModel): model_config = MODEL_CONFIG_TS; contractId: str
class TSRetrieveBarRequest(BaseModel): model_config = MODEL_CONFIG_TS; contractId: str; live: bool; startTime: str; endTime: str; unit: TSAggregateBarUnit; unitNumber: int; limit: int; includePartialBar: bool
class TSSearchOrderRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; startTimestamp: str; endTimestamp: Optional[str] = None
class TSSearchTradeRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; startTimestamp: Optional[str] = None; endTimestamp: Optional[str] = None
class TSSearchOpenOrderRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int
class TSPlaceOrderRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; contractId: str; type: TSTraderOrderType; side: TSOrderSide; size: int; limitPrice: Optional[Decimal] = None; stopPrice: Optional[Decimal] = None; trailPrice: Optional[Decimal] = None; customTag: Optional[str] = None; linkedOrderId: Optional[int] = None
class TSCancelOrderRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; orderId: int
class TSModifyOrderRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; orderId: int; size: Optional[int] = None; limitPrice: Optional[Decimal] = None; stopPrice: Optional[Decimal] = None; trailPrice: Optional[Decimal] = None
class TSSearchPositionRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int
class TSCloseContractPositionRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; contractId: str
class TSPartialCloseContractPositionRequest(BaseModel): model_config = MODEL_CONFIG_TS; accountId: int; contractId: str; size: int

# --- Response Models ---
class TSSearchAccountResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSSearchAccountErrorCode; errorMessage: Optional[str] = None; accounts: List[TSTradingAccountModel] = Field(default_factory=list)
class TSLoginResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSLoginErrorCode; errorMessage: Optional[str] = None; token: Optional[str] = None
class TSLogoutResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSLogoutErrorCode; errorMessage: Optional[str] = None
class TSValidateResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSValidateErrorCode; errorMessage: Optional[str] = None; newToken: Optional[str] = None
class TSSearchContractResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSSearchContractErrorCode; errorMessage: Optional[str] = None; contracts: List[TSContractModel] = Field(default_factory=list)
class TSSearchContractByIdResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSSearchContractByIdErrorCode; errorMessage: Optional[str] = None; contract: Optional[TSContractModel] = None
class TSRetrieveBarResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSRetrieveBarErrorCode; errorMessage: Optional[str] = None; bars: List[TSAggregateBarModel] = Field(default_factory=list)
class TSSearchOrderResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSSearchOrderErrorCode; errorMessage: Optional[str] = None; orders: List[TSOrderModel] = Field(default_factory=list)
class TSPlaceOrderResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSPlaceOrderErrorCode; errorMessage: Optional[str] = None; orderId: Optional[int] = None
class TSCancelOrderResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSCancelOrderErrorCode; errorMessage: Optional[str] = None
class TSModifyOrderResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSModifyOrderErrorCode; errorMessage: Optional[str] = None
class TSSearchPositionResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSSearchPositionErrorCode; errorMessage: Optional[str] = None; positions: List[TSPositionModel] = Field(default_factory=list)
class TSClosePositionResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSClosePositionErrorCode; errorMessage: Optional[str] = None
class TSPartialClosePositionResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSPartialClosePositionErrorCode; errorMessage: Optional[str] = None
class TSSearchHalfTradeResponse(BaseModel): model_config = MODEL_CONFIG_TS; success: bool; errorCode: TSSearchTradeErrorCode; errorMessage: Optional[str] = None; trades: List[TSHalfTradeModel] = Field(default_factory=list)