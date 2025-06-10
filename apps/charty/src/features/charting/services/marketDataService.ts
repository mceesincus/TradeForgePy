// src/features/charting/services/marketDataService.ts
import { OhlcData, UTCTimestamp } from 'lightweight-charts';
import { websocketService } from '../../../services/websocketService';

export interface CandlestickData extends OhlcData {
  time: UTCTimestamp;
}

// ** THIS FUNCTION IS NOW MODIFIED TO BE TIMEFRAME-AWARE **
export const getHistoricalData = async (symbol: string, timeframe: string): Promise<CandlestickData[]> => {
  console.log(`Fetching historical data for ${symbol} on timeframe ${timeframe}... (using smart mock data)`);
  
  const data: CandlestickData[] = [];
  let price = 5000;
  
  // --- Logic to determine how much data to generate ---
  let daysToLoad = 20; // Default
  let intervalInMinutes = 60; // Default

  if (timeframe === '5m') {
    daysToLoad = 3;
    intervalInMinutes = 5;
  } else if (timeframe === '15m') {
    daysToLoad = 10;
    intervalInMinutes = 15;
  } else if (timeframe === '60m') {
    daysToLoad = 20;
    intervalInMinutes = 60;
  }

  const candlesPerDay = (24 * 60) / intervalInMinutes;
  const totalCandles = Math.floor(candlesPerDay * daysToLoad);
  const intervalInSeconds = intervalInMinutes * 60;
  
  let time = (Math.floor(Date.now() / 1000) - (totalCandles * intervalInSeconds)) as UTCTimestamp;
  
  for (let i = 0; i < totalCandles; i++) {
    const open = price + (Math.random() - 0.5) * (intervalInMinutes / 5); // Fluctuation scales with timeframe
    const close = open + (Math.random() - 0.5) * (intervalInMinutes / 2.5);
    const high = Math.max(open, close) + Math.random() * (intervalInMinutes / 10);
    const low = Math.min(open, close) - Math.random() * (intervalInMinutes / 10);

    data.push({
      time,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
    });

    time = (time + intervalInSeconds) as UTCTimestamp;
    price = close;
  }
  
  console.log(`Generated ${totalCandles} mock candles for ${timeframe} timeframe.`);
  return Promise.resolve(data);
};

// This function now subscribes to your live FastAPI WebSocket stream
export const subscribeToRealtimeData = (
  symbol: string,
  callback: (data: CandlestickData) => void
) => {
  const WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"; 
  websocketService.connect(WEBSOCKET_URL);

  const onOpen = () => {
    console.log(`WebSocket connection open. Subscribing to market data for ${symbol}...`);
    const subscriptionMessage = {
      action: "subscribe_market_data",
      params: { provider_contract_ids: [symbol], data_types: ["QUOTE"] }
    };
    websocketService.sendMessage(subscriptionMessage);
  };

  const unsubscribeFromOpen = websocketService.onOpen(onOpen);

  const onMessage = (event: any) => {
    if (event.event_type === 'quote' && event.symbol === symbol) {
      const candle = event.data as CandlestickData;
      if (candle && candle.time && candle.open) {
          callback(candle);
      }
    }
  };

  const unsubscribeFromMessage = websocketService.onMessage(onMessage);

  return () => {
    console.log(`Unsubscribing from real-time data for ${symbol}`);
    unsubscribeFromOpen();
    unsubscribeFromMessage();
    const unsubscribeMessage = {
      action: "unsubscribe_market_data",
      params: { provider_contract_ids: [symbol] }
    };
    websocketService.sendMessage(unsubscribeMessage);
  };
};