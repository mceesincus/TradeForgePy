// src/features/charting/components/TimeframeSelector.tsx
import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"; // Using Shadcn UI Select
import { Label } from "@/components/ui/label";

interface TimeframeSelectorProps {
  // Props for current timeframe, onChange handler will be added later
}

export const TimeframeSelector: React.FC<TimeframeSelectorProps> = () => {
  const timeframes = ["1m", "5m", "15m", "1H", "4H", "1D"];

  return (
    <div className="flex flex-col space-y-1.5">
      <Label htmlFor="timeframe-select" className="text-xs text-muted-foreground">Timeframe</Label>
      <Select defaultValue="15m"> {/* Placeholder default value */}
        {/* value and onValueChange will be added later */}
        <SelectTrigger id="timeframe-select" className="h-8 text-sm">
          <SelectValue placeholder="Select timeframe" />
        </SelectTrigger>
        <SelectContent>
          {timeframes.map((tf) => (
            <SelectItem key={tf} value={tf} className="text-sm">
              {tf}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};