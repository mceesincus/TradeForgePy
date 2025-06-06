// src/features/charting/components/OhlcDisplay.tsx
import React from 'react';

interface OhlcDisplayProps {
  open?: number | string;
  high?: number | string;
  low?: number | string;
  close?: number | string;
  // We can add volume, time, etc. later
}

const formatPrice = (price?: number | string) => price !== undefined ? Number(price).toFixed(2) : '-';

export const OhlcDisplay: React.FC<OhlcDisplayProps> = ({
  open = '-',
  high = '-',
  low = '-',
  close = '-',
}) => {
  return (
    <div className="flex space-x-3 text-xs text-muted-foreground tabular-nums">
      <span>O: <span className="text-foreground">{formatPrice(open)}</span></span>
      <span>H: <span className="text-foreground">{formatPrice(high)}</span></span>
      <span>L: <span className="text-foreground">{formatPrice(low)}</span></span>
      <span>C: <span className="text-foreground">{formatPrice(close)}</span></span>
    </div>
  );
};