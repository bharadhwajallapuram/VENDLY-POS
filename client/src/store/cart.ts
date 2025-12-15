// ===========================================
// Vendly POS - Cart Store (Zustand)
// ===========================================

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface CartLine {
  variantId: string;
  name: string;
  qty: number;
  priceCents: number;
  availableStock?: number; // Track available stock for validation
}

interface CartState {
  lines: CartLine[];
  add: (line: CartLine) => boolean; // Returns true if added, false if exceeds stock
  inc: (variantId: string) => boolean; // Returns true if incremented, false if exceeds stock
  dec: (variantId: string) => void;
  remove: (variantId: string) => void;
  clear: () => void;
  updateStock: (variantId: string, newStock: number) => void; // Update available stock for a cart line
  subtotal: () => number;
  itemCount: () => number;
}

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      lines: [],

      add: (line) => {
        const state = get();
        const existing = state.lines.find((l) => l.variantId === line.variantId);
        const currentQty = existing?.qty || 0;
        const maxStock = line.availableStock || Infinity;

        // Check if adding would exceed stock
        if (currentQty + line.qty > maxStock) {
          return false; // Exceeded stock
        }

        set((s) => {
          const existingIdx = s.lines.findIndex((l) => l.variantId === line.variantId);
          if (existingIdx > -1) {
            const updated = [...s.lines];
            updated[existingIdx] = {
              ...updated[existingIdx],
              qty: updated[existingIdx].qty + line.qty,
            };
            return { lines: updated };
          }
          return { lines: [line, ...s.lines] };
        });

        return true; // Successfully added
      },

      inc: (variantId) => {
        const state = get();
        const line = state.lines.find((l) => l.variantId === variantId);
        
        if (!line) return false;

        const maxStock = line.availableStock || Infinity;
        
        // Check if incrementing would exceed stock
        if (line.qty + 1 > maxStock) {
          return false; // Exceeded stock
        }

        set((s) => ({
          lines: s.lines.map((l) =>
            l.variantId === variantId ? { ...l, qty: l.qty + 1 } : l
          ),
        }));

        return true; // Successfully incremented
      },

      dec: (variantId) =>
        set((state) => ({
          lines: state.lines.map((l) =>
            l.variantId === variantId ? { ...l, qty: Math.max(1, l.qty - 1) } : l
          ),
        })),

      remove: (variantId) =>
        set((state) => ({
          lines: state.lines.filter((l) => l.variantId !== variantId),
        })),

      clear: () => set({ lines: [] }),

      updateStock: (variantId, newStock) =>
        set((state) => ({
          lines: state.lines.map((l) =>
            l.variantId === variantId ? { ...l, availableStock: newStock } : l
          ),
        })),

      subtotal: () => get().lines.reduce((sum, l) => sum + l.qty * l.priceCents, 0),

      itemCount: () => get().lines.reduce((sum, l) => sum + l.qty, 0),
    }),
    {
      name: 'vendly-cart',
    }
  )
);
