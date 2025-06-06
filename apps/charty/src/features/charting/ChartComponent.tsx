// src/features/charting/ChartComponent.tsx
import React, { useRef, useLayoutEffect, useEffect } from 'react';
import * as LightweightCharts from 'lightweight-charts';
import { getMockHistoricalData, subscribeToRealtimeData, CandlestickData as MarketDataCandlestick } from './services/marketDataService';
import { useNotifier } from '@/features/notifications/useNotifier';
import { websocketService } from '../../services/websocketService';
import { IndicatorConfig } from './components/IndicatorSelector';

export interface OhlcDataForDisplay {
  open?: number;
  high?: number;
  low?: number;
  close?: number;
}

interface ChartComponentProps {
  onCrosshairMove: (data: OhlcDataForDisplay) => void;
  indicators: IndicatorConfig[];
}

export const ChartComponent: React.FC<ChartComponentProps> = ({ onCrosshairMove, indicators }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<LightweightCharts.IChartApi | null>(null);
  const seriesRef = useRef<LightweightCharts.ISeriesApi<'Candlestick'> | null>(null);
  const indicatorSeriesRef = useRef<Map<string, LightweightCharts.ISeriesApi<'Line'>>>(new Map());
  const dataRef = useRef<MarketDataCandlestick[]>([]);
  const { notify } = useNotifier();

  useEffect(() => {
    const handleRealtimeUpdate = (newTick: MarketDataCandlestick) => {
      if (seriesRef.current) {
        seriesRef.current.update(newTick);
        const lastDataPoint = dataRef.current[dataRef.current.length - 1];
        if (lastDataPoint && newTick.time === lastDataPoint.time) {
          dataRef.current[dataRef.current.length - 1] = newTick;
        } else {
          dataRef.current.push(newTick);
        }
      }
    };
    const unsubscribe = subscribeToRealtimeData('/MES', handleRealtimeUpdate);
    const onOpen = () => notify("Connected to data stream!", undefined, 'success');
    const onClose = () => notify("Data stream disconnected.", undefined, 'error');
    websocketService.onOpen(onOpen);
    websocketService.onClose(onClose);
    return () => { unsubscribe(); };
  }, [notify]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    const candleData = dataRef.current;
    if (candleData.length === 0) return;
    indicatorSeriesRef.current.forEach((series, key) => {
      if (!indicators.some(ind => `${ind.name}-${ind.period}` === key)) {
        chart.removeSeries(series);
        indicatorSeriesRef.current.delete(key);
      }
    });
    indicators.forEach(indicator => {
      const key = `${indicator.name}-${indicator.period}`;
      if (!indicatorSeriesRef.current.has(key)) {
        const smaData: LightweightCharts.LineData[] = [];
        for (let i = indicator.period - 1; i < candleData.length; i++) {
          let sum = 0;
          for (let j = 0; j < indicator.period; j++) {
            sum += candleData[i - j].close;
          }
          smaData.push({ time: candleData[i].time, value: sum / indicator.period });
        }
        const lineSeries = chart.addLineSeries({ color: indicator.color, lineWidth: 2, lastValueVisible: false, priceLineVisible: false });
        lineSeries.setData(smaData);
        indicatorSeriesRef.current.set(key, lineSeries);
      }
    });
  }, [indicators]);

  useLayoutEffect(() => {
    if (!chartContainerRef.current) return;
    const chart = LightweightCharts.createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      layout: { background: { type: LightweightCharts.ColorType.Solid, color: 'transparent' }, textColor: '#D1D5DB' },
      grid: { vertLines: { color: '#374151' }, horzLines: { color: '#374151' } },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
        // ** THE FIX IS HERE **
        rightOffset: 15,
      },
      rightPriceScale: { borderColor: '#374151' },
    });
    chartRef.current = chart;

    const candlestickSeries = chart.addCandlestickSeries({ upColor: '#10B981', downColor: '#EF4444', borderVisible: false, wickUpColor: '#10B981', wickDownColor: '#EF4444' });
    seriesRef.current = candlestickSeries;

    const historicalData = getMockHistoricalData();
    dataRef.current = historicalData;
    candlestickSeries.setData(historicalData);

    chart.subscribeCrosshairMove(param => {
      const seriesData = param.seriesData.get(candlestickSeries);
      if (seriesData && param.time) {
        const ohlc = seriesData as LightweightCharts.CandlestickData;
        onCrosshairMove({ open: ohlc.open, high: ohlc.high, low: ohlc.low, close: ohlc.close });
      } else { onCrosshairMove({}); }
    });

    const handleResize = () => chart.resize(chartContainerRef.current!.clientWidth, chartContainerRef.current!.clientHeight);
    window.addEventListener('resize', handleResize);

    // This makes sure the chart auto-fits the data initially
    chart.timeScale().fitContent();

    return () => { window.removeEventListener('resize', handleResize); chart.remove(); chartRef.current = null; seriesRef.current = null; };
  }, [onCrosshairMove]);

  return <div ref={chartContainerRef} className="w-full h-full min-h-[300px]" />;
};