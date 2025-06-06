// src/store/tradingStore.ts
import { create } from 'zustand';

// --- Types ---
export type OrderSide = 'BUY' | 'SELL';
export type OrderType = 'Market' | 'Limit' | 'Stop';

export interface Position {
  symbol: string;
  quantity: number;
  entryPrice: number;
  side: OrderSide;
}

export interface Order {
  id: string;
  symbol: string;
  quantity: number;
  side: OrderSide;
  type: OrderType;
  price?: number;
}

// --- State and Actions ---
interface TradingState {
  // Order Entry State
  symbol: string;
  orderType: OrderType;
  quantity: number;
  limitPrice?: number;
  
  // Account State
  activePosition: Position | null;
  workingOrders: Order[];
  
  // Actions
  setSymbol: (symbol: string) => void;
  setOrderType: (type: OrderType) => void;
  setQuantity: (qty: number) => void;
  setLimitPrice: (price: number) => void;
  
  // Mock Trading Actions
  submitMarketOrder: (side: OrderSide) => void;
  closePosition: () => void;
  reversePosition: () => void;
  flattenAll: () => void;
}

// Mock a "last price" for calculating P/L
const mockLastPrices: { [key: string]: number } = {
  "ESM24": 5005.50,
  "NQM24": 18100.25,
};

export const useTradingStore = create<TradingState>((set, get) => ({
  // --- Initial State ---
  symbol: 'ESM24',
  orderType: 'Market',
  quantity: 1,
  limitPrice: undefined,
  activePosition: null,
  workingOrders: [],

  // --- Actions ---
  setSymbol: (symbol) => set({ symbol }),
  setOrderType: (type) => set({ orderType: type }),
  setQuantity: (qty) => set({ quantity: qty }),
  setLimitPrice: (price) => set({ limitPrice: price }),

  // --- Mock Trading Actions ---
  submitMarketOrder: (side) => {
    const { symbol, quantity, activePosition } = get();
    if (quantity <= 0) return; // Can't submit 0 qty order
    if (activePosition) {
        console.warn("Cannot open new position while one is active. Flatten first.");
        return;
    }
    
    // Simulate a market fill
    const fillPrice = mockLastPrices[symbol] || 5000;
    console.log(`Simulating ${side} order for ${quantity} ${symbol} @ ${fillPrice}`);
    set({
      activePosition: {
        symbol,
        quantity,
        side,
        entryPrice: fillPrice,
      },
    });
  },

  closePosition: () => {
    const { activePosition } = get();
    if (!activePosition) return;
    
    console.log(`Simulating closing position for ${activePosition.symbol}`);
    set({ activePosition: null });
  },

  reversePosition: () => {
    const { activePosition } = get();
    if (!activePosition) return;

    console.log(`Simulating reversing position for ${activePosition.symbol}`);
    const newSide = activePosition.side === 'BUY' ? 'SELL' : 'BUY';
    set((state) => ({
      activePosition: {
        ...state.activePosition!,
        side: newSide,
      },
    }));
  },

  flattenAll: () => {
    console.log("Simulating FLATTEN ALL");
    set({ activePosition: null, workingOrders: [] });
  },
}));