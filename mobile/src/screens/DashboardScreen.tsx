/**
 * Dashboard Screen - Sales summary and analytics
 * Fetches data dynamically from API, matches web client theme
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Share,
  Modal,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService, createWebSocket } from '../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type TimeRange = 'today' | 'week' | 'month';

interface Transaction {
  id: number;
  total: number;
  payment_method: string;
  status: string;
  created_at: string;
  subtotal: number;
  tax: number;
  discount: number;
}

interface SalesSummary {
  total_sales: number;
  total_revenue: number;
  total_tax: number;
  total_discount: number;
  items_sold: number;
  transaction_count: number;
  average_transaction: number;
  returns_amount: number;
  top_products?: TopProduct[];
  payment_methods?: PaymentBreakdown[];
}

interface TopProduct {
  id: number;
  name: string;
  quantity: number;
  revenue: number;
}

interface PaymentBreakdown {
  method: string;
  count: number;
  revenue: number;
  percentage: number;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const DashboardScreen: React.FC<{ navigation?: { navigate: (screen: string) => void } }> = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('today');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [showTransactions, setShowTransactions] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  
  // Dynamic data
  const [summary, setSummary] = useState<SalesSummary | null>(null);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [paymentBreakdown, setPaymentBreakdown] = useState<PaymentBreakdown[]>([]);

  // Helper to format date as YYYY-MM-DD in local timezone
  const formatLocalDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const getDateRange = useCallback(() => {
    const today = new Date();
    // Add 1 day buffer to handle UTC timezone differences
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    let startDate: Date;
    
    switch (timeRange) {
      case 'week':
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 7);
        break;
      case 'month':
        startDate = new Date(today);
        startDate.setMonth(today.getMonth() - 1);
        break;
      default:
        startDate = new Date(today);
    }
    
    return {
      startDate: formatLocalDate(startDate),
      endDate: formatLocalDate(tomorrow),
    };
  }, [timeRange]);

  const loadDashboardData = useCallback(async () => {
    try {
      setError('');
      const { startDate, endDate } = getDateRange();
      
      // Load dashboard summary data
      const summaryData = await apiService.getReportSummary(startDate, endDate).catch(() => null);

      if (summaryData) {
        const typedSummary = summaryData as SalesSummary;
        setSummary(typedSummary);
        // Extract top products if available
        if (typedSummary.top_products) {
          setTopProducts(typedSummary.top_products.slice(0, 5));
        }
        // Extract payment breakdown if available
        if (typedSummary.payment_methods) {
          setPaymentBreakdown(typedSummary.payment_methods);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getDateRange]);

  useEffect(() => {
    setLoading(true);
    loadDashboardData();
  }, [loadDashboardData]);

  // WebSocket for real-time transaction updates
  useEffect(() => {
    const ws = createWebSocket((data: unknown) => {
      const message = data as { event?: string; type?: string; data?: Transaction };
      
      // Check for sale_created event
      if (message.event === 'sale_created' || message.type === 'sale_created') {
        const newTransaction = message.data;
        if (newTransaction) {
          console.log('📥 Real-time transaction received:', newTransaction.id);
          
          // Refresh dashboard data to update totals
          loadDashboardData();
          
          // If transactions modal is open, add new transaction
          if (showTransactions) {
            const { startDate, endDate } = getDateRange();
            const txDate = formatLocalDate(new Date(newTransaction.created_at));
            const inRange = txDate >= startDate && txDate <= endDate;
            
            if (inRange) {
              setTransactions(prev => {
                // Avoid duplicates
                if (prev.some(t => t.id === newTransaction.id)) return prev;
                // Add to beginning (newest first)
                return [newTransaction, ...prev];
              });
            }
          }
        }
      }
    });

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [showTransactions, getDateRange, loadDashboardData]);

  const loadTransactions = useCallback(async () => {
    setLoadingTransactions(true);
    try {
      const { startDate, endDate } = getDateRange();
      const data = await apiService.getSales({ limit: 100 });
      // Filter by date range
      const filtered = (data as Transaction[]).filter(t => {
        const txDate = formatLocalDate(new Date(t.created_at));
        return txDate >= startDate && txDate <= endDate;
      });
      // Sort newest first
      filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setTransactions(filtered);
    } catch (_err) {
      // Failed to load transactions
      setTransactions([]);
    } finally {
      setLoadingTransactions(false);
    }
  }, [getDateRange]);

  const openTransactions = () => {
    setShowTransactions(true);
    loadTransactions();
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  // PDF generation for future use
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _generatePdfHtml = () => {
    const { startDate, endDate } = getDateRange();
    const netSales = summary ? summary.total_revenue - (summary.returns_amount || 0) : 0;
    const transactionCount = summary?.total_sales || 0;
    const avgTicket = summary?.average_transaction || (transactionCount > 0 ? summary!.total_revenue / transactionCount : 0);
    const itemsSold = summary?.items_sold || 0;
    const returns = summary?.returns_amount || 0;

    const topProductsHtml = topProducts.length > 0 
      ? topProducts.map((product, index) => `
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">${index + 1}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">${product.name}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${product.quantity}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${formatCurrency(product.revenue)}</td>
        </tr>
      `).join('')
      : '<tr><td colspan="4" style="padding: 16px; text-align: center; color: #94a3b8;">No product data available</td></tr>';

    const paymentMethodsHtml = paymentBreakdown.length > 0
      ? paymentBreakdown.map(payment => `
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-transform: capitalize;">${payment.method}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${payment.count}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${formatCurrency(payment.revenue)}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${payment.percentage.toFixed(1)}%</td>
        </tr>
      `).join('')
      : '<tr><td colspan="4" style="padding: 16px; text-align: center; color: #94a3b8;">No payment data available</td></tr>';

    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Vendly Sales Report</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              margin: 0;
              padding: 20px;
              background: #fff;
              color: #0f172a;
            }
            .header {
              background: linear-gradient(135deg, #0ea5e9, #8b5cf6);
              color: white;
              padding: 24px;
              border-radius: 12px;
              margin-bottom: 24px;
            }
            .header h1 {
              margin: 0 0 8px 0;
              font-size: 28px;
            }
            .header p {
              margin: 0;
              opacity: 0.9;
              font-size: 14px;
            }
            .summary-grid {
              display: grid;
              grid-template-columns: repeat(2, 1fr);
              gap: 16px;
              margin-bottom: 24px;
            }
            .summary-card {
              background: #f8fafc;
              border: 1px solid #e2e8f0;
              border-radius: 12px;
              padding: 16px;
            }
            .summary-card .label {
              font-size: 12px;
              color: #64748b;
              text-transform: uppercase;
              letter-spacing: 0.5px;
            }
            .summary-card .value {
              font-size: 24px;
              font-weight: 700;
              color: #0f172a;
              margin-top: 4px;
            }
            .summary-card.primary .value {
              color: #0ea5e9;
            }
            .summary-card.success .value {
              color: #10b981;
            }
            .summary-card.warning .value {
              color: #f59e0b;
            }
            .summary-card.danger .value {
              color: #ef4444;
            }
            .section {
              margin-bottom: 24px;
            }
            .section h2 {
              font-size: 18px;
              color: #0f172a;
              margin: 0 0 12px 0;
              padding-bottom: 8px;
              border-bottom: 2px solid #0ea5e9;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              background: #fff;
              border-radius: 8px;
              overflow: hidden;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th {
              background: #f1f5f9;
              padding: 12px 8px;
              text-align: left;
              font-weight: 600;
              color: #475569;
              font-size: 12px;
              text-transform: uppercase;
            }
            .footer {
              text-align: center;
              padding: 20px;
              color: #94a3b8;
              font-size: 12px;
              border-top: 1px solid #e2e8f0;
              margin-top: 32px;
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>📊 Vendly Sales Report</h1>
            <p>Period: ${startDate} to ${endDate} | Generated: ${new Date().toLocaleString()}</p>
          </div>

          <div class="summary-grid">
            <div class="summary-card primary">
              <div class="label">Net Sales</div>
              <div class="value">${formatCurrency(netSales)}</div>
            </div>
            <div class="summary-card success">
              <div class="label">Transactions</div>
              <div class="value">${transactionCount}</div>
            </div>
            <div class="summary-card warning">
              <div class="label">Average Ticket</div>
              <div class="value">${formatCurrency(avgTicket)}</div>
            </div>
            <div class="summary-card">
              <div class="label">Items Sold</div>
              <div class="value">${itemsSold}</div>
            </div>
            <div class="summary-card danger">
              <div class="label">Returns</div>
              <div class="value">${formatCurrency(returns)}</div>
            </div>
            <div class="summary-card">
              <div class="label">Tax Collected</div>
              <div class="value">${formatCurrency(summary?.total_tax || 0)}</div>
            </div>
          </div>

          <div class="section">
            <h2>🏆 Top Selling Products</h2>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Product</th>
                  <th style="text-align: right;">Qty</th>
                  <th style="text-align: right;">Revenue</th>
                </tr>
              </thead>
              <tbody>
                ${topProductsHtml}
              </tbody>
            </table>
          </div>

          <div class="section">
            <h2>💳 Payment Methods</h2>
            <table>
              <thead>
                <tr>
                  <th>Method</th>
                  <th style="text-align: right;">Count</th>
                  <th style="text-align: right;">Amount</th>
                  <th style="text-align: right;">Share</th>
                </tr>
              </thead>
              <tbody>
                ${paymentMethodsHtml}
              </tbody>
            </table>
          </div>

          <div class="footer">
            <p>Generated by Vendly POS • ${new Date().getFullYear()}</p>
          </div>
        </body>
      </html>
    `;
  };

  const generateTextReport = () => {
    const { startDate, endDate } = getDateRange();
    const netSalesVal = summary ? summary.total_revenue - (summary.returns_amount || 0) : 0;
    const transCount = summary?.total_sales || 0;
    const avgTicket = summary?.average_transaction || (transCount > 0 ? summary!.total_revenue / transCount : 0);
    const itemsSoldVal = summary?.items_sold || 0;
    const returnsVal = summary?.returns_amount || 0;

    let report = `
📊 VENDLY SALES REPORT
══════════════════════════════
Period: ${startDate} to ${endDate}
Generated: ${new Date().toLocaleString()}

💰 SALES SUMMARY
──────────────────────────────
Net Sales:        ${formatCurrency(netSalesVal)}
Transactions:     ${transCount}
Average Ticket:   ${formatCurrency(avgTicket)}
Items Sold:       ${itemsSoldVal}
Returns:          ${formatCurrency(returnsVal)}
Tax Collected:    ${formatCurrency(summary?.total_tax || 0)}
`;

    if (topProducts.length > 0) {
      report += `
🏆 TOP SELLING PRODUCTS
──────────────────────────────`;
      topProducts.forEach((product, index) => {
        report += `
${index + 1}. ${product.name}
   Qty: ${product.quantity} | Revenue: ${formatCurrency(product.revenue)}`;
      });
    }

    if (paymentBreakdown.length > 0) {
      report += `

💳 PAYMENT METHODS
──────────────────────────────`;
      paymentBreakdown.forEach(payment => {
        report += `
${payment.method.charAt(0).toUpperCase() + payment.method.slice(1)}: ${formatCurrency(payment.revenue)} (${payment.percentage.toFixed(1)}%)`;
      });
    }

    report += `

══════════════════════════════
Powered by Vendly POS
`;

    return report;
  };

  const handleExportReport = async () => {
    try {
      setExporting(true);
      
      const reportText = generateTextReport();
      
      const result = await Share.share({
        message: reportText,
        title: 'Vendly Sales Report',
      });

      if (result.action === Share.sharedAction) {
        // Successfully shared
      }
    } catch (_err) {
      Alert.alert('Export Failed', 'Unable to share report. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  // Default values if no data
  const netSales = summary ? summary.total_revenue - (summary.returns_amount || 0) : 0;
  const transactionCount = summary?.total_sales || 0;
  const averageTicket = summary?.average_transaction || (transactionCount > 0 ? summary.total_revenue / transactionCount : 0);
  const itemsSold = summary?.items_sold || 0;
  const returns = summary?.returns_amount || 0;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0ea5e9" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <View style={styles.timeRangeSelector}>
          {(['today', 'week', 'month'] as TimeRange[]).map(range => (
            <TouchableOpacity
              key={range}
              style={[
                styles.timeRangeButton,
                timeRange === range && styles.timeRangeButtonActive,
              ]}
              onPress={() => setTimeRange(range)}
            >
              <Text style={[
                styles.timeRangeText,
                timeRange === range && styles.timeRangeTextActive,
              ]}>
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#0ea5e9" />
        }
      >
        {error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={48} color="#ef4444" />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={loadDashboardData}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {/* Main Stats */}
            <View style={styles.mainStatsRow}>
              <View style={[styles.mainStatCard, styles.primaryStatCard]}>
                <Text style={styles.mainStatLabel}>Net Sales</Text>
                <Text style={styles.mainStatValue}>${netSales.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Text>
                <View style={styles.statChange}>
                  <Ionicons name="trending-up" size={14} color="#22c55e" />
                  <Text style={styles.statChangeText}>vs last {timeRange}</Text>
                </View>
              </View>
            </View>

            {/* Quick Stats Grid */}
            <View style={styles.statsGrid}>
              <TouchableOpacity 
                style={styles.statCard}
                onPress={openTransactions}
              >
                <View style={[styles.statIcon, { backgroundColor: '#e0f2fe' }]}>
                  <Ionicons name="receipt-outline" size={20} color="#0ea5e9" />
                </View>
                <Text style={styles.statValue}>{transactionCount}</Text>
                <Text style={styles.statLabel}>Transactions</Text>
              </TouchableOpacity>
              <View style={styles.statCard}>
                <View style={[styles.statIcon, { backgroundColor: '#fef3c7' }]}>
                  <Ionicons name="trending-up-outline" size={20} color="#f59e0b" />
                </View>
                <Text style={styles.statValue}>${averageTicket.toFixed(2)}</Text>
                <Text style={styles.statLabel}>Avg. Ticket</Text>
              </View>
              <View style={styles.statCard}>
                <View style={[styles.statIcon, { backgroundColor: '#dcfce7' }]}>
                  <Ionicons name="cube-outline" size={20} color="#22c55e" />
                </View>
                <Text style={styles.statValue}>{itemsSold}</Text>
                <Text style={styles.statLabel}>Items Sold</Text>
              </View>
              <View style={styles.statCard}>
                <View style={[styles.statIcon, { backgroundColor: '#fee2e2' }]}>
                  <Ionicons name="arrow-undo-outline" size={20} color="#ef4444" />
                </View>
                <Text style={styles.statValue}>${returns.toFixed(2)}</Text>
                <Text style={styles.statLabel}>Returns</Text>
              </View>
            </View>

            {/* Top Products */}
            {topProducts.length > 0 && (
              <View style={styles.topProductsCard}>
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>Top Selling Products</Text>
                  <TouchableOpacity>
                    <Text style={styles.viewAllText}>View All</Text>
                  </TouchableOpacity>
                </View>
                {topProducts.map((product, index) => (
                  <View key={product.id} style={styles.productRow}>
                    <View style={styles.productRank}>
                      <Text style={styles.productRankText}>{index + 1}</Text>
                    </View>
                    <View style={styles.productInfo}>
                      <Text style={styles.productName}>{product.name}</Text>
                      <Text style={styles.productQuantity}>{product.quantity} sold</Text>
                    </View>
                    <Text style={styles.productRevenue}>${product.revenue.toFixed(2)}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Payment Methods Breakdown */}
            {paymentBreakdown.length > 0 && (
              <View style={styles.paymentBreakdownCard}>
                <Text style={styles.sectionTitle}>Payment Methods</Text>
                <View style={styles.paymentMethods}>
                  {paymentBreakdown.map((payment, index) => (
                    <View key={index} style={styles.paymentMethod}>
                      <View style={[styles.paymentDot, { backgroundColor: getPaymentColor(payment.method) }]} />
                      <View style={styles.paymentInfo}>
                        <Text style={styles.paymentType}>{payment.method}</Text>
                        <Text style={styles.paymentAmount}>${payment.revenue.toFixed(2)}</Text>
                      </View>
                      <Text style={styles.paymentPercent}>{payment.percentage.toFixed(0)}%</Text>
                    </View>
                  ))}
                </View>
                
                {/* Visual bar */}
                <View style={styles.paymentBar}>
                  {paymentBreakdown.map((payment, index) => (
                    <View 
                      key={index}
                      style={[
                        styles.paymentBarSegment, 
                        { flex: payment.percentage, backgroundColor: getPaymentColor(payment.method) }
                      ]} 
                    />
                  ))}
                </View>
              </View>
            )}

            {/* Quick Actions */}
            <View style={styles.quickActions}>
              <TouchableOpacity 
                style={[styles.quickAction, exporting && styles.quickActionDisabled]} 
                onPress={handleExportReport}
                disabled={exporting}
              >
                {exporting ? (
                  <ActivityIndicator size="small" color="#0ea5e9" />
                ) : (
                  <Ionicons name="download-outline" size={20} color="#0ea5e9" />
                )}
                <Text style={styles.quickActionText}>
                  {exporting ? 'Generating...' : 'Export Report'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.quickAction} onPress={handleExportReport}>
                <Ionicons name="print-outline" size={20} color="#0ea5e9" />
                <Text style={styles.quickActionText}>Print Summary</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>

      {/* Transactions Modal */}
      <Modal
        visible={showTransactions}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowTransactions(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Transactions</Text>
            <TouchableOpacity onPress={() => setShowTransactions(false)}>
              <Ionicons name="close" size={24} color="#64748b" />
            </TouchableOpacity>
          </View>
          
          {loadingTransactions ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#0ea5e9" />
            </View>
          ) : transactions.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="receipt-outline" size={64} color="#cbd5e1" />
              <Text style={styles.emptyText}>No transactions found</Text>
            </View>
          ) : (
            <FlatList
              data={transactions}
              keyExtractor={(item) => item.id.toString()}
              contentContainerStyle={{ padding: 16 }}
              renderItem={({ item }) => (
                <View style={styles.transactionItem}>
                  <View style={styles.transactionLeft}>
                    <Text style={styles.transactionId}>#{item.id}</Text>
                    <Text style={styles.transactionTime}>
                      {new Date(item.created_at).toLocaleTimeString('en-US', { 
                        hour: 'numeric', minute: '2-digit', hour12: true 
                      })}
                    </Text>
                    <Text style={[styles.transactionStatus, { color: item.status === 'completed' ? '#22c55e' : '#f59e0b' }]}>
                      {item.status}
                    </Text>
                  </View>
                  <View style={styles.transactionRight}>
                    <Text style={styles.transactionTotal}>${item.total?.toFixed(2) || '0.00'}</Text>
                    <Text style={styles.transactionPayment}>{item.payment_method}</Text>
                  </View>
                </View>
              )}
              ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
            />
          )}
        </View>
      </Modal>
    </View>
  );
};

function getPaymentColor(method: string): string {
  const colors: Record<string, string> = {
    card: '#0ea5e9',
    cash: '#22c55e',
    digital: '#a855f7',
    gift_card: '#f59e0b',
  };
  return colors[method.toLowerCase()] || '#64748b';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#64748b',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorText: {
    marginTop: 12,
    fontSize: 16,
    color: '#ef4444',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 10,
    backgroundColor: '#0ea5e9',
    borderRadius: 8,
  },
  retryText: {
    color: '#fff',
    fontWeight: '600',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 16,
    paddingHorizontal: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: 12,
  },
  timeRangeSelector: {
    flexDirection: 'row',
    backgroundColor: '#f1f5f9',
    borderRadius: 8,
    padding: 4,
  },
  timeRangeButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  timeRangeButtonActive: {
    backgroundColor: '#0ea5e9',
  },
  timeRangeText: {
    fontSize: 14,
    color: '#64748b',
    fontWeight: '500',
  },
  timeRangeTextActive: {
    color: '#fff',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  mainStatsRow: {
    marginBottom: 16,
  },
  mainStatCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  primaryStatCard: {
    backgroundColor: '#f0fdf4',
    borderColor: '#86efac',
  },
  mainStatLabel: {
    fontSize: 14,
    color: '#16a34a',
  },
  mainStatValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#0f172a',
    marginVertical: 4,
  },
  statChange: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statChangeText: {
    fontSize: 13,
    color: '#22c55e',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    width: (SCREEN_WIDTH - 44) / 2,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  statIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0f172a',
  },
  statLabel: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  topProductsCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  viewAllText: {
    fontSize: 14,
    color: '#0ea5e9',
  },
  productRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  productRank: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#f1f5f9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  productRankText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748b',
  },
  productInfo: {
    flex: 1,
    marginLeft: 12,
  },
  productName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#0f172a',
  },
  productQuantity: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  productRevenue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#22c55e',
  },
  paymentBreakdownCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  paymentMethods: {
    gap: 12,
    marginBottom: 16,
  },
  paymentMethod: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  paymentDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  paymentInfo: {
    flex: 1,
    marginLeft: 12,
  },
  paymentType: {
    fontSize: 14,
    color: '#0f172a',
  },
  paymentAmount: {
    fontSize: 12,
    color: '#64748b',
  },
  paymentPercent: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
  },
  paymentBar: {
    flexDirection: 'row',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  paymentBarSegment: {
    height: '100%',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
  },
  quickAction: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#ffffff',
    paddingVertical: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  quickActionDisabled: {
    opacity: 0.6,
  },
  quickActionText: {
    fontSize: 14,
    color: '#0ea5e9',
    fontWeight: '500',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0f172a',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 16,
  },
  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  transactionLeft: {
    gap: 2,
  },
  transactionId: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0f172a',
  },
  transactionTime: {
    fontSize: 13,
    color: '#64748b',
  },
  transactionStatus: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'capitalize',
    marginTop: 2,
  },
  transactionRight: {
    alignItems: 'flex-end',
  },
  transactionTotal: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
  },
  transactionPayment: {
    fontSize: 12,
    color: '#64748b',
    textTransform: 'capitalize',
    marginTop: 2,
  },
});

export default DashboardScreen;
