// src/features/charting/components/ChartOverlay.tsx
import React from 'react';

interface ChartOverlayProps {
  symbol: string;
  timeframe: string;
}

export const ChartOverlay: React.FC<ChartOverlayProps> = ({ symbol, timeframe }) => {
  return (
    // This div is now positioned absolutely within its parent.
    // `z-10` ensures it sits on top of the chart canvas.
    // `pointer-events-none` allows mouse interactions to "pass through" to the chart below.
    <div className="absolute top-3 left-4 z-10 pointer-events-none">
      <p className="text-2xl font-bold text-gray-500/40"> {/* Slightly transparent text */}
        {symbol} <span className="font-semibold">{timeframe}</span>
      </p>
    </div>
  );
};