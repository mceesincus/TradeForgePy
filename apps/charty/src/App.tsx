// src/App.tsx

import { Header } from './components/layout/Header';
// import { Footer } from './components/layout/Footer';
import { Toaster } from 'sonner';
import { ChartContainer } from './features/charting/ChartContainer';
import { LeftToolbar } from './components/layout/LeftToolbar';
import { RightOrderPanel } from './components/layout/RightOrderPanel';
import { ThemeProvider } from './components/shared/ThemeProvider';
import { ChartToolbar } from './components/layout/ChartToolbar';

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="trading-app-theme">
      <div className="flex flex-col h-screen bg-background text-foreground overflow-hidden">
        <Header />

        <main className="flex-grow grid grid-cols-[auto_1fr_auto] overflow-hidden">
          <LeftToolbar />

          <div className="flex flex-col h-full overflow-hidden">
            <ChartToolbar />
            <div className="flex-grow grid grid-cols-1 lg:grid-cols-7 gap-2 p-2 overflow-hidden">
              <ChartContainer className="lg:col-span-2" timeframe="60m" />
              <ChartContainer className="lg:col-span-2" timeframe="15m" />
              <ChartContainer className="lg:col-span-3" timeframe="5m" />
            </div>
          </div>

          <RightOrderPanel />
        </main>

        <Toaster richColors position="top-right" />
      </div>
    </ThemeProvider>
  );
}

export default App;