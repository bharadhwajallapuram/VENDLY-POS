/**
 * Dashboard Screen - Sales summary and analytics
 * Fetches data dynamically from API, matches web client theme
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type TimeRange = 'today' | 'week' | 'month';

interface SalesSummary {
  total_sales: number;
  total_revenue: number;
  total_tax: number;
  total_discount: number;
  items_sold: number;
  transaction_count: number;
  average_transaction: number;
  returns_amount: number;
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

export const DashboardScreen: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('today');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Dynamic data
  const [summary, setSummary] = useState<SalesSummary | null>(null);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [paymentBreakdown, setPaymentBreakdown] = useState<PaymentBreakdown[]>([]);

  const getDateRange = useCallback(() => {
    const today = new Date();
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
        startDate = today;
    }
    
    return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: today.toISOString().split('T')[0],
    };
  }, [timeRange]);

  const loadDashboardData = useCallback(async () => {
    try {
      setError('');
      const { startDate, endDate } = getDateRange();
      
      // Load dashboard summary data
      const summaryData = await apiService.getReportSummary(startDate, endDate).catch(() => null);

      if (summaryData) {
        setSummary(summaryData as SalesSummary);
        // Extract top products if available
        if ((summaryData as any).top_products) {
          setTopProducts((summaryData as any).top_products.slice(0, 5));
        }
        // Extract payment breakdown if available
        if ((summaryData as any).payment_methods) {
          setPaymentBreakdown((summaryData as any).payment_methods);
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

  const onRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
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
              <View style={styles.statCard}>
                <View style={[styles.statIcon, { backgroundColor: '#e0f2fe' }]}>
                  <Ionicons name="receipt-outline" size={20} color="#0ea5e9" />
                </View>
                <Text style={styles.statValue}>{transactionCount}</Text>
                <Text style={styles.statLabel}>Transactions</Text>
              </View>
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
              <TouchableOpacity style={styles.quickAction}>
                <Ionicons name="download-outline" size={20} color="#0ea5e9" />
                <Text style={styles.quickActionText}>Export Report</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.quickAction}>
                <Ionicons name="print-outline" size={20} color="#0ea5e9" />
                <Text style={styles.quickActionText}>Print Summary</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>
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
  quickActionText: {
    fontSize: 14,
    color: '#0ea5e9',
    fontWeight: '500',
  },
});

export default DashboardScreen;
