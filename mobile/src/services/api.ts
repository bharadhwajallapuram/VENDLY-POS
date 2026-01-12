/**
 * API Service - Handles all HTTP requests to the backend
 */
import { Platform } from 'react-native';

// For web use localhost, for Android emulator use 10.0.2.2
const getApiBaseUrl = () => {
  if (Platform.OS === 'web') {
    return 'http://localhost:8000/api/v1';
  }
  // Android emulator: 10.0.2.2 maps to host machine's localhost
  return process.env.EXPO_PUBLIC_API_URL || 'http://10.0.2.2:8000/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

// Token getter function to avoid circular dependency
let getAuthToken: (() => string | null) | null = null;
// Callback to clear auth on 401
let onAuthFailure: (() => void) | null = null;

export function setAuthTokenGetter(getter: () => string | null) {
  getAuthToken = getter;
}

export function setAuthFailureHandler(handler: () => void) {
  onAuthFailure = handler;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  requiresAuth?: boolean;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, requiresAuth = true } = options;

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (requiresAuth) {
      const token = getAuthToken?.();
      if (token) {
        requestHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      
      // Handle 401 - invalid/expired token
      if (response.status === 401 && requiresAuth) {
        onAuthFailure?.();
      }
      
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  }

  // ========== Auth ==========
  async login(email: string, password: string) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  async getCurrentUser(token: string) {
    return this.request('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
  }

  // ========== Products ==========
  async getProducts(params?: { search?: string; category_id?: number; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append('q', params.search);
    if (params?.category_id) searchParams.append('category_id', params.category_id.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('skip', params.offset.toString());

    const query = searchParams.toString();
    const response = await this.request(`/products${query ? `?${query}` : ''}`);
    // API returns { items: [...], Count: n } - extract items array
    if (response && typeof response === 'object' && 'items' in (response as object)) {
      return (response as { items: unknown[] }).items;
    }
    // Fallback for direct array response
    return Array.isArray(response) ? response : [];
  }

  async getProduct(id: number) {
    return this.request(`/products/${id}`);
  }

  async getProductByBarcode(barcode: string) {
    return this.request(`/products/barcode/${barcode}`);
  }

  async updateProduct(data: { id: number; [key: string]: unknown }) {
    return this.request(`/products/${data.id}`, {
      method: 'PATCH',
      body: data,
    });
  }

  async getCategories() {
    const response = await this.request('/categories');
    // Backend returns array of category objects, extract names for UI
    if (Array.isArray(response)) {
      return (response as Array<{ id: number; name: string }>).map((cat) => cat.name);
    }
    return [];
  }

  async getCategoriesWithIds(): Promise<Array<{ id: number; name: string; description?: string }>> {
    const response = await this.request('/categories');
    // Return full category objects with id and name
    if (Array.isArray(response)) {
      return response as Array<{ id: number; name: string; description?: string }>;
    }
    return [];
  }

  // ========== Inventory ==========
  async getInventory(storeId?: number) {
    // Get products with stock quantities - transform to inventory items format
    const query = storeId ? `?store_id=${storeId}&limit=500` : '?limit=500';
    const response = await this.request(`/products${query}`);
    
    // Extract items from paginated response
    let products: Array<{ id: number; name: string; sku: string; stock_quantity: number; price: number; min_quantity?: number; category?: string }> = [];
    if (response && typeof response === 'object' && 'items' in (response as object)) {
      products = (response as { items: typeof products }).items;
    } else if (Array.isArray(response)) {
      products = response;
    }
    
    // Transform to inventory item format expected by InventoryScreen
    return products.map((p) => ({
      id: p.id,
      product_id: p.id,
      product_name: p.name,
      sku: p.sku || '',
      quantity: p.stock_quantity || 0,
      min_quantity: p.min_quantity || 10,
      price: p.price || 0,
      category: p.category || 'Uncategorized',
    }));
  }

  async getInventorySummary() {
    return this.request('/inventory/summary');
  }

  async updateInventory(data: { product_id: number; quantity: number; type: string; notes?: string }) {
    return this.request('/inventory/adjust', {
      method: 'POST',
      body: data,
    });
  }

  async getLowStockAlerts() {
    const response = await this.request('/inventory/low-stock');
    if (response && typeof response === 'object' && 'items' in (response as object)) {
      return (response as { items: unknown[] }).items;
    }
    return Array.isArray(response) ? response : [];
  }

  // ========== Sales ==========
  async createSale(data: {
    items: Array<{ product_id: number; quantity: number; price: number; discount?: number }>;
    customer_id?: number;
    payment_method: string;
    discount?: number;
    notes?: string;
  }) {
    return this.request('/sales', {
      method: 'POST',
      body: data,
    });
  }

  async getSales(params?: { date?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.date) searchParams.append('date', params.date);
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const query = searchParams.toString();
    const response = await this.request(`/sales${query ? `?${query}` : ''}`);
    // Extract items array if paginated
    if (response && typeof response === 'object' && 'items' in (response as object)) {
      return (response as { items: unknown[] }).items;
    }
    return Array.isArray(response) ? response : [];
  }

  async getSale(id: number) {
    return this.request(`/sales/${id}`);
  }

  // ========== Customers ==========
  async getCustomers(search?: string) {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    const response = await this.request(`/customers${query}`);
    if (response && typeof response === 'object' && 'items' in (response as object)) {
      return (response as { items: unknown[] }).items;
    }
    return Array.isArray(response) ? response : [];
  }

  async getCustomer(id: number) {
    return this.request(`/customers/${id}`);
  }

  async createCustomer(data: { name: string; email?: string; phone?: string }) {
    return this.request('/customers', {
      method: 'POST',
      body: data,
    });
  }

  // ========== Reports ==========
  async getDailySummary(date?: string) {
    const query = date ? `?date=${date}` : '';
    return this.request(`/reports/daily-summary${query}`);
  }

  async getReportSummary(startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const query = params.toString() ? `?${params}` : '';
    return this.request(`/reports/summary${query}`);
  }

  async getZReport(reportDate?: string) {
    const query = reportDate ? `?report_date=${reportDate}` : '';
    return this.request(`/reports/z-report${query}`);
  }

  async reconcileCash(actualCash: number, reportDate?: string, notes?: string) {
    const params = new URLSearchParams();
    if (reportDate) params.append('report_date', reportDate);
    const query = params.toString() ? `?${params}` : '';
    return this.request(`/reports/z-report/reconcile${query}`, {
      method: 'POST',
      body: { actual_cash: actualCash, notes },
    });
  }

  async getSalesSummary(reportDate?: string) {
    const query = reportDate ? `?report_date=${reportDate}` : '';
    return this.request(`/reports/sales-summary${query}`);
  }

  // ========== Stores ==========
  async getStores() {
    return this.request('/stores');
  }

  async getCurrentStore() {
    return this.request('/stores/current');
  }

  async setCurrentStore(storeId: number) {
    return this.request(`/stores/${storeId}/set-current`, {
      method: 'POST',
    });
  }

  // ========== Push Notifications ==========
  async registerPushToken(token: string, platform: 'ios' | 'android') {
    return this.request('/notifications/register', {
      method: 'POST',
      body: { token, platform },
    });
  }
}

export const apiService = new ApiService();
