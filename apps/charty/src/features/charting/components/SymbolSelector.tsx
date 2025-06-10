import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

/**
 * Defines the props for the SymbolSelector component.
 * It's a controlled component, requiring the current value and a change handler.
 */
interface SymbolSelectorProps {
  symbol: string;
  onSymbolChange: (newSymbol: string) => void;
  // An optional disabled prop is added for better reusability
  disabled?: boolean;
}

/**
 * A controlled input component for selecting a financial symbol.
 * It is styled to be compact and consistent with the application's UI.
 */
export const SymbolSelector = ({
  symbol,
  onSymbolChange,
  disabled = false,
}: SymbolSelectorProps) => {
  return (
    <div className="flex flex-col space-y-1.5">
      <Label htmlFor="symbol-input" className="text-xs text-muted-foreground">
        Symbol
      </Label>
      <Input
        id="symbol-input"
        type="text"
        placeholder="e.g., BTCUSD, AAPL"
        value={symbol}
        onChange={(e) => onSymbolChange(e.target.value)}
        disabled={disabled}
        className="h-8 text-sm" // Compact size for the toolbar
      />
    </div>
  );
};