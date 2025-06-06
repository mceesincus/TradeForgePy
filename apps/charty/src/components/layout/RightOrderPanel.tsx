// src/components/layout/RightOrderPanel.tsx
import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator"; // A nice horizontal line component

// Add the Separator component if you don't have it
// npx shadcn-ui@latest add separator

export const RightOrderPanel: React.FC = () => {
  const quickQuantities = [1, 5, 10, 25, 50];

  return (
    <aside className="w-72 md:w-80 bg-background border-l p-4 flex flex-col gap-6">
      {/* Instrument Selection */}
      <div>
        <Label htmlFor="instrument-select" className="text-xs font-semibold">Contract</Label>
        <Select defaultValue="ESM24">
          <SelectTrigger id="instrument-select" className="mt-1">
            <SelectValue placeholder="Select Instrument" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ESM24">ESM24</SelectItem>
            <SelectItem value="NQM24">NQM24</SelectItem>
            <SelectItem value="RTYM24">RTYM24</SelectItem>
            <SelectItem value="YMZ24">YMZ24</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Order Type and Quantity */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="order-type" className="text-xs font-semibold">Order Type</Label>
          <Select defaultValue="Market">
            <SelectTrigger id="order-type" className="mt-1">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Market">Market</SelectItem>
              <SelectItem value="Limit">Limit</SelectItem>
              <SelectItem value="Stop">Stop</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="quantity" className="text-xs font-semibold">Quantity</Label>
          <Input id="quantity" type="number" defaultValue="1" className="mt-1" />
        </div>
      </div>
      <div className="grid grid-cols-5 gap-2">
        {quickQuantities.map(qty => (
          <Button key={qty} variant="outline" size="sm">{qty}</Button>
        ))}
      </div>
      
      {/* Main Action Buttons */}
      <div className="grid grid-cols-2 gap-4 mt-2">
         <Button size="lg" className="bg-green-600 hover:bg-green-700 text-white">BUY</Button>
         <Button size="lg" className="bg-red-600 hover:bg-red-700 text-white">SELL</Button>
      </div>

      <Separator />

      {/* Position and Management */}
      <div className="text-center">
         <p className="text-sm text-muted-foreground">No Active Position</p>
         {/* We can add more details here later, e.g., P/L */}
      </div>
      <div className="grid grid-cols-2 gap-4">
         <Button variant="secondary">Close Position</Button>
         <Button variant="secondary">Reverse</Button>
      </div>
      
      <Separator />

      {/* Global Actions */}
      <div className="flex flex-col gap-3 mt-auto"> {/* mt-auto pushes this block to the bottom */}
         <Button variant="destructive" className="w-full">FLATTEN ALL</Button>
         <Button variant="outline" className="w-full">CANCEL ALL</Button>
      </div>
    </aside>
  );
};