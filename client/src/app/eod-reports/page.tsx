'use client';

// ===========================================
// Vendly POS - End-of-Day Reports Page
// ===========================================

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Reports } from '@/lib/api';

interface ZReport {
  report_date: string;
  report_time: string;
  total_sales: number;
  total_revenue: number;
  total_tax: number;
  total_discount: number;
  items_sold: number;
  total_refunds: number;
  total_returns: number;
  refund_amount: number;
  return_amount: number;
  payment_methods: Array<{
    method: string;
    count: number;
    revenue: number;
    percentage: number;
  }>;
  top_products: Array<{
    name: string;
    quantity: number;
    revenue: number;
  }>;
  shift_start_time?: string;
  shift_end_time?: string;
  employee_count?: number;
}

interface SalesSummary {
  date: string;
  total_sales: number;
  total_revenue: number;
  total_tax: number;
  total_discount: number;
  items_sold: number;
  average_transaction: number;
}

function EODReportsContent() {
  const [zReport, setZReport] = useState<ZReport | null>(null);
  const [salesSummary, setSalesSummary] = useState<SalesSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportDate, setReportDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [cashAmount, setCashAmount] = useState('');
  const [reconcileNotes, setReconcileNotes] = useState('');
  const [reconciling, setReconciling] = useState(false);
  const [reconcileResult, setReconcileResult] = useState<any>(null);
  const [error, setError] = useState('');

  const loadZReport = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const report = await Reports.zReport(reportDate);
      setZReport(report);
      
      const summary = await Reports.salesSummary(reportDate);
      setSalesSummary(summary);
    } catch (err: any) {
      setError(err.message || 'Failed to load Z-Report');
    } finally {
      setLoading(false);
    }
  }, [reportDate]);

  const handleReconcileCash = async () => {
    if (!cashAmount) {
      setError('Please enter actual cash amount');
      return;
    }

    setReconciling(true);
    setError('');
    try {
      const result = await Reports.reconcileCash(
        parseFloat(cashAmount),
        reportDate,
        reconcileNotes
      );
      setReconcileResult(result);
      setCashAmount('');
      setReconcileNotes('');
    } catch (err: any) {
      setError(err.message || 'Failed to reconcile cash drawer');
    } finally {
      setReconciling(false);
    }
  };

  useEffect(() => {
    loadZReport();
  }, [loadZReport]);

  return (
    <div className="max-w-7xl mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">End-of-Day Reports</h1>
          <p className="text-gray-600 mt-1">Z-Reports & Cash Reconciliation</p>
        </div>
        <input
          type="date"
          className="input w-48"
          value={reportDate}
          onChange={(e) => setReportDate(e.target.value)}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : zReport ? (
        <>
          {/* Z-Report Header */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-600">Report Date</p>
                <p className="text-lg font-semibold">{zReport.report_date}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Report Time</p>
                <p className="text-lg font-semibold">{zReport.report_time}</p>
              </div>
              {zReport.shift_start_time && (
                <div>
                  <p className="text-sm text-gray-600">Shift Start</p>
                  <p className="text-lg font-semibold">{zReport.shift_start_time}</p>
                </div>
              )}
              {zReport.employee_count !== undefined && (
                <div>
                  <p className="text-sm text-gray-600">Employees</p>
                  <p className="text-lg font-semibold">{zReport.employee_count}</p>
                </div>
              )}
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-600 mb-2">Total Sales</p>
              <p className="text-3xl font-bold">{zReport.total_sales}</p>
              <p className="text-xs text-gray-500 mt-2">{zReport.items_sold} items sold</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-600 mb-2">Total Revenue</p>
              <p className="text-3xl font-bold text-green-600">
                ${zReport.total_revenue.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Tax: ${zReport.total_tax.toFixed(2)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-600 mb-2">Discounts & Refunds</p>
              <p className="text-3xl font-bold text-red-600">
                -${(zReport.total_discount + zReport.refund_amount).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Refunds: ${zReport.refund_amount.toFixed(2)}
              </p>
            </div>
          </div>

          {/* Payment Method Breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-bold mb-4">Payment Method Breakdown</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-semibold">Payment Method</th>
                    <th className="text-right p-3 font-semibold">Count</th>
                    <th className="text-right p-3 font-semibold">Revenue</th>
                    <th className="text-right p-3 font-semibold">Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  {zReport.payment_methods.map((method, idx) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      <td className="p-3 capitalize">{method.method}</td>
                      <td className="text-right p-3">{method.count}</td>
                      <td className="text-right p-3 font-semibold">
                        ${method.revenue.toFixed(2)}
                      </td>
                      <td className="text-right p-3">{method.percentage.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Refunds & Returns */}
          {(zReport.total_refunds > 0 || zReport.total_returns > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <p className="text-sm text-gray-600 mb-2">Total Refunds</p>
                <p className="text-2xl font-bold text-orange-600">
                  {zReport.total_refunds}
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  Amount: ${zReport.refund_amount.toFixed(2)}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <p className="text-sm text-gray-600 mb-2">Total Returns</p>
                <p className="text-2xl font-bold text-orange-600">
                  {zReport.total_returns}
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  Amount: ${zReport.return_amount.toFixed(2)}
                </p>
              </div>
            </div>
          )}

          {/* Top Products */}
          {zReport.top_products.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-bold mb-4">Top Products</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-semibold">Product</th>
                      <th className="text-right p-3 font-semibold">Quantity</th>
                      <th className="text-right p-3 font-semibold">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {zReport.top_products.map((product, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="p-3 font-medium">{product.name}</td>
                        <td className="text-right p-3">{product.quantity}</td>
                        <td className="text-right p-3 font-semibold">
                          ${product.revenue.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cash Drawer Reconciliation */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-bold mb-6">Cash Drawer Reconciliation</h2>
            
            {reconcileResult && (
              <div className={`rounded-lg p-4 mb-6 ${
                reconcileResult.status === 'success'
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-yellow-50 border border-yellow-200'
              }`}>
                <p className={`font-semibold ${
                  reconcileResult.status === 'success'
                    ? 'text-green-700'
                    : 'text-yellow-700'
                }`}>
                  {reconcileResult.message}
                </p>
                <p className="text-sm mt-2">
                  Expected: ${reconcileResult.reconciliation.expected_cash.toFixed(2)} | 
                  Actual: ${reconcileResult.reconciliation.actual_cash.toFixed(2)} | 
                  Variance: ${reconcileResult.reconciliation.variance.toFixed(2)} ({reconcileResult.reconciliation.variance_percentage.toFixed(2)}%)
                </p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Expected Cash (from sales)
                </label>
                <div className="text-2xl font-bold text-green-600">
                  ${salesSummary ? 
                    (salesSummary.total_revenue - (salesSummary.total_discount + zReport.refund_amount)).toFixed(2)
                    : '0.00'
                  }
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Based on cash sales for {reportDate}
                </p>
              </div>

              <div>
                <label htmlFor="cashAmount" className="block text-sm font-medium mb-2">
                  Actual Cash Counted
                </label>
                <input
                  id="cashAmount"
                  type="number"
                  step="0.01"
                  min="0"
                  className="input w-full"
                  placeholder="Enter amount"
                  value={cashAmount}
                  onChange={(e) => setCashAmount(e.target.value)}
                />
              </div>

              <div>
                <label htmlFor="reconcileNotes" className="block text-sm font-medium mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  id="reconcileNotes"
                  className="input w-full resize-none"
                  rows={3}
                  placeholder="Add any notes about cash discrepancies..."
                  value={reconcileNotes}
                  onChange={(e) => setReconcileNotes(e.target.value)}
                />
              </div>

              <button
                className="btn btn-primary w-full"
                onClick={handleReconcileCash}
                disabled={reconciling || !cashAmount}
              >
                {reconciling ? 'Reconciling...' : 'Reconcile Cash Drawer'}
              </button>
            </div>
          </div>

          {/* Export Options */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-bold mb-4">Export Report</h2>
            <div className="flex gap-3">
              <button
                className="btn btn-secondary"
                onClick={() => {
                  const reportText = `
Z-REPORT - ${zReport.report_date}
Generated: ${zReport.report_time}
=====================================

SALES SUMMARY
Total Sales: ${zReport.total_sales}
Total Revenue: $${zReport.total_revenue.toFixed(2)}
Total Tax: $${zReport.total_tax.toFixed(2)}
Total Discount: $${zReport.total_discount.toFixed(2)}
Items Sold: ${zReport.items_sold}

PAYMENT METHODS
${zReport.payment_methods.map(m => 
  `${m.method.toUpperCase()}: ${m.count} transactions, $${m.revenue.toFixed(2)} (${m.percentage.toFixed(1)}%)`
).join('\n')}

REFUNDS & RETURNS
Total Refunds: ${zReport.total_refunds} ($${zReport.refund_amount.toFixed(2)})
Total Returns: ${zReport.total_returns} ($${zReport.return_amount.toFixed(2)})
                  `;
                  const blob = new Blob([reportText], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `z-report-${zReport.report_date}.txt`;
                  a.click();
                }}
              >
                📄 Download as Text
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => window.print()}
              >
                🖨️ Print Report
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <p className="text-gray-500">No data available for {reportDate}</p>
          <button
            className="btn btn-primary mt-4"
            onClick={loadZReport}
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

export default function EODReportsPage() {
  return (
    <ProtectedRoute>
      <EODReportsContent />
    </ProtectedRoute>
  );
}
