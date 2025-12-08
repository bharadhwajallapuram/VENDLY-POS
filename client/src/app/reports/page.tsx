'use client';

// ===========================================
// Vendly POS - Reports Page
// ===========================================

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Reports, ReportSummary } from '@/lib/api';

function ReportsContent() {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  const loadReport = useCallback(async () => {
    setLoading(true);
    try {
      const data = await Reports.summary(dateRange.start, dateRange.end);
      setSummary(data);
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoading(false);
    }
  }, [dateRange.start, dateRange.end]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Reports</h1>
        <div className="flex gap-2 items-center">
          <input
            type="date"
            className="input w-auto"
            value={dateRange.start}
            onChange={(e) => setDateRange((r) => ({ ...r, start: e.target.value }))}
          />
          <span>to</span>
          <input
            type="date"
            className="input w-auto"
            value={dateRange.end}
            onChange={(e) => setDateRange((r) => ({ ...r, end: e.target.value }))}
          />
          <button className="btn btn-primary" onClick={loadReport}>
            Apply
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : summary ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Total Sales</div>
              <div className="text-3xl font-bold">{summary.total_sales}</div>
            </div>
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Total Revenue</div>
              <div className="text-3xl font-bold">
                ${summary.total_revenue.toFixed(2)}
              </div>
            </div>
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Average Sale</div>
              <div className="text-3xl font-bold">
                ${summary.average_sale.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Refunds & Returns Section */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card border-l-4" style={{ borderLeftColor: '#d97706' }}>
              <div className="text-sm text-gray-600 mb-1">Total Refunds</div>
              <div className="text-2xl font-bold" style={{ color: '#d97706' }}>{summary.total_refunds || 0}</div>
            </div>
            <div className="card border-l-4" style={{ borderLeftColor: '#d97706' }}>
              <div className="text-sm text-gray-600 mb-1">Refund Amount</div>
              <div className="text-2xl font-bold" style={{ color: '#d97706' }}>
                ${(summary.refund_amount || 0).toFixed(2)}
              </div>
            </div>
            <div className="card border-l-4" style={{ borderLeftColor: '#dc2626' }}>
              <div className="text-sm text-gray-600 mb-1">Total Returns</div>
              <div className="text-2xl font-bold" style={{ color: '#dc2626' }}>{summary.total_returns || 0}</div>
            </div>
            <div className="card border-l-4" style={{ borderLeftColor: '#dc2626' }}>
              <div className="text-sm text-gray-600 mb-1">Return Amount</div>
              <div className="text-2xl font-bold" style={{ color: '#dc2626' }}>
                ${(summary.return_amount || 0).toFixed(2)}
              </div>
            </div>
          </div>

          {/* Top Products */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Top Products</h2>
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="p-3 text-left">Product</th>
                  <th className="p-3 text-right">Quantity</th>
                  <th className="p-3 text-right">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {summary.top_products.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="p-6 text-center text-gray-500">
                      No sales data available
                    </td>
                  </tr>
                ) : (
                  summary.top_products.map((product, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{product.name}</td>
                      <td className="p-3 text-right">{product.quantity}</td>
                      <td className="p-3 text-right">
                        ${product.revenue.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="card text-center py-12 text-gray-500">
          Failed to load report data
        </div>
      )}
    </div>
  );
}

export default function ReportsPage() {
  return (
    <ProtectedRoute roles={['manager', 'admin']}>
      <ReportsContent />
    </ProtectedRoute>
  );
}
