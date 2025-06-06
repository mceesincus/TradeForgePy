// src/store/appStore.ts
import { create } from 'zustand';

interface AppState {
  theme: 'dark' | 'light';
  voiceAnnouncementsEnabled: boolean;
  botModeEnabled: boolean;
  toggleTheme: () => void;
  setVoiceAnnouncementsEnabled: (enabled: boolean) => void;
  setBotModeEnabled: (enabled: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'dark', // Default theme
  voiceAnnouncementsEnabled: false,
  botModeEnabled: false,
  toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
  setVoiceAnnouncementsEnabled: (enabled) => set({ voiceAnnouncementsEnabled: enabled }),
  setBotModeEnabled: (enabled) => set({ botModeEnabled: enabled }),
}));