# ==============================================================================
# tradeforgepy/tradeforgepy/core/enums.py
# ==============================================================================
from enum import Enum

class AssetClass(str, Enum):
    FUTURES = "FUTURES"
    STOCK = "STOCK"
    OPTION = "OPTION"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    INDEX = "INDEX"
    UNKNOWN = "UNKNOWN"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    STOP_LIMIT = "STOP_LIMIT"
    JOIN_BID = "JOIN_BID"
    JOIN_ASK = "JOIN_ASK"
    # TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET" # This feature is disabled due to provider API ambiguity.

class OrderTimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTD = "GTD"

class OrderStatus(str, Enum):
    PENDING_SUBMIT = "PENDING_SUBMIT"
    PENDING_NEW = "PENDING_NEW"
    NEW = "NEW"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"

class BarTimeframeUnit(str, Enum):
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"

class StreamConnectionStatus(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHENTICATED = "AUTHENTICATED"
    SUBSCRIBED = "SUBSCRIBED"
    ERROR = "ERROR"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"

class MarketDataType(str, Enum):
    QUOTE = "QUOTE"
    TRADE = "TRADE"
    DEPTH = "DEPTH"
    CANDLE = "CANDLE"

class UserDataType(str, Enum):
    ORDER_UPDATE = "ORDER_UPDATE"
    POSITION_UPDATE = "POSITION_UPDATE"
    ACCOUNT_UPDATE = "ACCOUNT_UPDATE"
    USER_TRADE = "USER_TRADE"