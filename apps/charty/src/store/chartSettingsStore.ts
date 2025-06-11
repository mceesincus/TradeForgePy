// src/store/chartSettingsStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Define the shape of our settings state
export interface ChartSettings {
  barSpacing: number;
  upColor: string;
  downColor: string;
  borderUpColor: string;
  borderDownColor: string;
  wickUpColor: string;
  wickDownColor: string;
}

// Define the shape of the store, including actions
interface ChartSettingsState extends ChartSettings {
  setBarSpacing: (spacing: number) => void;
  setColor: (key: keyof Omit<ChartSettings, 'barSpacing'>, color: string) => void;
  resetToDefaults: () => void;
}

// Define the default settings
const defaultSettings: ChartSettings = {
  barSpacing: 18,
  upColor: 'rgba(34, 197, 94, 0.3)',   // Low-contrast green fill
  downColor: 'rgba(239, 68, 68, 0.3)', // Low-contrast red fill
  borderUpColor: '#22c55e',            // Solid green border
  borderDownColor: '#ef4444',          // Solid red border
  wickUpColor: '#22c55e',              // Solid green wick
  wickDownColor: '#ef4444',            // Solid red wick
};

export const useChartSettingsStore = create<ChartSettingsState>()(
  // Use the 'persist' middleware to save the user's settings to localStorage
  persist(
    (set) => ({
      ...defaultSettings,
      setBarSpacing: (spacing) => set({ barSpacing: spacing }),
      setColor: (key, color) => set({ [key]: color }),
      resetToDefaults: () => set(defaultSettings),
    }),
    {
      name: 'chart-settings-storage', // The key to use in localStorage
    }
  )
);