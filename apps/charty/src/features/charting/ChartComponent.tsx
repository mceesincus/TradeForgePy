// src/features/charting/ChartComponent.tsx
import React, { useRef, useLayoutEffect, useEffect } from 'react';
import * as LightweightCharts from 'lightweight-charts';
import { getMockHistoricalData, subscribeToRealtimeData, CandlestickData as MarketDataCandlestick } from './services/marketDataService';
// Notifier and websocket service can remain for future use, but are not strictly needed for just rendering
import { useNotifier } from '@/features/notifications/useNotifier';
import { websocketService } from '../../services/websocketService';

// This component now has no props
export const ChartComponent: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const seriesRef = useRef<LightweightCharts.ISeriesApi<'Candlestick'> | null>(null);
  
  // Real-time update logic can stay, as it's self-contained
  useEffect(() => {
    const handleRealtimeUpdate = (newTick: MarketDataCandlestick) => {
      if (seriesRef.current) {
        seriesRef.current.update(newTick);
      }
    };
    const unsubscribe = subscribeToRealtimeData('/MES', handleRealtimeUpdate);
    return () => { unsubscribe(); };
  }, []);

  // Main chart creation logic
  useLayoutEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = LightweightCharts.createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      // We can disable the crosshair since there's no OHLC display
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Hidden,
      },
      layout: { background: { type: LightweightCharts.ColorType.Solid, color: 'transparent' }, textColor: '#D1D5DB' },
      grid: { vertLines: { color: 'transparent' }, horzLines: { color: 'transparent' } },
      timeScale: { borderColor: '#374151', timeVisible: true, rightOffset: 15 },
      rightPriceScale: { borderColor: '#374151' },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: true,
      borderUpColor: '#4ade80',
      borderDownColor: '#b91c1c',
      wickUpColor: '#4ade80',
      wickDownColor: '#b91c1c',
    });
    seriesRef.current = candlestickSeries;

    const historicalData = getMockHistoricalData();
    candlestickSeries.setData(historicalData);

    const handleResize = () => chart.resize(chartContainerRef.current!.clientWidth, chartContainerRef.current!.clientHeight);
    window.addEventListener('resize', handleResize);
    chart.timeScale().fitContent();

    return () => { 
      window.removeEventListener('resize', handleResize);
      chart.remove();
      seriesRef.current = null; 
    };
  }, []);

  return <div ref={chartContainerRef} className="w-full h-full min-h-[300px]" />;
};