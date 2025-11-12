import { create } from "zustand";

export type Line = { variantId: string; name: string; qty: number; priceCents: number };
export type CartState = {
  lines: Line[];
  add: (_l: Line) => void;
  inc: (_variantId: string) => void;
  dec: (_variantId: string) => void;
  remove: (_variantId: string) => void;
  clear: () => void;
  subtotal: () => number;
};

export const useCart = create<CartState>((set, get) => ({
  lines: [],
  add: (l) => set((s) => {
    const i = s.lines.findIndex((x) => x.variantId === l.variantId);
    if (i > -1) {
      const copy = [...s.lines];
      copy[i] = { ...copy[i], qty: copy[i].qty + l.qty };
      return { lines: copy };
    }
    return { lines: [l, ...s.lines] };
  }),
  inc: (id) => set((s) => ({ lines: s.lines.map((x) => (x.variantId === id ? { ...x, qty: x.qty + 1 } : x)) })),
  dec: (id) => set((s) => ({ lines: s.lines.map((x) => (x.variantId === id ? { ...x, qty: Math.max(1, x.qty - 1) } : x)) })),
  remove: (id) => set((s) => ({ lines: s.lines.filter((x) => x.variantId !== id) })),
  clear: () => set({ lines: [] }),
  subtotal: () => get().lines.reduce((sum, l) => sum + l.qty * l.priceCents, 0),
}));