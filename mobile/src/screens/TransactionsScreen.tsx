/**
 * Transactions Screen - List of all sales transactions
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Modal,
  ScrollView,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';

interface SaleItem {
  id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  discount: number;
  total: number;
}

interface Transaction {
  id: number;
  user_id: number;
  customer_id: number | null;
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  payment_method: string;
  payment_reference: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  items?: SaleItem[];
}

// Helper to format date as YYYY-MM-DD in local timezone
const formatLocalDate = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

type DateFilter = 'today' | 'week' | 'month' | 'all';

export const TransactionsScreen: React.FC = () => {
  const [dateFilter, setDateFilter] = useState<DateFilter>('today');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [showModal, setShowModal] = useState(false);

  const getDateRange = useCallback(() => {
    const today = new Date();
    let startDate: Date | null = null;
    
    switch (dateFilter) {
      case 'today':
        startDate = new Date(today);
        break;
      case 'week':
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 7);
        break;
      case 'month':
        startDate = new Date(today);
        startDate.setMonth(today.getMonth() - 1);
        break;
      default:
        startDate = null;
    }
    
    return {
      startDate: startDate ? formatLocalDate(startDate) : null,
      endDate: formatLocalDate(today),
    };
  }, [dateFilter]);

  const {
    data: transactions = [],
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<Transaction[]>({
    queryKey: ['transactions', dateFilter],
    queryFn: async () => {
      const { startDate, endDate } = getDateRange();
      const data = await apiService.getSales({ limit: 200 });
      
      // Filter by date range on client side
      if (startDate) {
        return (data as Transaction[]).filter(t => {
          const txDate = formatLocalDate(new Date(t.created_at));
          return txDate >= startDate && txDate <= endDate;
        });
      }
      
      return data as Transaction[];
    },
  });

  // Sort by date (newest first)
  const sortedTransactions = [...transactions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#22c55e';
      case 'refunded':
      case 'partially_refunded':
        return '#ef4444';
      case 'pending':
        return '#f59e0b';
      default:
        return '#64748b';
    }
  };

  const getPaymentIcon = (method: string): keyof typeof Ionicons.glyphMap => {
    switch (method?.toLowerCase()) {
      case 'cash':
        return 'cash-outline';
      case 'card':
      case 'credit':
      case 'debit':
        return 'card-outline';
      case 'mobile':
      case 'upi':
        return 'phone-portrait-outline';
      default:
        return 'wallet-outline';
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const openDetails = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setShowModal(true);
  };

  const renderTransaction = ({ item }: { item: Transaction }) => (
    <TouchableOpacity style={styles.transactionCard} onPress={() => openDetails(item)}>
      <View style={styles.transactionLeft}>
        <View style={[styles.paymentIcon, { backgroundColor: '#e0f2fe' }]}>
          <Ionicons name={getPaymentIcon(item.payment_method)} size={20} color="#0ea5e9" />
        </View>
        <View style={styles.transactionInfo}>
          <Text style={styles.transactionId}>#{item.id}</Text>
          <Text style={styles.transactionTime}>{formatTime(item.created_at)}</Text>
          <View style={styles.statusBadge}>
            <View style={[styles.statusDot, { backgroundColor: getStatusColor(item.status) }]} />
            <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
              {item.status}
            </Text>
          </View>
        </View>
      </View>
      <View style={styles.transactionRight}>
        <Text style={styles.transactionTotal}>${item.total?.toFixed(2) || '0.00'}</Text>
        <Text style={styles.paymentMethod}>{item.payment_method}</Text>
      </View>
    </TouchableOpacity>
  );

  const totalRevenue = sortedTransactions.reduce((sum, t) => sum + (t.total || 0), 0);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Transactions</Text>
        <Text style={styles.headerSubtitle}>
          {sortedTransactions.length} transactions • ${totalRevenue.toFixed(2)}
        </Text>
      </View>

      {/* Date Filter */}
      <View style={styles.filterContainer}>
        {(['today', 'week', 'month', 'all'] as DateFilter[]).map((filter) => (
          <TouchableOpacity
            key={filter}
            style={[styles.filterButton, dateFilter === filter && styles.filterButtonActive]}
            onPress={() => setDateFilter(filter)}
          >
            <Text style={[styles.filterText, dateFilter === filter && styles.filterTextActive]}>
              {filter === 'today' ? 'Today' : filter === 'week' ? '7 Days' : filter === 'month' ? '30 Days' : 'All'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Transactions List */}
      {isLoading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#0ea5e9" />
        </View>
      ) : sortedTransactions.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="receipt-outline" size={64} color="#cbd5e1" />
          <Text style={styles.emptyText}>No transactions found</Text>
          <Text style={styles.emptySubtext}>Transactions will appear here after sales</Text>
        </View>
      ) : (
        <FlatList
          data={sortedTransactions}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderTransaction}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#0ea5e9"
            />
          }
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}

      {/* Transaction Details Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Transaction #{selectedTransaction?.id}</Text>
            <TouchableOpacity onPress={() => setShowModal(false)}>
              <Ionicons name="close" size={24} color="#64748b" />
            </TouchableOpacity>
          </View>
          
          {selectedTransaction && (
            <ScrollView style={styles.modalContent}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Date</Text>
                <Text style={styles.detailValue}>{formatDate(selectedTransaction.created_at)}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Time</Text>
                <Text style={styles.detailValue}>{formatTime(selectedTransaction.created_at)}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Status</Text>
                <Text style={[styles.detailValue, { color: getStatusColor(selectedTransaction.status) }]}>
                  {selectedTransaction.status}
                </Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Payment</Text>
                <Text style={styles.detailValue}>{selectedTransaction.payment_method}</Text>
              </View>
              
              <View style={styles.divider} />
              
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Subtotal</Text>
                <Text style={styles.detailValue}>${selectedTransaction.subtotal?.toFixed(2)}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Tax</Text>
                <Text style={styles.detailValue}>${selectedTransaction.tax?.toFixed(2)}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Discount</Text>
                <Text style={styles.detailValue}>-${selectedTransaction.discount?.toFixed(2)}</Text>
              </View>
              
              <View style={styles.divider} />
              
              <View style={styles.detailRow}>
                <Text style={styles.totalLabel}>Total</Text>
                <Text style={styles.totalValue}>${selectedTransaction.total?.toFixed(2)}</Text>
              </View>

              {selectedTransaction.items && selectedTransaction.items.length > 0 && (
                <>
                  <View style={styles.divider} />
                  <Text style={styles.itemsHeader}>Items</Text>
                  {selectedTransaction.items.map((item, index) => (
                    <View key={index} style={styles.itemRow}>
                      <Text style={styles.itemName}>{item.product_name || `Product #${item.product_id}`}</Text>
                      <Text style={styles.itemQty}>x{item.quantity}</Text>
                      <Text style={styles.itemPrice}>${item.total?.toFixed(2)}</Text>
                    </View>
                  ))}
                </>
              )}
            </ScrollView>
          )}
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    backgroundColor: '#ffffff',
    paddingHorizontal: 16,
    paddingTop: 60,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0f172a',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  filterButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    alignItems: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#0ea5e9',
    borderColor: '#0ea5e9',
  },
  filterText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748b',
  },
  filterTextActive: {
    color: '#ffffff',
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#64748b',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  listContent: {
    padding: 16,
  },
  transactionCard: {
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
    flexDirection: 'row',
    alignItems: 'center',
  },
  paymentIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  transactionInfo: {
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
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  transactionRight: {
    alignItems: 'flex-end',
  },
  transactionTotal: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
  },
  paymentMethod: {
    fontSize: 12,
    color: '#64748b',
    textTransform: 'capitalize',
    marginTop: 2,
  },
  separator: {
    height: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
  },
  modalContent: {
    padding: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
  detailLabel: {
    fontSize: 14,
    color: '#64748b',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0f172a',
  },
  divider: {
    height: 1,
    backgroundColor: '#e2e8f0',
    marginVertical: 8,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
  },
  totalValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0ea5e9',
  },
  itemsHeader: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0f172a',
    marginBottom: 12,
    marginTop: 8,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  itemName: {
    flex: 1,
    fontSize: 14,
    color: '#0f172a',
  },
  itemQty: {
    fontSize: 14,
    color: '#64748b',
    marginRight: 16,
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0f172a',
  },
});
