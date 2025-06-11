// src/components/layout/ChartToolbar.tsx

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Pencil,
  MousePointer,
  CandlestickChart,
  BarChart3,
  LineChart,
  Settings2,
} from 'lucide-react';
import {
  Dialog,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
// Corrected import path assuming ChartSettingsDialog is in `src/components/settings`
import { ChartSettingsDialogContent } from '@/components/settings/ChartSettingsDialog';

// Define styles (preserved as requested)
const iconButtonStyle: React.CSSProperties = {
  height: '40px',
  width: '40px',
};
const textButtonStyle: React.CSSProperties = {
  height: '40px',
};
const iconStyle: React.CSSProperties = {
  height: '24px',
  width: '24px',
};

// The component is correctly named and exported as ChartToolbar.
export const ChartToolbar = () => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <div className="h-14 flex-shrink-0 bg-background border-b flex items-center px-4 gap-2">
      <div className="flex items-center gap-1">
        <Button variant="ghost" style={iconButtonStyle}>
          <MousePointer style={iconStyle} />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" style={iconButtonStyle}>
              <Pencil style={iconStyle} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Trend Line</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <Separator orientation="vertical" className="h-8" />
      <div className="flex items-center gap-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" style={textButtonStyle}>
              <CandlestickChart className="h-5 w-5 mr-2" />
              Candles
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
             <DropdownMenuItem>
              <CandlestickChart className="h-4 w-4 mr-2" />
              Candles
            </DropdownMenuItem>
            <DropdownMenuItem>
              <BarChart3 className="h-4 w-4 mr-2" />
              Bars
            </DropdownMenuItem>
            <DropdownMenuItem>
              <LineChart className="h-4 w-4 mr-2" />
              Line
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="flex-grow" />

      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogTrigger asChild>
          <Button variant="ghost" style={iconButtonStyle}>
            <Settings2 style={iconStyle} />
          </Button>
        </DialogTrigger>
        <ChartSettingsDialogContent />
      </Dialog>
    </div>
  );
};