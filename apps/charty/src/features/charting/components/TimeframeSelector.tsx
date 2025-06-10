import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

/**
 * Defines the props for the TimeframeSelector.
 * It's a controlled component, requiring the current value and a change handler.
 */
interface TimeframeSelectorProps {
  timeframe: string;
  onTimeframeChange: (newTimeframe: string) => void;
  // An optional array of available timeframes can be passed in
  availableTimeframes?: string[];
  disabled?: boolean;
}

// Default list of timeframes if none are provided via props
const DEFAULT_TIMEFRAMES = ['1m', '5m', '15m', '1H', '4H', '1D'];

/**
 * A controlled select component for choosing a chart timeframe.
 * It is styled to be compact and consistent with the application's UI.
 */
export const TimeframeSelector = ({
  timeframe,
  onTimeframeChange,
  availableTimeframes = DEFAULT_TIMEFRAMES,
  disabled = false,
}: TimeframeSelectorProps) => {
  return (
    <div className="flex flex-col space-y-1.5">
      <Label htmlFor="timeframe-select" className="text-xs text-muted-foreground">
        Timeframe
      </Label>
      <Select
        value={timeframe}
        onValueChange={onTimeframeChange}
        disabled={disabled}
      >
        <SelectTrigger id="timeframe-select" className="h-8 text-sm">
          <SelectValue placeholder="Select timeframe" />
        </SelectTrigger>
        <SelectContent>
          {availableTimeframes.map((tf) => (
            <SelectItem key={tf} value={tf} className="text-sm">
              {tf}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};