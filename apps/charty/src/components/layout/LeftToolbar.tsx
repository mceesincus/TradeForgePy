// src/components/layout/LeftToolbar.tsx

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  BarChart,
  Settings,
  HelpCircle,
  GitPullRequestArrow,
  TrendingUp,
  SlidersHorizontal,
} from 'lucide-react';

// Define the styles as objects to ensure consistency.
// This bypasses the broken Tailwind build process entirely.
const buttonStyle: React.CSSProperties = {
  height: '56px',
  width: '56px',
};

const iconStyle: React.CSSProperties = {
  height: '36px',
  width: '36px',
};

export const LeftToolbar = () => {
  return (
    <aside className="w-16 bg-background border-r flex flex-col items-center py-4 gap-2 shrink-0">
      <div className="flex flex-col gap-2">
        <Button variant="ghost" style={buttonStyle}>
          <BarChart style={iconStyle} />
        </Button>
        <Button variant="ghost" style={buttonStyle} className="text-muted-foreground">
          <GitPullRequestArrow style={iconStyle} />
        </Button>
        <Button variant="ghost" style={buttonStyle} className="text-muted-foreground">
          <TrendingUp style={iconStyle} />
        </Button>
        <Button variant="ghost" style={buttonStyle} className="text-muted-foreground">
          <SlidersHorizontal style={iconStyle} />
        </Button>
      </div>

      <div className="mt-auto flex flex-col gap-2">
        <Button variant="ghost" style={buttonStyle} className="text-muted-foreground">
          <Settings style={iconStyle} />
        </Button>
        <Button variant="ghost" style={buttonStyle} className="text-muted-foreground">
          <HelpCircle style={iconStyle} />
        </Button>
      </div>
    </aside>
  );
};