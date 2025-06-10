// src/features/charting/ChartContainer.tsx

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ChartComponent } from './ChartComponent';
import { ChartOverlay } from './components/ChartOverlay';
import { useTradingStore } from '@/store/tradingStore';

// Final, simplified version of the container.
export const ChartContainer = ({ className, timeframe }: { className?: string; timeframe: string }) => {
  const symbol = useTradingStore((state) => state.symbol);

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      {/*
        The entire card is now dedicated to the chart content.
        The OHLC display has been removed.
      */}
      <CardContent className="flex-grow relative p-0 min-h-0">
        {/* The overlay provides the Symbol/Timeframe watermark */}
        <ChartOverlay symbol={symbol} timeframe={timeframe} />

        {/* The chart component fills the entire container */}
        <ChartComponent
          symbol={symbol}
          timeframe={timeframe}
        />
      </CardContent>
    </Card>
  );
};