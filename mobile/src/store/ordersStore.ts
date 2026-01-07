/**
 * Orders Store - Manage held/parked orders
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface OrderItem {
  id: number;
  product_id: number;
  name: string;
  sku: string;
  price: number;
  quantity: number;
  discount: number;
  barcode?: string;
}

export interface HeldOrder {
  id: string;
  name: string;
  items: OrderItem[];
  customerId?: number;
  customerName?: string;
  subtotal: number;
  discount: number;
  taxAmount: number;
  total: number;
  notes?: string;
  createdAt: Date;
  createdBy: string;
  createdByName: string;
}

interface OrdersState {
  heldOrders: HeldOrder[];
  
  // Actions
  holdOrder: (order: Omit<HeldOrder, 'id' | 'createdAt'>) => string;
  recallOrder: (orderId: string) => HeldOrder | null;
  deleteHeldOrder: (orderId: string) => void;
  updateHeldOrder: (orderId: string, updates: Partial<HeldOrder>) => void;
  getHeldOrderCount: () => number;
  clearAllHeldOrders: () => void;
}

export const useOrdersStore = create<OrdersState>()(
  persist(
    (set, get) => ({
      heldOrders: [],

      holdOrder: (order) => {
        const id = `ORD-${Date.now()}`;
        const heldOrder: HeldOrder = {
          ...order,
          id,
          createdAt: new Date(),
        };

        set(state => ({
          heldOrders: [...state.heldOrders, heldOrder],
        }));

        return id;
      },

      recallOrder: (orderId) => {
        const { heldOrders } = get();
        const order = heldOrders.find(o => o.id === orderId);
        
        if (order) {
          set(state => ({
            heldOrders: state.heldOrders.filter(o => o.id !== orderId),
          }));
          return order;
        }
        
        return null;
      },

      deleteHeldOrder: (orderId) => {
        set(state => ({
          heldOrders: state.heldOrders.filter(o => o.id !== orderId),
        }));
      },

      updateHeldOrder: (orderId, updates) => {
        set(state => ({
          heldOrders: state.heldOrders.map(order =>
            order.id === orderId ? { ...order, ...updates } : order
          ),
        }));
      },

      getHeldOrderCount: () => {
        return get().heldOrders.length;
      },

      clearAllHeldOrders: () => {
        set({ heldOrders: [] });
      },
    }),
    {
      name: 'vendly-held-orders',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

export default useOrdersStore;
