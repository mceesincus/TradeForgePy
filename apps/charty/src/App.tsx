// src/App.tsx
import { Header } from './components/layout/Header';
import { MainArea } from './components/layout/MainArea';
import { RightOrderPanel } from './components/layout/RightOrderPanel';
import { Footer } from './components/layout/Footer';
import { Toaster } from "@/components/ui/toaster";
import { ChartContainer } from './features/charting/ChartContainer';

function App() {
  return (
    // The screen is a flex column.
    <div className="flex flex-col h-screen antialiased bg-background text-foreground">
      
      {/* Header has a fixed height (h-16 = 4rem = 64px) */}
      <Header />

      {/* 
        This is the main content row. 
        - It's a flex container.
        - 'flex-grow' makes it take up the remaining space.
        - 'overflow-hidden' is crucial to prevent scrollbars from appearing on this container.
      */}
      <div className="flex flex-grow overflow-hidden">
        
        {/* 
          Main Charting Area.
          - 'flex-grow' allows it to expand.
          - 'flex flex-col' to stack its children vertically.
          - The children will be the padding and the grid itself.
        */}
        <div className="flex-grow flex flex-col">
            
            {/* 
              This is the grid container.
              - 'flex-grow' makes it take up all available vertical space inside its parent.
              - 'p-4' adds the padding.
            */}
            <div className="flex-grow grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
              {/* 
                Each ChartContainer will now correctly fill its grid cell,
                because the grid itself has a defined space to fill.
              */}
              <ChartContainer initialSymbol="/ES" initialTimeframe="30m" />
              <ChartContainer initialSymbol="/NQ" initialTimeframe="15m" />
              <ChartContainer initialSymbol="/RTY" initialTimeframe="5m" />
            </div>
        </div>

        {/* The Right Order Panel has a fixed width. */}
        <RightOrderPanel />
      </div>

      {/* Footer has a fixed height (h-10 = 2.5rem = 40px) */}
      <Footer />
      <Toaster />
    </div>
  );
}

export default App;