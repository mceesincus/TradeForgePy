import React, { useRef, useEffect } from 'react';
import {
  createChart,
  ColorType,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  Time,
} from 'lightweight-charts';
import {
  getHistoricalData,
  subscribeToRealtimeData,
  CandlestickData as MarketDataCandlestick,
} from './services/marketDataService';
import { useTheme } from 'next-themes';

interface ChartComponentProps {
  symbol: string;
  timeframe: string;
}

const getChartColors = (theme: string | undefined) => {
  const isDarkMode = theme === 'dark';
  return {
    backgroundColor: 'transparent',
    textColor: isDarkMode ? '#D1D5DB' : '#1F2937',
    gridColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
    borderColor: isDarkMode ? '#374151' : '#E5E7EB',
    upColor: isDarkMode ? '#22c55e' : '#16a34a',
    downColor: isDarkMode ? '#ef4444' : '#dc2626',
  };
};

export const ChartComponent = ({ symbol, timeframe }: ChartComponentProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    if (!chartContainerRef.current) return;
    const colors = getChartColors(resolvedTheme);
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: colors.backgroundColor },
        textColor: colors.textColor,
        fontFamily: 'system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
      rightPriceScale: {
        borderColor: colors.borderColor,
      },
      timeScale: {
        borderColor: colors.borderColor,
        timeVisible: true,
        // === FIX #1: INCREASE BAR SPACING FOR A WIDER APPEARANCE ===
        barSpacing: 18,
        rightOffset: 5, // A smaller offset to maximize space
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
    });
    chartRef.current = chart;
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: colors.upColor,
      downColor: colors.downColor,
      borderVisible: false,
      wickUpColor: colors.upColor,
      wickDownColor: colors.downColor,
    });
    seriesRef.current = candlestickSeries;
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chart.applyOptions({ width, height });
      }
    });
    resizeObserver.observe(chartContainerRef.current);
    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current) return;
    const colors = getChartColors(resolvedTheme);
    chartRef.current.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: colors.backgroundColor },
        textColor: colors.textColor,
      },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
      rightPriceScale: { borderColor: colors.borderColor },
      timeScale: { borderColor: colors.borderColor },
    });
    seriesRef.current?.applyOptions({
      upColor: colors.upColor,
      downColor: colors.downColor,
      wickUpColor: colors.upColor,
      wickDownColor: colors.downColor,
    });
  }, [resolvedTheme]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const abortController = new AbortController();
    const { signal } = abortController;
    seriesRef.current.setData([]);
    getHistoricalData(symbol, timeframe, signal)
      .then((initialData) => {
        if (!signal.aborted && seriesRef.current && chartRef.current) {
          seriesRef.current.setData(initialData);

          // === FIX #2: MANUALLY SET THE VISIBLE RANGE INSTEAD OF `fitContent()` ===
          // This prevents the chart from trying to show all data at once,
          // giving our barSpacing option room to work.
          if (initialData.length > 0) {
            const from = initialData[Math.max(0, initialData.length - 150)].time; // Show last 150 bars
            const to = initialData[initialData.length - 1].time;
            chartRef.current.timeScale().setVisibleRange({ from, to });
          }
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          console.error('Failed to fetch historical data:', error);
        }
      });
    return () => {
      abortController.abort();
    };
  }, [symbol, timeframe]);

  useEffect(() => {
    const handleRealtimeUpdate = (newTick: MarketDataCandlestick) => {
      if (seriesRef.current) {
        seriesRef.current.update(newTick);
      }
    };
    const unsubscribe = subscribeToRealtimeData(symbol, handleRealtimeUpdate);
    return () => unsubscribe();
  }, [symbol]);

  return <div ref={chartContainerRef} className="w-full h-full" />;
};