// src/components/layout/Header.tsx
import React from 'react';
import { Separator } from '@/components/ui/separator';

export const Header: React.FC = () => {
  return (
    <header className="bg-background border-b h-16 flex items-center px-6 shrink-0 justify-between">
      <div className="font-semibold text-lg text-foreground">
        Trading Application
      </div>
      
      {/* Mock Account Info */}
      <div className="flex items-center gap-4 text-sm">
        <div className='text-right'>
          <p className='font-bold text-foreground'>$50,071.02</p>
          <p className='text-xs text-muted-foreground'>Account Balance</p>
        </div>
        <Separator orientation="vertical" className="h-8"/>
        <div className='text-right'>
          <p className='font-bold text-green-500'>$0.00</p>
          <p className='text-xs text-muted-foreground'>Unrealized P/L</p>
        </div>
        <Separator orientation="vertical" className="h-8"/>
        <div>
          <p className='text-sm text-foreground'>Bot Status: <span className='font-semibold text-red-500'>Inactive</span></p>
        </div>
      </div>
    </header>
  );
};