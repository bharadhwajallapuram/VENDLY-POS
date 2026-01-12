/**
 * EOD Reports Screen - End of Day Z-Reports and Cash Reconciliation
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
  TextInput,
  Alert,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';

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
}

interface ReconcileResult {
  expected_cash: number;
  actual_cash: number;
  difference: number;
  status: string;
}

export function EODReportsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [zReport, setZReport] = useState<ZReport | null>(null);
  const [error, setError] = useState('');
  const [reportDate, setReportDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [showReconcile, setShowReconcile] = useState(false);
  const [cashAmount, setCashAmount] = useState('');
  const [reconcileNotes, setReconcileNotes] = useState('');
  const [reconciling, setReconciling] = useState(false);
  const [reconcileResult, setReconcileResult] = useState<ReconcileResult | null>(null);

  const loadZReport = useCallback(async () => {
    try {
      setError('');
      const data = await apiService.getZReport(reportDate);
      setZReport(data as ZReport);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load Z-Report');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [reportDate]);

  useEffect(() => {
    loadZReport();
  }, [loadZReport]);

  const onRefresh = () => {
    setRefreshing(true);
    loadZReport();
  };

  const handleReconcile = async () => {
    if (!cashAmount) {
      Alert.alert('Error', 'Please enter the actual cash amount');
      return;
    }

    setReconciling(true);
    try {
      const result = await apiService.reconcileCash(
        parseFloat(cashAmount),
        reportDate,
        reconcileNotes
      );
      setReconcileResult(result as ReconcileResult);
      setCashAmount('');
      setReconcileNotes('');
      Alert.alert('Success', 'Cash drawer reconciled successfully');
    } catch (err: unknown) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to reconcile cash');
    } finally {
      setReconciling(false);
    }
  };

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const changeDate = (days: number) => {
    const date = new Date(reportDate);
    date.setDate(date.getDate() + days);
    const today = new Date();
    if (date <= today) {
      setReportDate(date.toISOString().split('T')[0]);
      setLoading(true);
    }
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
        <Text style={styles.title}>End of Day</Text>
        <Text style={styles.subtitle}>Z-Report & Reconciliation</Text>
      </View>

      {/* Date Selector */}
      <View style={styles.dateSelector}>
        <TouchableOpacity style={styles.dateArrow} onPress={() => changeDate(-1)}>
          <Ionicons name="chevron-back" size={24} color="#94a3b8" />
        </TouchableOpacity>
        <View style={styles.dateDisplay}>
          <Ionicons name="calendar" size={20} color="#0ea5e9" />
          <Text style={styles.dateText}>{reportDate}</Text>
        </View>
        <TouchableOpacity
          style={styles.dateArrow}
          onPress={() => changeDate(1)}
          disabled={reportDate === new Date().toISOString().split('T')[0]}
        >
          <Ionicons
            name="chevron-forward"
            size={24}
            color={reportDate === new Date().toISOString().split('T')[0] ? '#334155' : '#94a3b8'}
          />
        </TouchableOpacity>
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
            <TouchableOpacity style={styles.retryButton} onPress={loadZReport}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : zReport ? (
          <>
            {/* Report Info */}
            <View style={styles.infoCard}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Report Date</Text>
                <Text style={styles.infoValue}>{zReport.report_date}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Generated At</Text>
                <Text style={styles.infoValue}>{zReport.report_time}</Text>
              </View>
            </View>

            {/* Summary Cards */}
            <View style={styles.summaryGrid}>
              <View style={styles.summaryCard}>
                <Text style={styles.cardLabel}>Total Sales</Text>
                <Text style={styles.cardValue}>{zReport.total_sales}</Text>
                <Text style={styles.cardSubtext}>{zReport.items_sold} items</Text>
              </View>
              <View style={[styles.summaryCard, styles.revenueCard]}>
                <Text style={styles.cardLabel}>Revenue</Text>
                <Text style={[styles.cardValue, styles.revenueValue]}>
                  {formatCurrency(zReport.total_revenue)}
                </Text>
                <Text style={styles.cardSubtext}>Tax: {formatCurrency(zReport.total_tax)}</Text>
              </View>
            </View>

            <View style={styles.summaryGrid}>
              <View style={styles.summaryCard}>
                <Text style={styles.cardLabel}>Discounts</Text>
                <Text style={[styles.cardValue, styles.discountValue]}>
                  -{formatCurrency(zReport.total_discount)}
                </Text>
              </View>
              <View style={styles.summaryCard}>
                <Text style={styles.cardLabel}>Refunds</Text>
                <Text style={[styles.cardValue, styles.refundValue]}>
                  -{formatCurrency(zReport.refund_amount)}
                </Text>
                <Text style={styles.cardSubtext}>{zReport.total_refunds} refunds</Text>
              </View>
            </View>

            {/* Payment Methods */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Payment Breakdown</Text>
              {zReport.payment_methods && zReport.payment_methods.length > 0 ? (
                zReport.payment_methods.map((pm, index) => (
                  <View key={index} style={styles.paymentRow}>
                    <View style={styles.paymentInfo}>
                      <Text style={styles.paymentMethod}>{pm.method}</Text>
                      <Text style={styles.paymentCount}>{pm.count} transactions</Text>
                    </View>
                    <View style={styles.paymentRight}>
                      <Text style={styles.paymentRevenue}>{formatCurrency(pm.revenue)}</Text>
                      <Text style={styles.paymentPercent}>{pm.percentage.toFixed(1)}%</Text>
                    </View>
                    <View
                      style={[styles.percentBar, { width: `${Math.min(pm.percentage, 100)}%` }]}
                    />
                  </View>
                ))
              ) : (
                <Text style={styles.emptyText}>No payment data</Text>
              )}
            </View>

            {/* Top Products */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Top Products</Text>
              {zReport.top_products && zReport.top_products.slice(0, 5).map((product, index) => (
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
                  <Text style={styles.productRevenue}>{formatCurrency(product.revenue)}</Text>
                </View>
              ))}
            </View>

            {/* Cash Reconciliation */}
            <View style={styles.section}>
              <TouchableOpacity
                style={styles.reconcileHeader}
                onPress={() => setShowReconcile(!showReconcile)}
              >
                <Ionicons name="calculator" size={24} color="#0ea5e9" />
                <Text style={styles.sectionTitle}>Cash Reconciliation</Text>
                <Ionicons
                  name={showReconcile ? 'chevron-up' : 'chevron-down'}
                  size={24}
                  color="#64748b"
                />
              </TouchableOpacity>

              {showReconcile && (
                <View style={styles.reconcileContent}>
                  <Text style={styles.reconcileLabel}>Actual Cash in Drawer</Text>
                  <TextInput
                    style={styles.input}
                    value={cashAmount}
                    onChangeText={setCashAmount}
                    placeholder="0.00"
                    placeholderTextColor="#64748b"
                    keyboardType="decimal-pad"
                  />

                  <Text style={styles.reconcileLabel}>Notes (Optional)</Text>
                  <TextInput
                    style={[styles.input, styles.textArea]}
                    value={reconcileNotes}
                    onChangeText={setReconcileNotes}
                    placeholder="Any discrepancy notes..."
                    placeholderTextColor="#64748b"
                    multiline
                    numberOfLines={3}
                  />

                  <TouchableOpacity
                    style={[styles.reconcileButton, reconciling && styles.buttonDisabled]}
                    onPress={handleReconcile}
                    disabled={reconciling}
                  >
                    {reconciling ? (
                      <ActivityIndicator size="small" color="#ffffff" />
                    ) : (
                      <>
                        <Ionicons name="checkmark-circle" size={20} color="#ffffff" />
                        <Text style={styles.buttonText}>Reconcile Cash</Text>
                      </>
                    )}
                  </TouchableOpacity>

                  {reconcileResult && (
                    <View
                      style={[
                        styles.resultCard,
                        reconcileResult.difference === 0
                          ? styles.resultSuccess
                          : styles.resultWarning,
                      ]}
                    >
                      <Text style={styles.resultTitle}>
                        {reconcileResult.difference === 0
                          ? '✓ Cash Balanced'
                          : '⚠ Discrepancy Found'}
                      </Text>
                      <View style={styles.resultRow}>
                        <Text style={styles.resultLabel}>Expected:</Text>
                        <Text style={styles.resultValue}>
                          {formatCurrency(reconcileResult.expected_cash)}
                        </Text>
                      </View>
                      <View style={styles.resultRow}>
                        <Text style={styles.resultLabel}>Actual:</Text>
                        <Text style={styles.resultValue}>
                          {formatCurrency(reconcileResult.actual_cash)}
                        </Text>
                      </View>
                      <View style={styles.resultRow}>
                        <Text style={styles.resultLabel}>Difference:</Text>
                        <Text
                          style={[
                            styles.resultValue,
                            reconcileResult.difference !== 0 && styles.differenceValue,
                          ]}
                        >
                          {formatCurrency(reconcileResult.difference)}
                        </Text>
                      </View>
                    </View>
                  )}
                </View>
              )}
            </View>
          </>
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons name="document-text-outline" size={64} color="#475569" />
            <Text style={styles.emptyText}>No report data for this date</Text>
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
  dateSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#ffffff',
    marginTop: 1,
  },
  dateArrow: {
    padding: 8,
  },
  dateDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginHorizontal: 16,
    gap: 8,
  },
  dateText: {
    color: '#0f172a',
    fontSize: 16,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  infoCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  infoLabel: {
    color: '#64748b',
    fontSize: 14,
  },
  infoValue: {
    color: '#0f172a',
    fontSize: 14,
    fontWeight: '600',
  },
  summaryGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  revenueCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#10b981',
  },
  cardLabel: {
    color: '#64748b',
    fontSize: 12,
  },
  cardValue: {
    color: '#0f172a',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 4,
  },
  revenueValue: {
    color: '#10b981',
  },
  discountValue: {
    color: '#f59e0b',
  },
  refundValue: {
    color: '#ef4444',
  },
  cardSubtext: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 4,
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
    flex: 1,
  },
  paymentRow: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
    position: 'relative',
    overflow: 'hidden',
  },
  paymentInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  paymentMethod: {
    color: '#0f172a',
    fontSize: 15,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  paymentCount: {
    color: '#94a3b8',
    fontSize: 13,
  },
  paymentRight: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  paymentRevenue: {
    color: '#10b981',
    fontWeight: '600',
  },
  paymentPercent: {
    color: '#94a3b8',
    fontSize: 13,
  },
  percentBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    height: 2,
    backgroundColor: '#0ea5e9',
    borderRadius: 1,
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
  reconcileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  reconcileContent: {
    marginTop: 16,
  },
  reconcileLabel: {
    color: '#64748b',
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 12,
    color: '#0f172a',
    fontSize: 16,
    marginBottom: 16,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  reconcileButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0ea5e9',
    paddingVertical: 14,
    borderRadius: 8,
    gap: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultCard: {
    marginTop: 16,
    padding: 16,
    borderRadius: 8,
  },
  resultSuccess: {
    backgroundColor: '#dcfce7',
    borderWidth: 1,
    borderColor: '#10b981',
  },
  resultWarning: {
    backgroundColor: '#fef3c7',
    borderWidth: 1,
    borderColor: '#f59e0b',
  },
  resultTitle: {
    color: '#0f172a',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  resultLabel: {
    color: '#64748b',
  },
  resultValue: {
    color: '#0f172a',
    fontWeight: '500',
  },
  differenceValue: {
    color: '#f59e0b',
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
    color: '#94a3b8',
    fontSize: 16,
    marginTop: 12,
  },
});
