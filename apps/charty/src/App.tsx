// src/App.tsx
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { Toaster } from "@/components/ui/toaster";
import { ChartContainer } from './features/charting/ChartContainer';
import { LeftToolbar } from './components/layout/LeftToolbar'; // Import the new toolbar

function App() {
  return (
    <div className="flex flex-col h-screen antialiased bg-background text-foreground">
      <Header />
      {/* The main row now contains the LeftToolbar and the main content area */}
      <div className="flex flex-grow overflow-hidden">
        
        {/* ADD THE NEW LEFT TOOLBAR */}
        <LeftToolbar />

        {/* This is the main content area for the charts */}
        <div className="flex-grow flex flex-col">
          <div className="flex-grow grid grid-cols-1 lg:grid-cols-10 gap-4 p-4">
            <div className="lg:col-span-3">
              <ChartContainer initialSymbol="/ES" initialTimeframe="30m" />
            </div>
            <div className="lg:col-span-3">
              <ChartContainer initialSymbol="/NQ" initialTimeframe="15m" />
            </div>
            <div className="lg:col-span-4">
              <ChartContainer initialSymbol="/RTY" initialTimeframe="5m" />
            </div>
          </div>
        </div>

        {/* The RightOrderPanel is no longer here. Its content is rendered inside the Sheet,
            which is triggered from the LeftToolbar. */}

      </div>
      <Footer />
      <Toaster />
    </div>
  );
}

export default App;