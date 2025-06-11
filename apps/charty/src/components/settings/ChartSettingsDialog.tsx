// src/components/settings/ChartSettingsDialog.tsx

import React from 'react';
import {
  DialogContent, // <-- We only need the content parts now
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { useChartSettingsStore, ChartSettings } from '@/store/chartSettingsStore';

const ColorInput = ({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) => (
  <div className="flex items-center justify-between">
    <Label>{label}</Label>
    <div className="flex items-center gap-2">
      <Input type="text" value={value} onChange={onChange} className="w-40 h-8 text-xs" />
      <Input type="color" value={value.startsWith('rgba') ? '#000000' : value} onChange={onChange} className="w-8 h-8 p-1" />
    </div>
  </div>
);

// === THE SPECIFIC FIX: This component now ONLY returns the dialog's content ===
export const ChartSettingsDialogContent = () => {
  const {
    barSpacing,
    upColor,
    downColor,
    borderUpColor,
    borderDownColor,
    wickUpColor,
    wickDownColor,
    setBarSpacing,
    setColor,
    resetToDefaults,
  } = useChartSettingsStore();

  const handleColorChange = (key: keyof Omit<ChartSettings, 'barSpacing'>) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setColor(key, e.target.value);
  };

  return (
    <DialogContent className="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Chart Appearance</DialogTitle>
        <DialogDescription>
          Customize the look and feel of the candlesticks. Changes are saved automatically.
        </DialogDescription>
      </DialogHeader>

      <div className="grid gap-6 py-4">
        <div className="grid gap-3">
          <Label htmlFor="bar-spacing">Candle Size (Bar Spacing)</Label>
          <div className="flex items-center gap-4">
            <Slider
              id="bar-spacing"
              min={2}
              max={40}
              step={1}
              value={[barSpacing]}
              onValueChange={(value) => setBarSpacing(value[0])}
            />
            <span className="text-sm font-medium w-8 text-center">{barSpacing}</span>
          </div>
        </div>
        <div className="grid gap-4">
          <h3 className="text-sm font-medium text-muted-foreground">Candle Colors</h3>
          <ColorInput label="Up-Candle Fill" value={upColor} onChange={handleColorChange('upColor')} />
          <ColorInput label="Up-Candle Border" value={borderUpColor} onChange={handleColorChange('borderUpColor')} />
          <ColorInput label="Up-Candle Wick" value={wickUpColor} onChange={handleColorChange('wickUpColor')} />
          <hr className="border-border" />
          <ColorInput label="Down-Candle Fill" value={downColor} onChange={handleColorChange('downColor')} />
          <ColorInput label="Down-Candle Border" value={borderDownColor} onChange={handleColorChange('borderDownColor')} />
          <ColorInput label="Down-Candle Wick" value={wickDownColor} onChange={handleColorChange('wickDownColor')} />
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={resetToDefaults}>
          Reset to Defaults
        </Button>
      </DialogFooter>
    </DialogContent>
  );
};