# tradeforgepy/providers/topstepx/mapper.py
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime
from decimal import Decimal

from .schemas_ts import (
    TSTradingAccountModel, TSContractModel, TSAggregateBarModel, TSOrderModel,
    TSPositionModel, TSHalfTradeModel,
    TSOrderStatus, TSTraderOrderType, TSOrderSide, TSAggregateBarUnit
)
from tradeforgepy.core.models_generic import (
    Account as GenericAccount, Contract as GenericContract, BarData as GenericBarData,
    Order as GenericOrder, Position as GenericPosition, Trade as GenericTrade,
    QuoteEvent, MarketTradeEvent, DepthSnapshotEvent, DepthLevel,
    OrderUpdateEvent, PositionUpdateEvent, AccountUpdateEvent, UserTradeEvent,
    GenericStreamEvent
)
from tradeforgepy.core.enums import (
    AssetClass, OrderSide, OrderType, OrderStatus, OrderTimeInForce, BarTimeframeUnit
)
from tradeforgepy.utils.time_utils import ensure_utc

logger = logging.getLogger(__name__)

# --- Enum Mappers ---
def map_ts_order_status_to_generic(ts_status: TSOrderStatus) -> OrderStatus:
    mapping = {
        TSOrderStatus.PENDING: OrderStatus.PENDING_NEW,
        TSOrderStatus.OPEN: OrderStatus.WORKING,
        TSOrderStatus.FILLED: OrderStatus.FILLED,
        TSOrderStatus.CANCELLED: OrderStatus.CANCELLED,
        TSOrderStatus.EXPIRED: OrderStatus.EXPIRED,
        TSOrderStatus.REJECTED: OrderStatus.REJECTED,
        TSOrderStatus.NONE: OrderStatus.UNKNOWN,
    }
    return mapping.get(ts_status, OrderStatus.UNKNOWN)

def map_ts_order_type_to_generic(ts_type: TSTraderOrderType) -> OrderType:
    mapping = {
        TSTraderOrderType.LIMIT: OrderType.LIMIT,
        TSTraderOrderType.MARKET: OrderType.MARKET,
        TSTraderOrderType.STOP: OrderType.STOP_MARKET,
        TSTraderOrderType.STOP_LIMIT: OrderType.STOP_LIMIT,
        TSTraderOrderType.TRAILING_STOP: OrderType.TRAILING_STOP_MARKET,
    }
    # Fallback for unknown types if needed, though STOP_MARKET is a good default for 'STOP'
    return mapping.get(ts_type, OrderType.MARKET)

def map_ts_order_side_to_generic(ts_side: TSOrderSide) -> OrderSide:
    return OrderSide.BUY if ts_side == TSOrderSide.BID else OrderSide.SELL

def map_generic_order_type_to_ts(g_type: OrderType) -> TSTraderOrderType:
    mapping = {
        OrderType.LIMIT: TSTraderOrderType.LIMIT,
        OrderType.MARKET: TSTraderOrderType.MARKET,
        OrderType.STOP_MARKET: TSTraderOrderType.STOP,
        OrderType.STOP_LIMIT: TSTraderOrderType.STOP_LIMIT,
        OrderType.TRAILING_STOP_MARKET: TSTraderOrderType.TRAILING_STOP,
    }
    ts_code = mapping.get(g_type)
    if ts_code is None:
        raise ValueError(f"Unsupported generic order type for TopStepX: {g_type.value}")
    return ts_code

def map_generic_order_side_to_ts(g_side: OrderSide) -> TSOrderSide:
    return TSOrderSide.BID if g_side == OrderSide.BUY else TSOrderSide.ASK

def map_generic_bar_unit_to_ts(g_unit: BarTimeframeUnit) -> TSAggregateBarUnit:
    mapping = {
        BarTimeframeUnit.SECOND: TSAggregateBarUnit.SECOND,
        BarTimeframeUnit.MINUTE: TSAggregateBarUnit.MINUTE,
        BarTimeframeUnit.HOUR: TSAggregateBarUnit.HOUR,
        BarTimeframeUnit.DAY: TSAggregateBarUnit.DAY,
        BarTimeframeUnit.WEEK: TSAggregateBarUnit.WEEK,
        BarTimeframeUnit.MONTH: TSAggregateBarUnit.MONTH,
    }
    ts_unit = mapping.get(g_unit)
    if ts_unit is None:
        raise ValueError(f"Unsupported bar timeframe unit for TopStepX: {g_unit.value}")
    return ts_unit

# --- REST API Model Mappers ---

def map_ts_account_to_generic(ts_account: TSTradingAccountModel, provider_name: str) -> GenericAccount:
    return GenericAccount(
        provider_account_id=str(ts_account.id),
        account_name=ts_account.name,
        balance=float(ts_account.balance),
        currency="USD",
        can_trade=ts_account.canTrade,
        is_active=(ts_account.isVisible and ts_account.canTrade),
        provider_name=provider_name,
        provider_specific_data=ts_account.model_dump()
    )

def map_ts_accounts_to_generic(ts_accounts: List[TSTradingAccountModel], provider_name: str) -> List[GenericAccount]:
    return [map_ts_account_to_generic(acc, provider_name) for acc in ts_accounts if acc]

def map_ts_contract_to_generic(ts_contract: TSContractModel, provider_name: str) -> GenericContract:
    multiplier = 1.0
    if ts_contract.tickValue and ts_contract.tickSize > 0:
        multiplier = float(ts_contract.tickValue / ts_contract.tickSize)
    
    return GenericContract(
        provider_contract_id=ts_contract.id,
        symbol=ts_contract.name,
        exchange="CME", # Assuming CME for now
        asset_class=AssetClass.FUTURES,
        description=ts_contract.description,
        tick_size=float(ts_contract.tickSize),
        tick_value=float(ts_contract.tickValue),
        price_currency="USD",
        multiplier=multiplier,
        is_tradable=ts_contract.activeContract,
        provider_name=provider_name,
        provider_specific_data=ts_contract.model_dump()
    )

def map_ts_contracts_to_generic(ts_contracts: List[TSContractModel], provider_name: str) -> List[GenericContract]:
    return [map_ts_contract_to_generic(c, provider_name) for c in ts_contracts if c]

def map_ts_order_details_to_generic(ts_order: TSOrderModel, provider_name: str) -> GenericOrder:
    return GenericOrder(
        provider_order_id=str(ts_order.id),
        provider_account_id=str(ts_order.accountId),
        provider_contract_id=ts_order.contractId,
        order_type=map_ts_order_type_to_generic(ts_order.type),
        order_side=map_ts_order_side_to_generic(ts_order.side),
        original_size=float(ts_order.size),
        status=map_ts_order_status_to_generic(ts_order.status),
        limit_price=float(ts_order.limitPrice) if ts_order.limitPrice is not None else None,
        stop_price=float(ts_order.stopPrice) if ts_order.stopPrice is not None else None,
        filled_size=float(ts_order.fillVolume),
        time_in_force=OrderTimeInForce.GTC,  # TopStepX orders are typically GTC
        created_at_utc=ts_order.creationTimestamp,
        updated_at_utc=ts_order.updateTimestamp,
        provider_name=provider_name,
        provider_specific_data=ts_order.model_dump()
    )

def map_ts_orders_to_generic(ts_orders: List[TSOrderModel], provider_name: str) -> List[GenericOrder]:
    return [map_ts_order_details_to_generic(o, provider_name) for o in ts_orders if o]

def map_ts_position_to_generic(ts_pos: TSPositionModel, provider_name: str) -> GenericPosition:
    # PositionType: 1 = Long, 2 = Short. We represent short with a negative quantity.
    quantity = float(ts_pos.size) if ts_pos.type == 1 else -float(ts_pos.size)
    return GenericPosition(
        provider_account_id=str(ts_pos.accountId),
        provider_contract_id=ts_pos.contractId,
        quantity=quantity,
        average_entry_price=float(ts_pos.averagePrice),
        provider_name=provider_name,
        provider_specific_data=ts_pos.model_dump()
    )

def map_ts_positions_to_generic(ts_positions: List[TSPositionModel], provider_name: str) -> List[GenericPosition]:
    return [map_ts_position_to_generic(p, provider_name) for p in ts_positions if p]

def map_ts_trade_to_generic(ts_trade: TSHalfTradeModel, provider_name: str) -> GenericTrade:
    return GenericTrade(
        provider_trade_id=str(ts_trade.id),
        provider_order_id=str(ts_trade.orderId),
        provider_account_id=str(ts_trade.accountId),
        provider_contract_id=ts_trade.contractId,
        price=float(ts_trade.price),
        quantity=float(ts_trade.size),
        side=map_ts_order_side_to_generic(ts_trade.side),
        timestamp_utc=ts_trade.creationTimestamp,
        commission=float(ts_trade.fees),
        pnl=float(ts_trade.profitAndLoss) if ts_trade.profitAndLoss is not None else None,
        provider_name=provider_name,
        provider_specific_data=ts_trade.model_dump()
    )

def map_ts_trades_to_generic(ts_trades: List[TSHalfTradeModel], provider_name: str) -> List[GenericTrade]:
    return [map_ts_trade_to_generic(t, provider_name) for t in ts_trades if t]


# --- Stream Event Mappers ---

def _parse_ts_stream_timestamp(ts_payload: Dict[str, Any]) -> datetime:
    # Prefer 'lastUpdated' as it seems more granular, fallback to 'timestamp'
    ts_val = ts_payload.get("lastUpdated") or ts_payload.get("timestamp")
    if ts_val:
        return ensure_utc(ts_val)
    # If no timestamp is in the payload, use the current time as a last resort
    return datetime.now(UTC_TZ)

def map_ts_quote_to_generic_event(provider_contract_id: str, ts_quote_data: Dict[str, Any], provider_name: str) -> Optional[QuoteEvent]:
    try:
        return QuoteEvent(
            provider_name=provider_name,
            provider_contract_id=provider_contract_id,
            timestamp_utc=_parse_ts_stream_timestamp(ts_quote_data),
            bid_price=ts_quote_data.get("bestBid"),
            ask_price=ts_quote_data.get("bestAsk"),
            last_price=ts_quote_data.get("lastPrice"),
            provider_specific_data=ts_quote_data
        )
    except Exception as e:
        logger.error(f"Error mapping TS quote stream: {e}. Data: {ts_quote_data}", exc_info=True)
        return None

def map_ts_depth_to_generic_event(provider_contract_id: str, ts_depth_updates: List[Optional[Dict[str, Any]]], provider_name: str) -> Optional[DepthSnapshotEvent]:
    try:
        bids, asks = [], []
        # Find the latest timestamp from the valid updates in the batch
        latest_timestamp = datetime.now(UTC_TZ)
        valid_updates = [u for u in ts_depth_updates if isinstance(u, dict) and 'timestamp' in u]
        if valid_updates:
            latest_timestamp = max(ensure_utc(u['timestamp']) for u in valid_updates)

        for level_update in ts_depth_updates:
            # Skip any null entries in the list
            if not isinstance(level_update, dict):
                continue
            
            price = level_update.get("price")
            size = level_update.get("volume")
            type_code = level_update.get("type")

            if price is None or size is None or type_code is None:
                continue

            # Type 3 is Ask, Type 4 is Bid. Ignore all others (5, 6, 7, 8, etc.).
            side = None
            if type_code == 3:
                side = OrderSide.SELL
            elif type_code == 4:
                side = OrderSide.BUY

            if side:
                level = DepthLevel(price=float(price), size=float(size), side=side)
                if side == OrderSide.BUY:
                    bids.append(level)
                else:
                    asks.append(level)
        
        # Only create an event if there were valid bid/ask updates
        if not bids and not asks:
            return None

        # Sort the results for a clean book
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        return DepthSnapshotEvent(
            provider_name=provider_name,
            provider_contract_id=provider_contract_id,
            timestamp_utc=latest_timestamp,
            bids=bids,
            asks=asks,
            is_snapshot=False, # These are incremental updates, not a full book snapshot
            provider_specific_data={"raw_updates": ts_depth_updates}
        )
    except Exception as e:
        logger.error(f"Error mapping TS depth stream: {e}. Data sample: {ts_depth_updates[:3]}...", exc_info=True)
        return None

def map_ts_market_trade_to_generic_event(provider_contract_id: str, ts_trade_data: Dict[str, Any], provider_name: str) -> Optional[MarketTradeEvent]:
    logger.warning(f"Mapper logic requires live `GatewayTrade` data. Payload: {ts_trade_data}")
    return None

def map_ts_account_update_to_generic_event(ts_account_payload: Dict[str, Any], provider_name: str) -> Optional[AccountUpdateEvent]:
    try:
        # The payload is {"action": 1, "data": {...}}
        # We need the inner 'data' dictionary.
        data_dict = ts_account_payload.get("data")
        if not isinstance(data_dict, dict):
            logger.warning(f"TS account update stream missing 'data' dict: {ts_account_payload}")
            return None
        
        # Use our existing REST mapper to convert the TS model to a generic one
        ts_account_model = TSTradingAccountModel.model_validate(data_dict)
        generic_account = map_ts_account_to_generic(ts_account_model, provider_name)

        return AccountUpdateEvent(
            provider_name=provider_name,
            provider_account_id=generic_account.provider_account_id,
            timestamp_utc=datetime.now(UTC_TZ), # Event doesn't have its own timestamp
            account_data=generic_account,
            provider_specific_data=ts_account_payload
        )
    except Exception as e:
        logger.error(f"Error mapping TS account update stream: {e}. Data: {ts_account_payload}", exc_info=True)
        return None

def map_ts_order_update_to_generic_event(ts_order_payload: Dict[str, Any], provider_name: str) -> Optional[OrderUpdateEvent]:
    logger.warning(f"Mapper logic requires live `GatewayUserOrder` data. Payload: {ts_order_payload}")
    return None

def map_ts_user_trade_to_generic_event(ts_trade_payload: Dict[str, Any], provider_name: str) -> Optional[UserTradeEvent]:
    logger.warning(f"Mapper logic requires live `GatewayUserTrade` data. Payload: {ts_trade_payload}")
    return None

def map_ts_position_update_to_generic_event(ts_pos_payload: Dict[str, Any], provider_name: str) -> Optional[PositionUpdateEvent]:
    logger.warning(f"Mapper logic requires live `GatewayUserPosition` data. Payload: {ts_pos_payload}")
    return None