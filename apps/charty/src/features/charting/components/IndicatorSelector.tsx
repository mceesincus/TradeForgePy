// src/features/charting/components/IndicatorSelector.tsx
import React from 'react';
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Define the shape of an indicator config
export interface IndicatorConfig {
  name: 'SMA'; // For now, only SMA
  period: number;
  color: string;
}

interface IndicatorSelectorProps {
  // We will pass down the list of active indicators and a function to toggle them
  activeIndicators: IndicatorConfig[];
  onToggleIndicator: (indicator: IndicatorConfig) => void;
}

// For this example, we have a hardcoded list of available indicators
const availableIndicators: IndicatorConfig[] = [
  { name: 'SMA', period: 20, color: 'rgba(255, 165, 0, 0.8)' },
  { name: 'SMA', period: 50, color: 'rgba(30, 144, 255, 0.8)' },
];

export const IndicatorSelector: React.FC<IndicatorSelectorProps> = ({ activeIndicators, onToggleIndicator }) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="text-xs h-8">
          Indicators
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuLabel>Overlays</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {availableIndicators.map((indicator) => (
          <DropdownMenuCheckboxItem
            key={`${indicator.name}-${indicator.period}`}
            // Check if an indicator with the same name and period is active
            checked={activeIndicators.some(
              (active) => active.name === indicator.name && active.period === indicator.period
            )}
            onSelect={(e) => {
              e.preventDefault(); // Prevent menu from closing on click
              onToggleIndicator(indicator);
            }}
          >
            {indicator.name} ({indicator.period})
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};