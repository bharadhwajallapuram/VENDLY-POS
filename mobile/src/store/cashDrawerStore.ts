/**
 * Cash Drawer Store - Manage register sessions and cash movements
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface CashMovement {
  id: string;
  type: 'cash_in' | 'cash_out' | 'sale' | 'refund' | 'float' | 'drop';
  amount: number;
  reason?: string;
  timestamp: Date;
  userId: string;
  userName: string;
}

export interface RegisterSession {
  id: string;
  status: 'open' | 'closed';
  openedAt: Date;
  closedAt?: Date;
  openedBy: string;
  openedByName: string;
  closedBy?: string;
  closedByName?: string;
  openingFloat: number;
  expectedCash: number;
  actualCash?: number;
  variance?: number;
  movements: CashMovement[];
  totalSales: number;
  totalRefunds: number;
  totalCashIn: number;
  totalCashOut: number;
  transactionCount: number;
}

interface CashDrawerState {
  currentSession: RegisterSession | null;
  sessionHistory: RegisterSession[];
  
  // Actions
  openRegister: (openingFloat: number, userId: string, userName: string) => void;
  closeRegister: (actualCash: number, userId: string, userName: string) => void;
  addCashMovement: (type: CashMovement['type'], amount: number, reason?: string) => void;
  recordSale: (amount: number, paymentMethod: string) => void;
  recordRefund: (amount: number) => void;
  getExpectedCash: () => number;
  clearHistory: () => void;
}

export const useCashDrawerStore = create<CashDrawerState>()(
  persist(
    (set, get) => ({
      currentSession: null,
      sessionHistory: [],

      openRegister: (openingFloat, userId, userName) => {
        const session: RegisterSession = {
          id: `REG-${Date.now()}`,
          status: 'open',
          openedAt: new Date(),
          openedBy: userId,
          openedByName: userName,
          openingFloat,
          expectedCash: openingFloat,
          movements: [
            {
              id: `MOV-${Date.now()}`,
              type: 'float',
              amount: openingFloat,
              reason: 'Opening float',
              timestamp: new Date(),
              userId,
              userName,
            },
          ],
          totalSales: 0,
          totalRefunds: 0,
          totalCashIn: 0,
          totalCashOut: 0,
          transactionCount: 0,
        };

        set({ currentSession: session });
      },

      closeRegister: (actualCash, userId, userName) => {
        const { currentSession, sessionHistory } = get();
        if (!currentSession) return;

        const expectedCash = get().getExpectedCash();
        const variance = actualCash - expectedCash;

        const closedSession: RegisterSession = {
          ...currentSession,
          status: 'closed',
          closedAt: new Date(),
          closedBy: userId,
          closedByName: userName,
          actualCash,
          expectedCash,
          variance,
        };

        set({
          currentSession: null,
          sessionHistory: [closedSession, ...sessionHistory].slice(0, 30), // Keep last 30 sessions
        });
      },

      addCashMovement: (type, amount, reason) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const movement: CashMovement = {
          id: `MOV-${Date.now()}`,
          type,
          amount,
          reason,
          timestamp: new Date(),
          userId: currentSession.openedBy,
          userName: currentSession.openedByName,
        };

        const updates: Partial<RegisterSession> = {
          movements: [...currentSession.movements, movement],
        };

        if (type === 'cash_in' || type === 'drop') {
          updates.totalCashIn = currentSession.totalCashIn + amount;
        } else if (type === 'cash_out') {
          updates.totalCashOut = currentSession.totalCashOut + amount;
        }

        set({
          currentSession: { ...currentSession, ...updates },
        });
      },

      recordSale: (amount, paymentMethod) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const updates: Partial<RegisterSession> = {
          totalSales: currentSession.totalSales + amount,
          transactionCount: currentSession.transactionCount + 1,
        };

        if (paymentMethod === 'cash') {
          const movement: CashMovement = {
            id: `MOV-${Date.now()}`,
            type: 'sale',
            amount,
            timestamp: new Date(),
            userId: currentSession.openedBy,
            userName: currentSession.openedByName,
          };
          updates.movements = [...currentSession.movements, movement];
        }

        set({
          currentSession: { ...currentSession, ...updates },
        });
      },

      recordRefund: (amount) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const movement: CashMovement = {
          id: `MOV-${Date.now()}`,
          type: 'refund',
          amount: -amount,
          timestamp: new Date(),
          userId: currentSession.openedBy,
          userName: currentSession.openedByName,
        };

        set({
          currentSession: {
            ...currentSession,
            totalRefunds: currentSession.totalRefunds + amount,
            movements: [...currentSession.movements, movement],
          },
        });
      },

      getExpectedCash: () => {
        const { currentSession } = get();
        if (!currentSession) return 0;

        return (
          currentSession.openingFloat +
          currentSession.movements
            .filter(m => ['sale', 'cash_in', 'drop'].includes(m.type))
            .reduce((sum, m) => sum + m.amount, 0) -
          currentSession.movements
            .filter(m => ['refund', 'cash_out'].includes(m.type))
            .reduce((sum, m) => sum + Math.abs(m.amount), 0)
        );
      },

      clearHistory: () => {
        set({ sessionHistory: [] });
      },
    }),
    {
      name: 'vendly-cash-drawer',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

export default useCashDrawerStore;
