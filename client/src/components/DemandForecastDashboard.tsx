'use client';

import React, { useState, useEffect } from 'react';
import { forecastSales } from '@/lib/aiApi';
import { Products } from '@/lib/api';

interface ForecastData {
  forecast: number[];
  confidence_intervals: {
    lower: number[];
    upper: number[];
  };
  model_used?: string;
  timestamp?: string;
  mape?: number;
}

interface Product {
  id: number;
  name: string;
  sku?: string;
}

export default function DemandForecastDashboard() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number>(1);
  const [forecastDays, setForecastDays] = useState<number>(7);
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Load products on mount
  useEffect(() => {
    const loadProducts = async () => {
      try {
        const productList = await Products.list();
        if (productList && productList.length > 0) {
          setProducts(productList);
          setSelectedProductId(productList[0].id);
        }
      } catch (err) {
        console.error('Failed to load products:', err);
      }
    };
    loadProducts();
  }, []);

  const handleGenerateForecast = async () => {
    setLoading(true);
    setError(null);
    setForecastData(null);

    try {
      const result = await forecastSales({
        product_id: selectedProductId,
        days: forecastDays,
      });
      setForecastData(result as ForecastData);
    } catch (err: any) {
      setError(err.message || 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  const selectedProduct = products.find((p) => p.id === selectedProductId);
  const dates = forecastData
    ? Array.from({ length: forecastDays }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() + i + 1);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      })
    : [];

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span>📊</span> Demand Forecast
        </h2>

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2">Product</label>
            <select
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(Number(e.target.value))}
              className="input w-full"
              disabled={loading}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.sku ? `(${p.sku})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Forecast Days</label>
            <select
              value={forecastDays}
              onChange={(e) => setForecastDays(Number(e.target.value))}
              className="input w-full"
              disabled={loading}
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
              <option value={90}>90 Days</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleGenerateForecast}
              disabled={loading || products.length === 0}
              className="btn btn-primary w-full"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span> Generating...
                </span>
              ) : (
                '🔮 Generate Forecast'
              )}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 mb-4">
            ⚠️ {error}
          </div>
        )}

        {/* Forecast Results */}
        {forecastData && forecastData.forecast && !loading && (
          <div className="space-y-4">
            {/* Summary Info */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="text-sm text-gray-600 mb-1">Product</div>
                <div className="text-lg font-semibold">{selectedProduct?.name}</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <div className="text-sm text-gray-600 mb-1">Forecast Model</div>
                <div className="text-lg font-semibold">
                  {forecastData.model_used || 'Ensemble'}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <div className="text-sm text-gray-600 mb-1">Accuracy (MAPE)</div>
                <div className="text-lg font-semibold">
                  {forecastData.mape
                    ? `${(forecastData.mape * 100).toFixed(2)}%`
                    : 'N/A'}
                </div>
              </div>
            </div>

            {/* Forecast Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="p-3 text-left">Date</th>
                    <th className="p-3 text-right">Forecast</th>
                    <th className="p-3 text-right">Lower Bound</th>
                    <th className="p-3 text-right">Upper Bound</th>
                    <th className="p-3 text-center">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {(forecastData.forecast || []).map((value, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{dates[index]}</td>
                      <td className="p-3 text-right">
                        <span className="font-semibold text-blue-600">
                          {Math.round(value)} units
                        </span>
                      </td>
                      <td className="p-3 text-right text-gray-600">
                        {Math.round(
                          forecastData.confidence_intervals?.lower?.[index] ?? value * 0.8
                        )}{' '}
                        units
                      </td>
                      <td className="p-3 text-right text-gray-600">
                        {Math.round(
                          forecastData.confidence_intervals?.upper?.[index] ?? value * 1.2
                        )}{' '}
                        units
                      </td>
                      <td className="p-3 text-center">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          95%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Chart (Simple ASCII visualization) */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm font-semibold mb-3">Forecast Visualization</div>
              <div className="space-y-2">
                {(forecastData.forecast || []).map((value, index) => {
                  const maxValue = Math.max(...(forecastData.forecast || [1]));
                  const barWidth = (value / maxValue) * 100;
                  return (
                    <div key={index} className="flex items-center gap-3">
                      <span className="text-xs font-medium w-12 text-right">
                        {dates[index]}
                      </span>
                      <div className="flex-1 bg-blue-200 rounded overflow-hidden">
                        <div
                          className="bg-blue-600 h-6 rounded flex items-center justify-end pr-2 text-xs text-white font-semibold"
                          style={{ width: `${barWidth}%` }}
                        >
                          {barWidth > 15 && Math.round(value)}
                        </div>
                      </div>
                      <span className="text-xs text-gray-600 w-20">
                        {Math.round(value)} units
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Insights */}
            <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
              <div className="font-semibold mb-2 flex items-center gap-2">
                💡 Forecast Insights
              </div>
              <ul className="text-sm space-y-1 text-gray-700">
                <li>
                  • Average predicted demand: {Math.round(
                    (forecastData.forecast || []).reduce((a, b) => a + b, 0) /
                      (forecastData.forecast?.length || 1)
                  )}{' '}
                  units
                </li>
                <li>
                  • Peak demand on:{' '}
                  {dates[
                    (forecastData.forecast || []).indexOf(
                      Math.max(...(forecastData.forecast || [0]))
                    )
                  ]}
                </li>
                <li>
                  • Demand range: {Math.round(Math.min(...(forecastData.forecast || [0])))} -{' '}
                  {Math.round(Math.max(...(forecastData.forecast || [0])))} units
                </li>
              </ul>
            </div>
          </div>
        )}

        {!forecastData && !loading && !error && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg mb-2">📈 Select a product and generate forecast to see predictions</div>
          </div>
        )}
      </div>
    </div>
  );
}
