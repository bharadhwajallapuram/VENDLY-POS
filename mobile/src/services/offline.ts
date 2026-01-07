/**
 * Offline Service - Handles local storage and offline data management
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  PRODUCTS: 'vendly_products_cache',
  CUSTOMERS: 'vendly_customers_cache',
  CATEGORIES: 'vendly_categories_cache',
  SETTINGS: 'vendly_settings_cache',
  CACHE_TIMESTAMPS: 'vendly_cache_timestamps',
};

interface CacheTimestamps {
  products?: string;
  customers?: string;
  categories?: string;
  settings?: string;
}

class OfflineService {
  private cacheExpiry = 24 * 60 * 60 * 1000; // 24 hours

  // ========== Generic Cache Methods ==========
  private async setCache<T>(key: string, data: T): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(data));
      await this.updateCacheTimestamp(key);
    } catch (error) {
      console.error(`Failed to cache ${key}:`, error);
    }
  }

  private async getCache<T>(key: string): Promise<T | null> {
    try {
      const data = await AsyncStorage.getItem(key);
      if (!data) return null;

      // Check if cache is expired
      const isExpired = await this.isCacheExpired(key);
      if (isExpired) {
        await AsyncStorage.removeItem(key);
        return null;
      }

      return JSON.parse(data);
    } catch (error) {
      console.error(`Failed to get cache ${key}:`, error);
      return null;
    }
  }

  private async updateCacheTimestamp(key: string): Promise<void> {
    try {
      const timestampsStr = await AsyncStorage.getItem(KEYS.CACHE_TIMESTAMPS);
      const timestamps: CacheTimestamps = timestampsStr ? JSON.parse(timestampsStr) : {};
      
      const keyName = Object.keys(KEYS).find(k => KEYS[k as keyof typeof KEYS] === key)?.toLowerCase();
      if (keyName) {
        (timestamps as any)[keyName] = new Date().toISOString();
      }
      
      await AsyncStorage.setItem(KEYS.CACHE_TIMESTAMPS, JSON.stringify(timestamps));
    } catch (error) {
      console.error('Failed to update cache timestamp:', error);
    }
  }

  private async isCacheExpired(key: string): Promise<boolean> {
    try {
      const timestampsStr = await AsyncStorage.getItem(KEYS.CACHE_TIMESTAMPS);
      if (!timestampsStr) return true;

      const timestamps: CacheTimestamps = JSON.parse(timestampsStr);
      const keyName = Object.keys(KEYS).find(k => KEYS[k as keyof typeof KEYS] === key)?.toLowerCase();
      
      if (!keyName) return true;
      
      const timestamp = (timestamps as any)[keyName];
      if (!timestamp) return true;

      const cacheTime = new Date(timestamp).getTime();
      const now = Date.now();
      
      return now - cacheTime > this.cacheExpiry;
    } catch {
      return true;
    }
  }

  // ========== Products ==========
  async cacheProducts(products: any[]): Promise<void> {
    await this.setCache(KEYS.PRODUCTS, products);
  }

  async getCachedProducts(): Promise<any[] | null> {
    return this.getCache(KEYS.PRODUCTS);
  }

  async searchCachedProducts(query: string): Promise<any[]> {
    const products = await this.getCachedProducts();
    if (!products) return [];

    const lowerQuery = query.toLowerCase();
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(lowerQuery) ||
        p.sku?.toLowerCase().includes(lowerQuery) ||
        p.barcode?.includes(query)
    );
  }

  async getCachedProductByBarcode(barcode: string): Promise<any | null> {
    const products = await this.getCachedProducts();
    if (!products) return null;
    return products.find((p) => p.barcode === barcode) || null;
  }

  // ========== Customers ==========
  async cacheCustomers(customers: any[]): Promise<void> {
    await this.setCache(KEYS.CUSTOMERS, customers);
  }

  async getCachedCustomers(): Promise<any[] | null> {
    return this.getCache(KEYS.CUSTOMERS);
  }

  async searchCachedCustomers(query: string): Promise<any[]> {
    const customers = await this.getCachedCustomers();
    if (!customers) return [];

    const lowerQuery = query.toLowerCase();
    return customers.filter(
      (c) =>
        c.name.toLowerCase().includes(lowerQuery) ||
        c.email?.toLowerCase().includes(lowerQuery) ||
        c.phone?.includes(query)
    );
  }

  // ========== Categories ==========
  async cacheCategories(categories: any[]): Promise<void> {
    await this.setCache(KEYS.CATEGORIES, categories);
  }

  async getCachedCategories(): Promise<any[] | null> {
    return this.getCache(KEYS.CATEGORIES);
  }

  // ========== Settings ==========
  async cacheSettings(settings: any): Promise<void> {
    await this.setCache(KEYS.SETTINGS, settings);
  }

  async getCachedSettings(): Promise<any | null> {
    return this.getCache(KEYS.SETTINGS);
  }

  // ========== Utility ==========
  async clearAllCaches(): Promise<void> {
    try {
      await AsyncStorage.multiRemove(Object.values(KEYS));
    } catch (error) {
      console.error('Failed to clear caches:', error);
    }
  }

  async getCacheStatus(): Promise<Record<string, { cached: boolean; timestamp?: string }>> {
    try {
      const timestampsStr = await AsyncStorage.getItem(KEYS.CACHE_TIMESTAMPS);
      const timestamps: CacheTimestamps = timestampsStr ? JSON.parse(timestampsStr) : {};

      const status: Record<string, { cached: boolean; timestamp?: string }> = {};

      for (const [name, key] of Object.entries(KEYS)) {
        if (name === 'CACHE_TIMESTAMPS') continue;
        
        const data = await AsyncStorage.getItem(key);
        const keyName = name.toLowerCase();
        
        status[keyName] = {
          cached: data !== null,
          timestamp: (timestamps as any)[keyName],
        };
      }

      return status;
    } catch {
      return {};
    }
  }
}

export const offlineService = new OfflineService();
