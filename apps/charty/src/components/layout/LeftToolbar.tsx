// src/components/layout/LeftToolbar.tsx (Recommended Refactor)
import React from 'react';
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Settings,
  HelpCircle,
  GitPullRequestArrow,
  TrendingUp,
  SlidersHorizontal,
} from "lucide-react";

export const LeftToolbar = () => { // Removed React.FC for consistency with modern practice
  // All inline styles and objects have been removed.
  // Styling is now 100% handled by Tailwind utility classes.

  return (
    // Use Tailwind's 'w-16' class for 64px width.
    <aside
      className="w-16 bg-background border-r flex flex-col items-center py-4 gap-2 shrink-0"
    >
      <div className="flex flex-col gap-2">
        {/* Use Tailwind classes for sizing: w-14 (56px) and h-14 (56px) */}
        {/* The 'lucide' icons can be sized directly with classes as well. */}
        <Button variant="ghost" size="icon" className="w-14 h-14">
          <BarChart className="w-8 h-8" />
        </Button>
        <Button variant="ghost" size="icon" className="w-14 h-14 text-muted-foreground">
          <GitPullRequestArrow className="w-8 h-8" />
        </Button>
        <Button variant="ghost" size="icon" className="w-14 h-14 text-muted-foreground">
          <TrendingUp className="w-8 h-8" />
        </Button>
        <Button variant="ghost" size="icon" className="w-14 h-14 text-muted-foreground">
          <SlidersHorizontal className="w-8 h-8" />
        </Button>
      </div>

      <div className="mt-auto flex flex-col gap-2">
        <Button variant="ghost" size="icon" className="w-14 h-14 text-muted-foreground">
          <Settings className="w-8 h-8" />
        </Button>
        <Button variant="ghost" size="icon" className="w-14 h-14 text-muted-foreground">
          <HelpCircle className="w-8 h-8" />
        </Button>
      </div>
    </aside>
  );
};