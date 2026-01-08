/**
 * Auth Store - Zustand store for authentication
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService, setAuthTokenGetter } from '../services/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  loadStoredAuth: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await apiService.login(email, password);
          const token = response.access_token;
          
          // Fetch user details using the token
          const user = await apiService.getCurrentUser(token);
          
          set({
            isAuthenticated: true,
            user: user as User,
            token: token,
            isLoading: false,
          });

          return true;
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Login failed',
          });
          return false;
        }
      },

      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          token: null,
          error: null,
        });
      },

      checkAuth: async () => {
        const { token } = get();
        
        if (!token) {
          set({ isAuthenticated: false });
          return;
        }

        try {
          const user = await apiService.getCurrentUser(token) as User;
          set({ isAuthenticated: true, user });
        } catch {
          set({ isAuthenticated: false, token: null, user: null });
        }
      },

      clearError: () => set({ error: null }),

      loadStoredAuth: () => {
        const { token, user } = get();
        if (token && user) {
          set({ isAuthenticated: true, isLoading: false });
        } else {
          set({ isAuthenticated: false, isLoading: false });
        }
      },
    }),
    {
      name: 'vendly-auth',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);

// Register the token getter to break circular dependency
setAuthTokenGetter(() => useAuthStore.getState().token);
