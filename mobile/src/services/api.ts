/**
 * API Service - Handles all HTTP requests to the backend
 */

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Token getter function to avoid circular dependency
let getAuthToken: (() => string | null) | null = null;

export function setAuthTokenGetter(getter: () => string | null) {
  getAuthToken = getter;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: any;
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

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
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
  async getProducts(params?: { search?: string; category?: string; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append('search', params.search);
    if (params?.category) searchParams.append('category', params.category);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const query = searchParams.toString();
    return this.request(`/products${query ? `?${query}` : ''}`);
  }

  async getProduct(id: number) {
    return this.request(`/products/${id}`);
  }

  async getProductByBarcode(barcode: string) {
    return this.request(`/products/barcode/${barcode}`);
  }

  async updateProduct(data: { id: number; [key: string]: any }) {
    return this.request(`/products/${data.id}`, {
      method: 'PATCH',
      body: data,
    });
  }

  async getCategories() {
    return this.request('/products/categories');
  }

  // ========== Inventory ==========
  async getInventory(storeId?: number) {
    const query = storeId ? `?store_id=${storeId}` : '';
    return this.request(`/inventory${query}`);
  }

  async updateInventory(data: { product_id: number; quantity: number; type: string; notes?: string }) {
    return this.request('/inventory/adjust', {
      method: 'POST',
      body: data,
    });
  }

  async getLowStockAlerts() {
    return this.request('/inventory/low-stock');
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
    return this.request(`/sales${query ? `?${query}` : ''}`);
  }

  async getSale(id: number) {
    return this.request(`/sales/${id}`);
  }

  // ========== Customers ==========
  async getCustomers(search?: string) {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.request(`/customers${query}`);
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

  async getSalesByHour(date?: string) {
    const query = date ? `?date=${date}` : '';
    return this.request(`/reports/sales-by-hour${query}`);
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
