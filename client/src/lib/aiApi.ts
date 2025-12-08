import { apiFetch } from './api';

// 1. Forecast
export async function forecastSales(data: { product_id?: number; days: number }) {
  return apiFetch('/api/v1/ai/forecast', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 2. Anomaly
export async function detectAnomalies(data: { sales_data: { date: string; sales: number }[]; threshold?: number }) {
  return apiFetch('/api/v1/ai/anomaly', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 3. Recommend
export async function recommendProducts(data: { customer_id: number; n?: number }) {
  return apiFetch('/api/v1/ai/recommend', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 4. Price Suggest
export async function suggestPrice(data: { product_id: number }) {
  return apiFetch('/api/v1/ai/price-suggest', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 5. Ask
export async function askAnalytics(data: { question: string }) {
  return apiFetch('/api/v1/ai/ask', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 6. Voice
export async function voiceCommand(data: { command: string }) {
  return apiFetch('/api/v1/ai/voice', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
