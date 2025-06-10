// src/components/layout/Footer.tsx
import React from 'react';

export const Footer = () => {
  return (
    <footer className="bg-background border-t h-10 flex items-center justify-center px-6 shrink-0">
      <p className="text-xs text-muted-foreground">
        © {new Date().getFullYear()} Trading App - Version 0.0.1
      </p>
    </footer>
  );
};