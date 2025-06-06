// src/features/charting/ChartContainer.tsx
import React, { useState } from 'react';
import { ChartComponent, OhlcDataForDisplay } from './ChartComponent';
import { OhlcDisplay } from './components/OhlcDisplay';
import { SymbolSelector } from './components/SymbolSelector';
import { TimeframeSelector } from './components/TimeframeSelector';
// ** NEW IMPORTS **
import { IndicatorSelector, IndicatorConfig } from './components/IndicatorSelector';

interface ChartContainerProps {
  initialSymbol?: string;
  initialTimeframe?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  initialSymbol = "/MES",
  initialTimeframe = "15m"
}) => {
  const [currentOhlc, setCurrentOhlc] = useState<OhlcDataForDisplay>({});
  // ** NEW STATE FOR INDICATORS **
  const [activeIndicators, setActiveIndicators] = useState<IndicatorConfig[]>([]);

  const handleCrosshairMove = (data: OhlcDataForDisplay) => {
    setCurrentOhlc(data);
  };

  // ** NEW HANDLER FOR TOGGLING INDICATORS **
  const handleToggleIndicator = (indicatorToToggle: IndicatorConfig) => {
    setActiveIndicators((prev) => {
      const isAlreadyActive = prev.some(
        (i) => i.name === indicatorToToggle.name && i.period === indicatorToToggle.period
      );
      if (isAlreadyActive) {
        // Remove it
        return prev.filter(
          (i) => !(i.name === indicatorToToggle.name && i.period === indicatorToToggle.period)
        );
      } else {
        // Add it
        return [...prev, indicatorToToggle];
      }
    });
  };

  return (
    <div className="bg-card rounded-lg shadow text-card-foreground h-full flex flex-col">
      <div className="flex items-center justify-between gap-2 p-2 border-b">
        <div className="flex items-end gap-2">
          <SymbolSelector />
          <TimeframeSelector />
          {/* ** RENDER THE NEW SELECTOR ** */}
          <IndicatorSelector 
            activeIndicators={activeIndicators}
            onToggleIndicator={handleToggleIndicator}
          />
        </div>
        <OhlcDisplay
          open={currentOhlc.open}
          high={currentOhlc.high}
          low={currentOhlc.low}
          close={currentOhlc.close}
        />
      </div>
      <div className="flex-grow p-1">
        {/* ** PASS INDICATORS TO CHARTCOMPONENT ** */}
        <ChartComponent 
          onCrosshairMove={handleCrosshairMove}
          indicators={activeIndicators} 
        />
      </div>
    </div>
  );
};