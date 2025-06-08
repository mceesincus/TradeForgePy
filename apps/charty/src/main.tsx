// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { ThemeProvider } from "@/components/shared/ThemeProvider"

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="dark" // Set the default theme
      enableSystem
      disableTransitionOnChange
      themes={['light', 'dark', 'very-dark']} // Make our new theme available
    >
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)