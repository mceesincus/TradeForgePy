// src/features/charting/services/marketDataService.ts
import { OhlcData, UTCTimestamp } from 'lightweight-charts';
import { websocketService } from '../../../services/websocketService';

export interface CandlestickData extends OhlcData {
  time: UTCTimestamp;
}

export const getMockHistoricalData = (): CandlestickData[] => {
  const data: CandlestickData[] = [];
  // Start 75 days ago
  let time = (Math.floor(Date.now() / 1000) - 75 * 86400) as UTCTimestamp;
  let price = 5000;

  // Generate 75 mock candles
  for (let i = 0; i < 75; i++) {
    const open = price + (Math.random() - 0.5) * 10;
    const close = open + (Math.random() - 0.5) * 20;
    const high = Math.max(open, close) + Math.random() * 5;
    const low = Math.min(open, close) - Math.random() * 5;

    data.push({
      time,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
    });

    time = (time + 86400) as UTCTimestamp;
    price = close;
  }
  return data;
};

let mockDataInterval: NodeJS.Timeout | null = null;
let lastCandle: CandlestickData | null = null;

const startMockDataStream = (callback: (data: CandlestickData) => void) => {
  if (mockDataInterval) {
    clearInterval(mockDataInterval);
  }

  if (!lastCandle) {
    const historicalData = getMockHistoricalData();
    lastCandle = historicalData[historicalData.length - 1];
  }

  mockDataInterval = setInterval(() => {
    if (!lastCandle) return;

    const lastClose = lastCandle.close;
    const newClose = lastClose + (Math.random() - 0.49) * 2;
    const newHigh = Math.max(lastCandle.high, newClose);
    const newLow = Math.min(lastCandle.low, newClose);

    const updatedCandle: CandlestickData = {
      ...lastCandle,
      high: parseFloat(newHigh.toFixed(2)),
      low: parseFloat(newLow.toFixed(2)),
      close: parseFloat(newClose.toFixed(2)),
    };
    
    const isNewCandle = Math.random() > 0.95; 
    if (isNewCandle) {
        lastCandle = {
            time: (lastCandle.time + 86400) as UTCTimestamp,
            open: lastCandle.close,
            close: lastCandle.close,
            high: lastCandle.close,
            low: lastCandle.close,
        }
    } else {
        lastCandle = updatedCandle;
    }
    
    callback(lastCandle);
  }, 1000);
};

const stopMockDataStream = () => {
  if (mockDataInterval) {
    clearInterval(mockDataInterval);
    mockDataInterval = null;
    lastCandle = null;
  }
};

export const subscribeToRealtimeData = (
  symbol: string,
  callback: (data: CandlestickData) => void
) => {
  console.log(`Subscribing to mock real-time data for ${symbol}`);
  startMockDataStream(callback);

  return () => {
    console.log(`Unsubscribing from mock real-time data for ${symbol}`);
    stopMockDataStream();
  };
};