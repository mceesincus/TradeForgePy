// src/components/layout/MainArea.tsx
import React from 'react';

interface MainAreaProps {
  children?: React.ReactNode;
}

// This component just passes children through. All layout is in App.tsx.
export const MainArea: React.FC<MainAreaProps> = ({ children }) => {
  return <>{children}</>;
};