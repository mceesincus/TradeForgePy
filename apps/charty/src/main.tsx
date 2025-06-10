// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { ThemeProvider } from "@/components/shared/ThemeProvider";

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="very-dark" // Let's default to your new theme
      enableSystem={false}     // Disable system preference to avoid conflicts
      disableTransitionOnChange
      themes={['light', 'dark', 'very-dark']}
    >
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);