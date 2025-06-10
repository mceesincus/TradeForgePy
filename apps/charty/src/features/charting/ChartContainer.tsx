// src/features/charting/ChartContainer.tsx

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card'; // CardHeader is no longer needed
import { ChartComponent } from './ChartComponent';
import { ChartOverlay } from './components/ChartOverlay';
import { OhlcDisplay } from './components/OhlcDisplay';
import { useTradingStore } from '@/store/tradingStore'; // Import the store to get the global symbol

// The container is now much simpler. It gets the symbol from the global store
// and the timeframe as a prop from App.tsx.
export const ChartContainer = ({ className, timeframe }: { className?: string; timeframe: string }) => {
  // --- STATE MANAGEMENT CHANGE ---
  // The symbol is now read from the global Zustand store.
  const symbol = useTradingStore((state) => state.symbol);

  // OHLC data would still be managed locally or passed up from the chart component.
  const [ohlc, setOhlc] = useState({});

  return (
    // The robust flexbox structure for the card's internals remains critical.
    <Card className={`h-full flex flex-col ${className}`}>
      {/*
        THE UI CHANGE: The CardHeader with all the controls has been removed.
        The chart content now takes up the entire card.
      */}
      <CardContent className="flex-grow relative p-0 min-h-0">
        {/*
          The Overlay and OHLC display are now positioned absolutely within the content area.
          This places them "on top" of the chart.
        */}
        <ChartOverlay symbol={symbol} timeframe={timeframe} />

        {/* OHLC display can be placed in a different corner, e.g., top-right */}
        <div className="absolute top-2 right-4 z-10 pointer-events-none">
          <OhlcDisplay {...ohlc} />
        </div>

        <ChartComponent
          symbol={symbol}
          timeframe={timeframe}
          // A prop like this could be used to push OHLC data up from the chart
          // onOhlcChange={setOhlc}
        />
      </CardContent>
    </Card>
  );
};