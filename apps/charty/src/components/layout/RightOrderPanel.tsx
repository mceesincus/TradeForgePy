// src/components/layout/RightOrderPanel.tsx
import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useTradingStore, OrderType } from '@/store/tradingStore';

export const RightOrderPanel: React.FC = () => {
  const symbol = useTradingStore((state) => state.symbol);
  const orderType = useTradingStore((state) => state.orderType);
  const quantity = useTradingStore((state) => state.quantity);
  const activePosition = useTradingStore((state) => state.activePosition);
  const { setSymbol, setOrderType, setQuantity, submitMarketOrder, closePosition, reversePosition, flattenAll } = useTradingStore.getState();
  const quickQuantities = [1, 5, 10, 25, 50];

  // The root element is a div, not an <aside> with layout classes
  return (
    <div className="flex flex-col gap-6 mt-6 h-full">
      {/* All the form elements go here... */}
      <div>
        <Label htmlFor="instrument-select" className="text-xs font-semibold">Contract</Label>
        <Select value={symbol} onValueChange={(value) => setSymbol(value)}>
          <SelectTrigger id="instrument-select" className="mt-1"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="ESM24">ESM24</SelectItem>
            <SelectItem value="NQM24">NQM24</SelectItem>
            {/* ... other items */}
          </SelectContent>
        </Select>
      </div>
      {/* ... the rest of your order panel content ... */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="order-type" className="text-xs font-semibold">Order Type</Label>
          <Select value={orderType} onValueChange={(value) => setOrderType(value as OrderType)}>
             <SelectTrigger id="order-type" className="mt-1"><SelectValue /></SelectTrigger>
             <SelectContent>
                <SelectItem value="Market">Market</SelectItem>
                <SelectItem value="Limit">Limit</SelectItem>
             </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="quantity" className="text-xs font-semibold">Quantity</Label>
          <Input id="quantity" type="number" value={quantity} onChange={(e) => setQuantity(parseInt(e.target.value, 10) || 0)} className="mt-1" />
        </div>
      </div>
      <div className="grid grid-cols-5 gap-2">{quickQuantities.map(qty => (<Button key={qty} variant="outline" size="sm" onClick={() => setQuantity(qty)}>{qty}</Button>))}</div>
      <div className="grid grid-cols-2 gap-4 mt-2">
        <Button size="lg" className="bg-green-600 hover:bg-green-700 text-white" onClick={() => submitMarketOrder('BUY')}>BUY</Button>
        <Button size="lg" className="bg-red-600 hover:bg-red-700 text-white" onClick={() => submitMarketOrder('SELL')}>SELL</Button>
      </div>
      <Separator/>
      <div className="text-center p-2 rounded-md bg-muted">
        {activePosition ? (
            <div>
              <p className={`font-bold text-sm ${activePosition.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>{activePosition.side === 'BUY' ? 'LONG' : 'SHORT'} {activePosition.quantity} {activePosition.symbol}</p>
              <p className="text-xs text-muted-foreground">@{activePosition.entryPrice.toFixed(2)}</p>
            </div>
        ) : (<p className="text-sm text-muted-foreground">No Active Position</p>)}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Button variant="secondary" onClick={closePosition} disabled={!activePosition}>Close Position</Button>
        <Button variant="secondary" onClick={reversePosition} disabled={!activePosition}>Reverse</Button>
      </div>
      <Separator/>
      <div className="flex flex-col gap-3 mt-auto">
        <Button variant="destructive" className="w-full" onClick={flattenAll}>FLATTEN ALL</Button>
        <Button variant="outline" className="w-full">CANCEL ALL</Button>
      </div>
    </div>
  );
};