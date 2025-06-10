import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTradingStore, OrderType } from '@/store/tradingStore';
import { Minus, Plus, Settings } from 'lucide-react';
import { cn } from '@/lib/utils'; // shadcn's utility for conditional classes

// A small, well-defined sub-component is acceptable here.
// It now uses a 'variant' prop for better clarity.
const QuantityButton: React.FC<{
  value: number;
  isActive: boolean;
  onClick: () => void;
}> = ({ value, isActive, onClick }) => (
  <Button
    onClick={onClick}
    // Use the 'default' variant for active, 'outline' for inactive
    variant={isActive ? 'default' : 'outline'}
    // Use Tailwind classes for sizing, ensuring consistency
    className="h-8 w-8 rounded-full text-xs font-bold shrink-0"
  >
    {value}
  </Button>
);

export const RightOrderPanel = () => { // Removed React.FC for modern practice
  // --- Idiomatic Zustand State Selection ---
  // Select state values needed for display
  const symbol = useTradingStore((state) => state.symbol);
  const orderType = useTradingStore((state) => state.orderType);
  const quantity = useTradingStore((state) => state.quantity);
  const activePosition = useTradingStore((state) => state.activePosition);

  // Select actions needed for handlers
  const setSymbol = useTradingStore((state) => state.setSymbol);
  const setOrderType = useTradingStore((state) => state.setOrderType);
  const setQuantity = useTradingStore((state) => state.setQuantity);
  const submitMarketOrder = useTradingStore((state) => state.submitMarketOrder);
  // ... other actions can be selected here if needed

  const handleQuantityChange = (delta: number) => {
    // Ensure quantity doesn't go below 1
    setQuantity(Math.max(1, quantity + delta));
  };

  const quickQuantities = [1, 3, 5, 10, 15];
  const positionText = activePosition
    ? `LONG ${activePosition.quantity}`
    : 'No Active Position';

  return (
    <aside className="w-64 bg-background border-l p-4 flex flex-col shrink-0 gap-4 text-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Order Panel</h2>
        <Button variant="ghost" size="icon" className="w-8 h-8">
          <Settings className="w-5 h-5" />
        </Button>
      </div>

      <div className="flex flex-col gap-3">
        <Select value={symbol} onValueChange={setSymbol}>
          <SelectTrigger>
            <SelectValue placeholder="Select Symbol" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ESM25">ESM25</SelectItem>
            <SelectItem value="NQM25">NQM25</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={orderType}
          onValueChange={(value) => setOrderType(value as OrderType)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select Order Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Market">Market</SelectItem>
            <SelectItem value="Limit">Limit</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex justify-between items-center">
        <Button
          variant="outline"
          size="icon"
          className="rounded-full w-8 h-8"
          onClick={() => handleQuantityChange(-1)}
        >
          <Minus className="w-4 h-4" />
        </Button>

        {quickQuantities.map((q) => (
          <QuantityButton
            key={q}
            value={q}
            isActive={q === quantity}
            onClick={() => setQuantity(q)}
          />
        ))}

        <Button
          variant="outline"
          size="icon"
          className="rounded-full w-8 h-8"
          onClick={() => handleQuantityChange(1)}
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      <Input
        type="number"
        value={quantity}
        onChange={(e) => setQuantity(parseInt(e.target.value, 10) || 0)}
        className="text-center text-lg font-bold"
      />
      
      {/* THEME-AWARE BUY/SELL BUTTONS */}
      <div className="flex flex-col gap-2">
        <Button
          size="lg"
          className="bg-green-500 text-white hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-700 dark:text-white font-bold h-12"
          onClick={() => submitMarketOrder('BUY')}
        >
          BUY {quantity} @ MARKET
        </Button>
        <Button
          size="lg"
          variant="destructive" // Using the built-in destructive variant
          className="font-bold h-12"
          onClick={() => submitMarketOrder('SELL')}
        >
          SELL {quantity} @ MARKET
        </Button>
      </div>
      
      {/* Position display */}
      <div className="text-center text-muted-foreground p-3 text-xs font-bold border rounded-md">
        {positionText}
      </div>

      {/* Secondary Actions */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <Button variant="secondary">JOIN BID</Button>
        <Button variant="secondary">JOIN ASK</Button>
        <Button variant="secondary">CLOSE POSITION</Button>
        <Button variant="secondary">REVERSE</Button>
      </div>
      
      {/* Pushed to bottom */}
      <div className="grid grid-cols-2 gap-2 mt-auto">
        <Button variant="secondary">FLATTEN ALL</Button>
        <Button variant="secondary">CANCEL ALL</Button>
      </div>
    </aside>
  );
};