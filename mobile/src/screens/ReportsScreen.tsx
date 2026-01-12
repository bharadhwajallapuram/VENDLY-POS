/**
 * Reports Screen - Sales reports and analytics
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';

interface ReportSummary {
  total_sales: number;
  total_revenue: number;
  average_sale: number;
  top_products: Array<{
    name: string;
    quantity: number;
    revenue: number;
  }>;
  total_refunds?: number;
  total_returns?: number;
  refund_amount?: number;
  return_amount?: number;
}

type DatePreset = 'today' | 'week' | 'month' | 'custom';

export function ReportsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [error, setError] = useState('');
  const [preset, setPreset] = useState<DatePreset>('week');
  const [dateRange, setDateRange] = useState(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 7);
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    };
  });

  const updateDateRange = (newPreset: DatePreset) => {
    const end = new Date();
    const start = new Date();

    switch (newPreset) {
      case 'today':
        break;
      case 'week':
        start.setDate(start.getDate() - 7);
        break;
      case 'month':
        start.setDate(start.getDate() - 30);
        break;
      default:
        return;
    }

    setPreset(newPreset);
    setDateRange({
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    });
  };

  const loadReport = useCallback(async () => {
    try {
      setError('');
      const data = await apiService.getReportSummary(dateRange.start, dateRange.end);
      setSummary(data as ReportSummary);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load report');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [dateRange.start, dateRange.end]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const onRefresh = () => {
    setRefreshing(true);
    loadReport();
  };

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#0ea5e9" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Sales Reports</Text>
        <Text style={styles.subtitle}>
          {dateRange.start} to {dateRange.end}
        </Text>
      </View>

      {/* Date Preset Buttons */}
      <View style={styles.presetContainer}>
        {(['today', 'week', 'month'] as DatePreset[]).map((p) => (
          <TouchableOpacity
            key={p}
            style={[styles.presetButton, preset === p && styles.presetButtonActive]}
            onPress={() => updateDateRange(p)}
          >
            <Text style={[styles.presetText, preset === p && styles.presetTextActive]}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#0ea5e9" />
        }
      >
        {error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={48} color="#ef4444" />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={loadReport}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : summary ? (
          <>
            {/* Summary Cards */}
            <View style={styles.cardsGrid}>
              <View style={styles.card}>
                <Ionicons name="receipt" size={24} color="#0ea5e9" />
                <Text style={styles.cardLabel}>Total Sales</Text>
                <Text style={styles.cardValue}>{summary.total_sales}</Text>
              </View>
              <View style={styles.card}>
                <Ionicons name="cash" size={24} color="#10b981" />
                <Text style={styles.cardLabel}>Revenue</Text>
                <Text style={[styles.cardValue, styles.revenueValue]}>
                  {formatCurrency(summary.total_revenue)}
                </Text>
              </View>
            </View>

            <View style={styles.cardsGrid}>
              <View style={styles.card}>
                <Ionicons name="trending-up" size={24} color="#8b5cf6" />
                <Text style={styles.cardLabel}>Average Sale</Text>
                <Text style={styles.cardValue}>{formatCurrency(summary.average_sale)}</Text>
              </View>
              <View style={styles.card}>
                <Ionicons name="return-down-back" size={24} color="#f59e0b" />
                <Text style={styles.cardLabel}>Refunds</Text>
                <Text style={[styles.cardValue, styles.refundValue]}>
                  {summary.total_refunds || 0}
                </Text>
              </View>
            </View>

            {/* Refund Amount */}
            {(summary.refund_amount || 0) > 0 && (
              <View style={styles.refundCard}>
                <View style={styles.refundRow}>
                  <Text style={styles.refundLabel}>Refund Amount</Text>
                  <Text style={styles.refundAmount}>
                    -{formatCurrency(summary.refund_amount || 0)}
                  </Text>
                </View>
                <View style={styles.refundRow}>
                  <Text style={styles.refundLabel}>Return Amount</Text>
                  <Text style={styles.refundAmount}>
                    -{formatCurrency(summary.return_amount || 0)}
                  </Text>
                </View>
              </View>
            )}

            {/* Top Products */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Top Products</Text>
              {summary.top_products && summary.top_products.length > 0 ? (
                summary.top_products.map((product, index) => (
                  <View key={index} style={styles.productRow}>
                    <View style={styles.productRank}>
                      <Text style={styles.rankText}>{index + 1}</Text>
                    </View>
                    <View style={styles.productInfo}>
                      <Text style={styles.productName} numberOfLines={1}>
                        {product.name}
                      </Text>
                      <Text style={styles.productQty}>{product.quantity} sold</Text>
                    </View>
                    <Text style={styles.productRevenue}>
                      {formatCurrency(product.revenue)}
                    </Text>
                  </View>
                ))
              ) : (
                <Text style={styles.emptyText}>No products data available</Text>
              )}
            </View>
          </>
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons name="document-text-outline" size={64} color="#475569" />
            <Text style={styles.emptyText}>No report data available</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
  header: {
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  presetContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  presetButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#f1f5f9',
    borderRadius: 8,
    alignItems: 'center',
  },
  presetButtonActive: {
    backgroundColor: '#0ea5e9',
  },
  presetText: {
    color: '#64748b',
    fontWeight: '600',
  },
  presetTextActive: {
    color: '#ffffff',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  cardsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  card: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  cardLabel: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 8,
  },
  cardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0f172a',
    marginTop: 4,
  },
  revenueValue: {
    color: '#10b981',
  },
  refundValue: {
    color: '#f59e0b',
  },
  refundCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  refundRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  refundLabel: {
    color: '#64748b',
    fontSize: 14,
  },
  refundAmount: {
    color: '#f59e0b',
    fontWeight: '600',
    fontSize: 16,
  },
  section: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#0f172a',
    marginBottom: 16,
  },
  productRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
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
    marginRight: 12,
  },
  rankText: {
    color: '#0f172a',
    fontWeight: '600',
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    color: '#0f172a',
    fontSize: 15,
    fontWeight: '500',
  },
  productQty: {
    color: '#94a3b8',
    fontSize: 13,
    marginTop: 2,
  },
  productRevenue: {
    color: '#10b981',
    fontWeight: '600',
    fontSize: 15,
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 16,
    marginTop: 12,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    backgroundColor: '#0ea5e9',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    color: '#64748b',
    fontSize: 16,
    marginTop: 12,
  },
});
