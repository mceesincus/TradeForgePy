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
// === STEP 1: IMPORT THE NEW ZUSTAND STORE ===
import { useChartSettingsStore } from '@/store/chartSettingsStore';

interface ChartComponentProps {
  symbol: string;
  timeframe: string;
}

const BARS_TO_SHOW = 150;
const RIGHT_SIDE_MARGIN_IN_BARS = 5;

// The local `getChartColors` function is now REMOVED.

export const ChartComponent = ({ symbol, timeframe }: ChartComponentProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const { resolvedTheme } = useTheme();

  // === STEP 2: GET ALL SETTINGS FROM THE ZUSTAND STORE ===
  const chartSettings = useChartSettingsStore((state) => state);

  // This effect creates the chart once and applies initial settings from the store.
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Theming for elements not covered by the settings store
    const isDarkMode = resolvedTheme === 'dark';
    const staticColors = {
      backgroundColor: 'transparent',
      textColor: isDarkMode ? '#D1D5DB' : '#1F2937',
      gridColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
      borderColor: isDarkMode ? '#374151' : '#E5E7EB',
      crosshairLabelColor: isDarkMode ? '#334155' : '#e2e8f0',
    };

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: staticColors.backgroundColor },
        textColor: staticColors.textColor,
        fontFamily: 'system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: staticColors.gridColor },
        horzLines: { color: staticColors.gridColor },
      },
      rightPriceScale: {
        borderColor: staticColors.borderColor,
      },
      timeScale: {
        borderColor: staticColors.borderColor,
        timeVisible: true,
        // Bar spacing is now read from the store
        barSpacing: chartSettings.barSpacing,
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { labelBackgroundColor: staticColors.crosshairLabelColor },
        horzLine: { labelBackgroundColor: staticColors.crosshairLabelColor },
      },
    });
    chartRef.current = chart;

    const candlestickSeries = chart.addCandlestickSeries({
      // All candle colors are now read directly from the store
      upColor: chartSettings.upColor,
      downColor: chartSettings.downColor,
      borderUpColor: chartSettings.borderUpColor,
      borderDownColor: chartSettings.borderDownColor,
      wickUpColor: chartSettings.wickUpColor,
      wickDownColor: chartSettings.wickDownColor,
      borderVisible: true,
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
  }, []); // This effect runs only once on mount.

  // === STEP 3: CREATE A NEW EFFECT TO DYNAMICALLY UPDATE SETTINGS ===
  // This effect watches for any changes in our settings store and applies them.
  useEffect(() => {
    if (!chartRef.current || !seriesRef.current) return;

    // Apply bar spacing change to the time scale
    chartRef.current.timeScale().applyOptions({
      barSpacing: chartSettings.barSpacing,
    });

    // Apply all color changes to the candlestick series
    seriesRef.current.applyOptions({
      upColor: chartSettings.upColor,
      downColor: chartSettings.downColor,
      borderUpColor: chartSettings.borderUpColor,
      borderDownColor: chartSettings.borderDownColor,
      wickUpColor: chartSettings.wickUpColor,
      wickDownColor: chartSettings.wickDownColor,
    });
  }, [chartSettings]); // The dependency array watches the entire settings object.

  // This effect handles theme changes for elements not in the settings store.
  useEffect(() => {
    if (!chartRef.current) return;
    const isDarkMode = resolvedTheme === 'dark';
    const staticColors = {
      textColor: isDarkMode ? '#D1D5DB' : '#1F2937',
      gridColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
      borderColor: isDarkMode ? '#374151' : '#E5E7EB',
      crosshairLabelColor: isDarkMode ? '#334155' : '#e2e8f0',
    };
    chartRef.current.applyOptions({
      layout: { textColor: staticColors.textColor },
      grid: { vertLines: { color: staticColors.gridColor }, horzLines: { color: staticColors.gridColor } },
      rightPriceScale: { borderColor: staticColors.borderColor },
      timeScale: { borderColor: staticColors.borderColor },
      crosshair: {
        vertLine: { labelBackgroundColor: staticColors.crosshairLabelColor },
        horzLine: { labelBackgroundColor: staticColors.crosshairLabelColor },
      },
    });
  }, [resolvedTheme]);


  // Data loading and realtime update effects remain unchanged.
  useEffect(() => {
    if (!seriesRef.current) return;
    const abortController = new AbortController();
    const { signal } = abortController;
    seriesRef.current.setData([]);
    getHistoricalData(symbol, timeframe, signal)
      .then((initialData) => {
        if (!signal.aborted && seriesRef.current && chartRef.current) {
          seriesRef.current.setData(initialData);
          if (initialData.length > 0) {
            const lastIndex = initialData.length - 1;
            const logicalRange = {
              from: Math.max(0, lastIndex - BARS_TO_SHOW),
              to: lastIndex + RIGHT_SIDE_MARGIN_IN_BARS,
            };
            chartRef.current.timeScale().setVisibleLogicalRange(logicalRange);
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