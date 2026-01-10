/**
 * Payments Screen - Payment processing and history
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
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';

interface Sale {
  id: number;
  total: number;
  payment_method: string;
  status: string;
  created_at: string;
  items_count?: number;
  customer_name?: string;
}

type PaymentMethod = 'all' | 'cash' | 'card' | 'upi';

const PAYMENT_METHODS: { key: PaymentMethod; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { key: 'all', label: 'All', icon: 'list' },
  { key: 'cash', label: 'Cash', icon: 'cash' },
  { key: 'card', label: 'Card', icon: 'card' },
  { key: 'upi', label: 'UPI', icon: 'phone-portrait' },
];

export function PaymentsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sales, setSales] = useState<Sale[]>([]);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<PaymentMethod>('all');
  const [todayStats, setTodayStats] = useState({
    totalTransactions: 0,
    totalAmount: 0,
    cashAmount: 0,
    cardAmount: 0,
    upiAmount: 0,
  });

  const loadPayments = useCallback(async () => {
    try {
      setError('');
      const today = new Date().toISOString().split('T')[0];
      const data = await apiService.getSales({ date: today, limit: 50 });
      
      // Calculate stats
      const salesArray = Array.isArray(data) ? data : [];
      const stats = {
        totalTransactions: salesArray.length,
        totalAmount: 0,
        cashAmount: 0,
        cardAmount: 0,
        upiAmount: 0,
      };

      salesArray.forEach((sale: any) => {
        const amount = sale.total || 0;
        stats.totalAmount += amount;
        
        const method = (sale.payment_method || '').toLowerCase();
        if (method === 'cash') stats.cashAmount += amount;
        else if (method.includes('card') || method === 'stripe') stats.cardAmount += amount;
        else if (method === 'upi') stats.upiAmount += amount;
      });

      setTodayStats(stats);
      setSales(salesArray);
    } catch (err: any) {
      setError(err.message || 'Failed to load payments');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadPayments();
  }, [loadPayments]);

  const onRefresh = () => {
    setRefreshing(true);
    loadPayments();
  };

  const filteredSales = sales.filter((sale) => {
    if (filter === 'all') return true;
    const method = (sale.payment_method || '').toLowerCase();
    if (filter === 'card') return method.includes('card') || method === 'stripe';
    return method === filter;
  });

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getPaymentIcon = (method: string): keyof typeof Ionicons.glyphMap => {
    const m = method.toLowerCase();
    if (m === 'cash') return 'cash';
    if (m.includes('card') || m === 'stripe') return 'card';
    if (m === 'upi') return 'phone-portrait';
    return 'wallet';
  };

  const getPaymentColor = (method: string) => {
    const m = method.toLowerCase();
    if (m === 'cash') return '#10b981';
    if (m.includes('card') || m === 'stripe') return '#3b82f6';
    if (m === 'upi') return '#8b5cf6';
    return '#64748b';
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return '#10b981';
      case 'pending':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      default:
        return '#64748b';
    }
  };

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Payments</Text>
        <Text style={styles.subtitle}>Today's transactions</Text>
      </View>

      {/* Today's Summary */}
      <View style={styles.summaryContainer}>
        <View style={styles.summaryMain}>
          <Text style={styles.summaryLabel}>Today's Total</Text>
          <Text style={styles.summaryValue}>{formatCurrency(todayStats.totalAmount)}</Text>
          <Text style={styles.summarySubtext}>
            {todayStats.totalTransactions} transactions
          </Text>
        </View>
        <View style={styles.summaryBreakdown}>
          <View style={styles.breakdownRow}>
            <Ionicons name="cash" size={16} color="#10b981" />
            <Text style={styles.breakdownLabel}>Cash</Text>
            <Text style={[styles.breakdownValue, { color: '#10b981' }]}>
              {formatCurrency(todayStats.cashAmount)}
            </Text>
          </View>
          <View style={styles.breakdownRow}>
            <Ionicons name="card" size={16} color="#3b82f6" />
            <Text style={styles.breakdownLabel}>Card</Text>
            <Text style={[styles.breakdownValue, { color: '#3b82f6' }]}>
              {formatCurrency(todayStats.cardAmount)}
            </Text>
          </View>
          <View style={styles.breakdownRow}>
            <Ionicons name="phone-portrait" size={16} color="#8b5cf6" />
            <Text style={styles.breakdownLabel}>UPI</Text>
            <Text style={[styles.breakdownValue, { color: '#8b5cf6' }]}>
              {formatCurrency(todayStats.upiAmount)}
            </Text>
          </View>
        </View>
      </View>

      {/* Filter Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
        <View style={styles.filterContainer}>
          {PAYMENT_METHODS.map((method) => (
            <TouchableOpacity
              key={method.key}
              style={[styles.filterButton, filter === method.key && styles.filterButtonActive]}
              onPress={() => setFilter(method.key)}
            >
              <Ionicons
                name={method.icon}
                size={18}
                color={filter === method.key ? '#ffffff' : '#94a3b8'}
              />
              <Text style={[styles.filterText, filter === method.key && styles.filterTextActive]}>
                {method.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Transaction List */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3b82f6" />
        }
      >
        {error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={48} color="#ef4444" />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={loadPayments}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : filteredSales.length > 0 ? (
          filteredSales.map((sale) => (
            <TouchableOpacity
              key={sale.id}
              style={styles.transactionCard}
              onPress={() =>
                Alert.alert(
                  `Transaction #${sale.id}`,
                  `Amount: ${formatCurrency(sale.total)}\nMethod: ${sale.payment_method}\nStatus: ${sale.status}`,
                  [{ text: 'OK' }]
                )
              }
            >
              <View
                style={[
                  styles.paymentIcon,
                  { backgroundColor: `${getPaymentColor(sale.payment_method)}20` },
                ]}
              >
                <Ionicons
                  name={getPaymentIcon(sale.payment_method)}
                  size={24}
                  color={getPaymentColor(sale.payment_method)}
                />
              </View>
              <View style={styles.transactionInfo}>
                <Text style={styles.transactionId}>#{sale.id}</Text>
                <Text style={styles.transactionMeta}>
                  {sale.payment_method} • {formatTime(sale.created_at)}
                </Text>
              </View>
              <View style={styles.transactionRight}>
                <Text style={styles.transactionAmount}>{formatCurrency(sale.total)}</Text>
                <View
                  style={[
                    styles.statusBadge,
                    { backgroundColor: `${getStatusColor(sale.status)}20` },
                  ]}
                >
                  <Text style={[styles.statusText, { color: getStatusColor(sale.status) }]}>
                    {sale.status}
                  </Text>
                </View>
              </View>
            </TouchableOpacity>
          ))
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons name="wallet-outline" size={64} color="#475569" />
            <Text style={styles.emptyText}>No transactions found</Text>
            <Text style={styles.emptySubtext}>
              {filter !== 'all' ? `No ${filter} payments today` : 'Start a sale to see transactions'}
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  header: {
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 20,
    backgroundColor: '#1e293b',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#f1f5f9',
  },
  subtitle: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  summaryContainer: {
    flexDirection: 'row',
    margin: 16,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    overflow: 'hidden',
  },
  summaryMain: {
    flex: 1,
    padding: 20,
    backgroundColor: '#3b82f6',
    alignItems: 'center',
  },
  summaryLabel: {
    color: '#ffffff',
    opacity: 0.8,
    fontSize: 13,
  },
  summaryValue: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  summarySubtext: {
    color: '#ffffff',
    opacity: 0.7,
    fontSize: 12,
  },
  summaryBreakdown: {
    flex: 1,
    padding: 16,
    justifyContent: 'center',
  },
  breakdownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  breakdownLabel: {
    color: '#94a3b8',
    fontSize: 13,
    marginLeft: 8,
    flex: 1,
  },
  breakdownValue: {
    fontWeight: '600',
    fontSize: 14,
  },
  filterScroll: {
    maxHeight: 50,
  },
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#1e293b',
    borderRadius: 20,
    gap: 6,
  },
  filterButtonActive: {
    backgroundColor: '#3b82f6',
  },
  filterText: {
    color: '#94a3b8',
    fontWeight: '500',
  },
  filterTextActive: {
    color: '#ffffff',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  transactionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  paymentIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  transactionInfo: {
    flex: 1,
  },
  transactionId: {
    color: '#f1f5f9',
    fontSize: 16,
    fontWeight: '600',
  },
  transactionMeta: {
    color: '#64748b',
    fontSize: 13,
    marginTop: 2,
  },
  transactionRight: {
    alignItems: 'flex-end',
  },
  transactionAmount: {
    color: '#f1f5f9',
    fontSize: 18,
    fontWeight: 'bold',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginTop: 4,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
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
    backgroundColor: '#3b82f6',
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
    fontSize: 18,
    fontWeight: '600',
    marginTop: 12,
  },
  emptySubtext: {
    color: '#64748b',
    fontSize: 14,
    marginTop: 4,
  },
});
