/**
 * Cart Store - Zustand store for POS cart management
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface CartItem {
  id: number;
  product_id: number;
  name: string;
  sku: string;
  price: number;
  quantity: number;
  discount: number;
  barcode?: string;
  image_url?: string;
}

interface CartState {
  items: CartItem[];
  customerId: number | null;
  customerName: string | null;
  discount: number;
  taxRate: number;
  notes: string;

  // Computed values
  subtotal: number;
  discountAmount: number;
  taxAmount: number;
  total: number;
  itemCount: number;

  // Actions
  addItem: (product: Omit<CartItem, 'quantity' | 'discount'>) => void;
  removeItem: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  setItemDiscount: (productId: number, discount: number) => void;
  setCustomer: (id: number | null, name: string | null) => void;
  setCartDiscount: (discount: number) => void;
  setDiscount: (discount: number) => void; // Alias for setCartDiscount
  setNotes: (notes: string) => void;
  clearCart: () => void;
  calculateTotals: () => void;
}

const calculateTotals = (items: CartItem[], cartDiscount: number, taxRate: number) => {
  const subtotal = items.reduce((sum, item) => {
    const itemTotal = item.price * item.quantity;
    const itemDiscount = (itemTotal * item.discount) / 100;
    return sum + (itemTotal - itemDiscount);
  }, 0);

  const discountAmount = (subtotal * cartDiscount) / 100;
  const afterDiscount = subtotal - discountAmount;
  const taxAmount = (afterDiscount * taxRate) / 100;
  const total = afterDiscount + taxAmount;
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  return { subtotal, discountAmount, taxAmount, total, itemCount };
};

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      customerId: null,
      customerName: null,
      discount: 0,
      taxRate: 8.875, // Default NYC tax rate
      notes: '',
      subtotal: 0,
      discountAmount: 0,
      taxAmount: 0,
      total: 0,
      itemCount: 0,

      addItem: (product) => {
        const { items, discount, taxRate } = get();
        const existingIndex = items.findIndex(item => item.product_id === product.product_id);

        let newItems: CartItem[];
        if (existingIndex >= 0) {
          newItems = items.map((item, index) =>
            index === existingIndex
              ? { ...item, quantity: item.quantity + 1 }
              : item
          );
        } else {
          newItems = [...items, { ...product, quantity: 1, discount: 0 }];
        }

        const totals = calculateTotals(newItems, discount, taxRate);
        set({ items: newItems, ...totals });
      },

      removeItem: (productId) => {
        const { items, discount, taxRate } = get();
        const newItems = items.filter(item => item.product_id !== productId);
        const totals = calculateTotals(newItems, discount, taxRate);
        set({ items: newItems, ...totals });
      },

      updateQuantity: (productId, quantity) => {
        const { items, discount, taxRate } = get();
        
        if (quantity <= 0) {
          const newItems = items.filter(item => item.product_id !== productId);
          const totals = calculateTotals(newItems, discount, taxRate);
          set({ items: newItems, ...totals });
          return;
        }

        const newItems = items.map(item =>
          item.product_id === productId ? { ...item, quantity } : item
        );
        const totals = calculateTotals(newItems, discount, taxRate);
        set({ items: newItems, ...totals });
      },

      setItemDiscount: (productId, itemDiscount) => {
        const { items, discount, taxRate } = get();
        const newItems = items.map(item =>
          item.product_id === productId ? { ...item, discount: itemDiscount } : item
        );
        const totals = calculateTotals(newItems, discount, taxRate);
        set({ items: newItems, ...totals });
      },

      setCustomer: (id, name) => {
        set({ customerId: id, customerName: name });
      },

      setCartDiscount: (cartDiscount) => {
        const { items, taxRate } = get();
        const totals = calculateTotals(items, cartDiscount, taxRate);
        set({ discount: cartDiscount, ...totals });
      },

      // Alias for setCartDiscount
      setDiscount: (cartDiscount) => {
        const { items, taxRate } = get();
        const totals = calculateTotals(items, cartDiscount, taxRate);
        set({ discount: cartDiscount, ...totals });
      },

      setNotes: (notes) => set({ notes }),

      clearCart: () => {
        set({
          items: [],
          customerId: null,
          customerName: null,
          discount: 0,
          notes: '',
          subtotal: 0,
          discountAmount: 0,
          taxAmount: 0,
          total: 0,
          itemCount: 0,
        });
      },

      calculateTotals: () => {
        const { items, discount, taxRate } = get();
        const totals = calculateTotals(items, discount, taxRate);
        set(totals);
      },
    }),
    {
      name: 'vendly-cart',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        items: state.items,
        customerId: state.customerId,
        customerName: state.customerName,
        discount: state.discount,
        notes: state.notes,
      }),
    }
  )
);
