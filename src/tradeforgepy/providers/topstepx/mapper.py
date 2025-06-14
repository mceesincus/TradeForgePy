# tradeforgepy/providers/topstepx/mapper.py
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime
from decimal import Decimal

from tradeforgepy.utils.time_utils import ensure_utc, UTC_TZ

from .schemas_ts import (
    TSTradingAccountModel, TSContractModel, TSAggregateBarModel, TSOrderModel,
    TSPositionModel, TSHalfTradeModel, TSPositionType,
    TSOrderStatus, TSTraderOrderType, TSOrderSide, TSAggregateBarUnit
)
from tradeforgepy.core.models_generic import (
    Account as GenericAccount, Contract as GenericContract, BarData as GenericBarData,
    Order as GenericOrder, Position as GenericPosition, Trade as GenericTrade,
    QuoteEvent, MarketTradeEvent, DepthSnapshotEvent, DepthLevel,
    OrderUpdateEvent, PositionUpdateEvent, AccountUpdateEvent, UserTradeEvent
)
from tradeforgepy.core.enums import (
    AssetClass, OrderSide, OrderType, OrderStatus, OrderTimeInForce, BarTimeframeUnit
)

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

def map_ts_order_type_to_generic(ts_type: TSTraderOrderType) -> Optional[OrderType]:
    mapping = {
        TSTraderOrderType.LIMIT: OrderType.LIMIT,
        TSTraderOrderType.MARKET: OrderType.MARKET,
        TSTraderOrderType.STOP: OrderType.STOP_MARKET,
        TSTraderOrderType.STOP_LIMIT: OrderType.STOP_LIMIT,
        # TSTraderOrderType.TRAILING_STOP is intentionally not mapped to a generic type
    }
    return mapping.get(ts_type)

def map_ts_order_side_to_generic(ts_side: TSOrderSide) -> OrderSide:
    return OrderSide.BUY if ts_side == TSOrderSide.BID else OrderSide.SELL

def map_generic_order_type_to_ts(g_type: OrderType) -> TSTraderOrderType:
    mapping = {
        OrderType.LIMIT: TSTraderOrderType.LIMIT,
        OrderType.MARKET: TSTraderOrderType.MARKET,
        OrderType.STOP_MARKET: TSTraderOrderType.STOP,
        OrderType.STOP_LIMIT: TSTraderOrderType.STOP_LIMIT,
    }
    ts_code = mapping.get(g_type)
    if ts_code is None: raise ValueError(f"Unsupported generic order type for TopStepX: {g_type.value}")
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
    if ts_unit is None: raise ValueError(f"Unsupported bar timeframe unit for TopStepX: {g_unit.value}")
    return ts_unit

# --- REST API Model Mappers ---
def map_ts_account_to_generic(ts_account: TSTradingAccountModel, provider_name: str) -> GenericAccount:
    return GenericAccount(
        provider_account_id=str(ts_account.id), account_name=ts_account.name,
        balance=float(ts_account.balance), currency="USD", can_trade=ts_account.canTrade,
        is_active=(ts_account.isVisible and ts_account.canTrade), provider_name=provider_name,
        provider_specific_data=ts_account.model_dump()
    )

def map_ts_accounts_to_generic(ts_accounts: List[TSTradingAccountModel], provider_name: str) -> List[GenericAccount]:
    return [map_ts_account_to_generic(acc, provider_name) for acc in ts_accounts if acc]

def map_ts_contract_to_generic(ts_contract: TSContractModel, provider_name: str) -> GenericContract:
    multiplier = 1.0
    if ts_contract.tickValue and ts_contract.tickSize > 0:
        multiplier = float(ts_contract.tickValue / ts_contract.tickSize)
    
    return GenericContract(
        provider_contract_id=ts_contract.id, symbol=ts_contract.name, exchange="CME",
        asset_class=AssetClass.FUTURES, description=ts_contract.description,
        tick_size=float(ts_contract.tickSize), tick_value=float(ts_contract.tickValue),
        price_currency="USD", multiplier=multiplier, is_tradable=ts_contract.activeContract,
        provider_name=provider_name, provider_specific_data=ts_contract.model_dump()
    )

def map_ts_contracts_to_generic(ts_contracts: List[TSContractModel], provider_name: str) -> List[GenericContract]:
    return [map_ts_contract_to_generic(c, provider_name) for c in ts_contracts if c]

def map_ts_order_details_to_generic(ts_order: TSOrderModel, provider_name: str) -> Optional[GenericOrder]:
    generic_order_type = map_ts_order_type_to_generic(ts_order.type)
    if generic_order_type is None:
        logger.debug(f"Skipping mapping for unsupported order type: {ts_order.type.name}")
        return None
        
    return GenericOrder(
        provider_order_id=str(ts_order.id), provider_account_id=str(ts_order.accountId),
        provider_contract_id=ts_order.contractId, order_type=generic_order_type,
        order_side=map_ts_order_side_to_generic(ts_order.side), original_size=float(ts_order.size),
        status=map_ts_order_status_to_generic(ts_order.status),
        limit_price=float(ts_order.limitPrice) if ts_order.limitPrice is not None else None,
        stop_price=float(ts_order.stopPrice) if ts_order.stopPrice is not None else None,
        filled_size=float(ts_order.fillVolume), time_in_force=OrderTimeInForce.GTC,
        created_at_utc=ts_order.creationTimestamp, updated_at_utc=ts_order.updateTimestamp,
        provider_name=provider_name, provider_specific_data=ts_order.model_dump()
    )

def map_ts_orders_to_generic(ts_orders: List[TSOrderModel], provider_name: str) -> List[GenericOrder]:
    generic_orders = []
    for o in ts_orders:
        if o:
            mapped_order = map_ts_order_details_to_generic(o, provider_name)
            if mapped_order:
                generic_orders.append(mapped_order)
    return generic_orders

def map_ts_position_to_generic(ts_pos: TSPositionModel, provider_name: str) -> GenericPosition:
    if ts_pos.type == TSPositionType.LONG:
        quantity = float(ts_pos.size)
    elif ts_pos.type == TSPositionType.SHORT:
        quantity = -float(ts_pos.size)
    else:  # Catches TSPositionType.UNDEFINED (0) and any other unexpected values
        quantity = 0.0
        logger.warning(
            f"Received an undefined or unknown position type '{ts_pos.type.value}' for "
            f"contract {ts_pos.contractId}. Mapping to a flat position (quantity 0). "
            f"Payload: {ts_pos.model_dump()}"
        )
        
    return GenericPosition(
        provider_account_id=str(ts_pos.accountId), provider_contract_id=ts_pos.contractId,
        quantity=quantity, average_entry_price=float(ts_pos.averagePrice),
        provider_name=provider_name, provider_specific_data=ts_pos.model_dump()
    )

def map_ts_positions_to_generic(ts_positions: List[TSPositionModel], provider_name: str) -> List[GenericPosition]:
    return [map_ts_position_to_generic(p, provider_name) for p in ts_positions if p]

def map_ts_trade_to_generic(ts_trade: TSHalfTradeModel, provider_name: str) -> GenericTrade:
    return GenericTrade(
        provider_trade_id=str(ts_trade.id), provider_order_id=str(ts_trade.orderId),
        provider_account_id=str(ts_trade.accountId), provider_contract_id=ts_trade.contractId,
        price=float(ts_trade.price), quantity=float(ts_trade.size),
        side=map_ts_order_side_to_generic(ts_trade.side), timestamp_utc=ts_trade.creationTimestamp,
        commission=float(ts_trade.fees), pnl=float(ts_trade.profitAndLoss) if ts_trade.profitAndLoss is not None else None,
        provider_name=provider_name, provider_specific_data=ts_trade.model_dump()
    )

def map_ts_trades_to_generic(ts_trades: List[TSHalfTradeModel], provider_name: str) -> List[GenericTrade]:
    return [map_ts_trade_to_generic(t, provider_name) for t in ts_trades if t]

# --- Stream Event Mappers ---
def _parse_ts_stream_timestamp(ts_payload: Dict[str, Any]) -> Optional[datetime]:
    ts_val = ts_payload.get("lastUpdated") or ts_payload.get("timestamp") or ts_payload.get("creationTimestamp")
    if ts_val:
        return ensure_utc(ts_val)
    return None

def map_ts_quote_to_generic_event(provider_contract_id: str, ts_quote_data: Dict[str, Any], provider_name: str) -> Optional[QuoteEvent]:
    try:
        event_timestamp = _parse_ts_stream_timestamp(ts_quote_data)
        if not event_timestamp:
            logger.warning(f"Skipping quote event for {provider_contract_id} due to missing timestamp. Payload: {ts_quote_data}")
            return None
            
        return QuoteEvent(
            provider_name=provider_name, provider_contract_id=provider_contract_id,
            timestamp_utc=event_timestamp,
            bid_price=ts_quote_data.get("bestBid"), ask_price=ts_quote_data.get("bestAsk"),
            last_price=ts_quote_data.get("lastPrice"), provider_specific_data=ts_quote_data
        )
    except Exception as e:
        logger.error(f"Error mapping TS quote stream: {e}", exc_info=True)
        return None

def map_ts_depth_to_generic_event(provider_contract_id: str, ts_depth_updates: List[Optional[Dict[str, Any]]], provider_name: str) -> Optional[DepthSnapshotEvent]:
    try:
        bids, asks = [], []
        latest_timestamp = None
        
        valid_updates = [u for u in ts_depth_updates if isinstance(u, dict) and 'timestamp' in u]
        if valid_updates:
            latest_timestamp = max(ensure_utc(u['timestamp']) for u in valid_updates)

        if not latest_timestamp:
            logger.warning(f"Skipping depth event for {provider_contract_id} due to missing timestamps in all levels. Payload: {ts_depth_updates}")
            return None

        for level_update in ts_depth_updates:
            if not isinstance(level_update, dict): continue
            price, size, type_code = level_update.get("price"), level_update.get("volume"), level_update.get("type")
            if price is None or size is None or type_code is None: continue
            side = None
            if type_code == 3: side = OrderSide.SELL
            elif type_code == 4: side = OrderSide.BUY
            if side:
                level = DepthLevel(price=float(price), size=float(size), side=side)
                (bids if side == OrderSide.BUY else asks).append(level)
        
        if not bids and not asks: return None
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)
        
        return DepthSnapshotEvent(
            provider_name=provider_name, provider_contract_id=provider_contract_id,
            timestamp_utc=latest_timestamp, bids=bids, asks=asks, is_snapshot=False,
            provider_specific_data={"raw_updates": ts_depth_updates}
        )
    except Exception as e:
        logger.error(f"Error mapping TS depth stream: {e}", exc_info=True)
        return None

def map_ts_market_trade_to_generic_event(provider_contract_id: str, ts_trade_data: Dict[str, Any], provider_name: str) -> Optional[MarketTradeEvent]:
    try:
        event_timestamp = _parse_ts_stream_timestamp(ts_trade_data)
        if not event_timestamp:
            logger.warning(f"Skipping market trade event for {provider_contract_id} due to missing timestamp. Payload: {ts_trade_data}")
            return None

        price = float(ts_trade_data['price'])
        size = float(ts_trade_data['volume'])
        aggressor_side = OrderSide.BUY if ts_trade_data.get('side') == 0 else OrderSide.SELL
        return MarketTradeEvent(
            provider_name=provider_name, provider_contract_id=provider_contract_id,
            timestamp_utc=event_timestamp,
            price=price, size=size, aggressor_side=aggressor_side,
            provider_specific_data=ts_trade_data
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error mapping TS market trade stream: {e}", exc_info=True)
        return None

def map_ts_account_update_to_generic_event(ts_payload: Dict[str, Any], provider_name: str) -> Optional[AccountUpdateEvent]:
    try:
        data_dict = ts_payload.get("data")
        if not isinstance(data_dict, dict): return None

        event_timestamp = _parse_ts_stream_timestamp(data_dict)
        if not event_timestamp:
            logger.warning(f"Skipping account update event due to missing timestamp. Payload: {ts_payload}")
            return None

        ts_account_model = TSTradingAccountModel.model_validate(data_dict)
        generic_account = map_ts_account_to_generic(ts_account_model, provider_name)
        return AccountUpdateEvent(
            provider_name=provider_name, provider_account_id=generic_account.provider_account_id,
            timestamp_utc=event_timestamp, account_data=generic_account,
            provider_specific_data=ts_payload
        )
    except Exception as e:
        logger.error(f"Error mapping TS account update stream: {e}", exc_info=True)
        return None

def map_ts_order_update_to_generic_event(ts_payload: Dict[str, Any], provider_name: str) -> Optional[OrderUpdateEvent]:
    try:
        data_dict = ts_payload.get("data")
        if not isinstance(data_dict, dict): return None

        event_timestamp = _parse_ts_stream_timestamp(data_dict)
        if not event_timestamp:
            logger.warning(f"Skipping order update event due to missing timestamp. Payload: {ts_payload}")
            return None

        ts_order_model = TSOrderModel.model_validate(data_dict)
        
        generic_order = map_ts_order_details_to_generic(ts_order_model, provider_name)
        if generic_order is None: return None # Skip unsupported order types
        
        return OrderUpdateEvent(
            provider_name=provider_name, provider_account_id=generic_order.provider_account_id,
            provider_contract_id=generic_order.provider_contract_id,
            timestamp_utc=event_timestamp,
            order_data=generic_order, provider_specific_data=ts_payload
        )
    except Exception as e:
        logger.error(f"Error mapping TS order update stream: {e}", exc_info=True)
        return None

def map_ts_user_trade_to_generic_event(ts_payload: Dict[str, Any], provider_name: str) -> Optional[UserTradeEvent]:
    try:
        if ts_payload.get("action") != 0: return None
        data_dict = ts_payload.get("data")
        if not isinstance(data_dict, dict): return None

        event_timestamp = _parse_ts_stream_timestamp(data_dict)
        if not event_timestamp:
            logger.warning(f"Skipping user trade event due to missing timestamp. Payload: {ts_payload}")
            return None

        ts_trade_model = TSHalfTradeModel.model_validate(data_dict)
        generic_trade = map_ts_trade_to_generic(ts_trade_model, provider_name)
        return UserTradeEvent(
            provider_name=provider_name, provider_account_id=generic_trade.provider_account_id,
            provider_contract_id=generic_trade.provider_contract_id,
            timestamp_utc=event_timestamp,
            trade_data=generic_trade, provider_specific_data=ts_payload
        )
    except Exception as e:
        logger.error(f"Error mapping TS user trade stream: {e}", exc_info=True)
        return None

def map_ts_position_update_to_generic_event(ts_payload: Dict[str, Any], provider_name: str) -> Optional[PositionUpdateEvent]:
    try:
        data_dict = ts_payload.get("data")
        if not isinstance(data_dict, dict): return None

        event_timestamp = _parse_ts_stream_timestamp(data_dict)
        if not event_timestamp:
            logger.warning(f"Skipping position update event due to missing timestamp. Payload: {ts_payload}")
            return None

        ts_pos_model = TSPositionModel.model_validate(data_dict)
        generic_pos = map_ts_position_to_generic(ts_pos_model, provider_name)
        return PositionUpdateEvent(
            provider_name=provider_name, provider_account_id=generic_pos.provider_account_id,
            provider_contract_id=generic_pos.provider_contract_id,
            timestamp_utc=event_timestamp,
            position_data=generic_pos, provider_specific_data=ts_payload
        )
    except Exception as e:
        logger.error(f"Error mapping TS position update stream: {e}", exc_info=True)
        return None