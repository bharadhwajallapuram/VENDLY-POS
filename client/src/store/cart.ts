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
}

interface CartState {
  lines: CartLine[];
  add: (line: CartLine) => void;
  inc: (variantId: string) => void;
  dec: (variantId: string) => void;
  remove: (variantId: string) => void;
  clear: () => void;
  subtotal: () => number;
  itemCount: () => number;
}

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      lines: [],

      add: (line) =>
        set((state) => {
          const existing = state.lines.findIndex((l) => l.variantId === line.variantId);
          if (existing > -1) {
            const updated = [...state.lines];
            updated[existing] = {
              ...updated[existing],
              qty: updated[existing].qty + line.qty,
            };
            return { lines: updated };
          }
          return { lines: [line, ...state.lines] };
        }),

      inc: (variantId) =>
        set((state) => ({
          lines: state.lines.map((l) =>
            l.variantId === variantId ? { ...l, qty: l.qty + 1 } : l
          ),
        })),

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

      subtotal: () => get().lines.reduce((sum, l) => sum + l.qty * l.priceCents, 0),

      itemCount: () => get().lines.reduce((sum, l) => sum + l.qty, 0),
    }),
    {
      name: 'vendly-cart',
    }
  )
);
