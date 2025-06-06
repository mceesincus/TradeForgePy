// src/features/charting/components/SymbolSelector.tsx
import React from 'react';
import { Input } from "@/components/ui/input"; // Using Shadcn UI Input
import { Label } from "@/components/ui/label";   // Using Shadcn UI Label

interface SymbolSelectorProps {
  // Props for current symbol, onChange handler will be added later
}

export const SymbolSelector: React.FC<SymbolSelectorProps> = () => {
  return (
    <div className="flex flex-col space-y-1.5">
      <Label htmlFor="symbol-input" className="text-xs text-muted-foreground">Symbol</Label>
      <Input
        id="symbol-input"
        type="text"
        placeholder="e.g., /MES, AAPL"
        defaultValue="/MESM24" // Placeholder default value
        className="h-8 text-sm" // Smaller input
        // value and onChange will be added later
      />
    </div>
  );
};