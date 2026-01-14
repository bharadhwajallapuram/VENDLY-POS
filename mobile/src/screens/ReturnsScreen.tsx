/**
 * Returns Screen - Process returns, refunds, and exchanges
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  FlatList,
  Alert,
  Modal,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';
import { useAuthStore } from '../store/authStore';

interface SaleItem {
  id: number;
  product_name: string;
  sku?: string;
  quantity: number;
  unit_price: number;
  discount?: number;
}

interface Sale {
  id: number;
  receipt_number?: string;
  created_at: string;
  total: number;
  items?: SaleItem[];
  payment_method: string;
  customer_name?: string;
  status: string;
}

interface ReturnItem {
  id: number;
  name: string;
  sku: string;
  quantity: number;
  maxQuantity: number;
  price: number;
  selected: boolean;
  returnQuantity: number;
  reason?: string;
}

const RETURN_REASONS = [
  'Defective/Damaged',
  'Wrong Item',
  'Changed Mind',
  'Not as Described',
  'Better Price Found',
  'Other',
];

export const ReturnsScreen: React.FC = () => {
  const { user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null);
  const [returnItems, setReturnItems] = useState<ReturnItem[]>([]);
  const [showReasonModal, setShowReasonModal] = useState(false);
  const [currentItemId, setCurrentItemId] = useState<number | null>(null);
  const [refundMethod, setRefundMethod] = useState<'original' | 'store_credit'>('original');
  const [processing, setProcessing] = useState(false);
  const [notes, setNotes] = useState('');

  const loadSales = useCallback(async () => {
    try {
      const data = await apiService.getSales({ limit: 100 });
      // Filter only completed sales that can be refunded
      const refundableSales = (data as Sale[]).filter(
        s => s.status === 'completed' || s.status === 'partially_refunded'
      );
      setSales(refundableSales);
    } catch (_err) {
      Alert.alert('Error', 'Failed to load sales');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadSales();
  }, [loadSales]);

  const onRefresh = () => {
    setRefreshing(true);
    loadSales();
  };

  const filteredSales = sales.filter(sale => {
    const query = searchQuery.toLowerCase();
    return (
      (sale.receipt_number || `#${sale.id}`).toLowerCase().includes(query) ||
      sale.customer_name?.toLowerCase().includes(query)
    );
  });

  const handleSelectSale = async (sale: Sale) => {
    try {
      // Fetch full sale details with items
      const fullSale = await apiService.getSale(sale.id) as Sale;
      setSelectedSale(fullSale);
      
      // Transform items for return processing
      const items: ReturnItem[] = (fullSale.items || []).map(item => ({
        id: item.id,
        name: item.product_name,
        sku: item.sku || '',
        quantity: item.quantity,
        maxQuantity: item.quantity,
        price: item.unit_price,
        selected: false,
        returnQuantity: 1,
      }));
      setReturnItems(items);
    } catch (_err) {
      Alert.alert('Error', 'Failed to load sale details');
    }
  };

  const toggleItemSelection = (itemId: number) => {
    setReturnItems(items =>
      items.map(item =>
        item.id === itemId ? { ...item, selected: !item.selected } : item
      )
    );
  };

  const updateReturnQuantity = (itemId: number, quantity: number) => {
    setReturnItems(items =>
      items.map(item =>
        item.id === itemId ? { ...item, returnQuantity: Math.min(quantity, item.maxQuantity) } : item
      )
    );
  };

  const openReasonModal = (itemId: number) => {
    setCurrentItemId(itemId);
    setShowReasonModal(true);
  };

  const selectReason = (reason: string) => {
    if (currentItemId !== null) {
      setReturnItems(items =>
        items.map(item =>
          item.id === currentItemId ? { ...item, reason } : item
        )
      );
    }
    setShowReasonModal(false);
  };

  const selectedItems = returnItems.filter(item => item.selected);
  const refundSubtotal = selectedItems.reduce(
    (sum, item) => sum + item.price * item.returnQuantity,
    0
  );
  const refundTax = refundSubtotal * 0.08875;
  const refundTotal = refundSubtotal + refundTax;

  const handleProcessReturn = async () => {
    if (selectedItems.length === 0) {
      Alert.alert('Error', 'Please select items to return');
      return;
    }

    const missingReasons = selectedItems.filter(item => !item.reason);
    if (missingReasons.length > 0) {
      Alert.alert('Error', 'Please select a reason for each return item');
      return;
    }

    Alert.alert(
      'Confirm Return',
      `Process return for ${selectedItems.length} item(s)?\nRefund Amount: $${refundTotal.toFixed(2)}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Process Return',
          onPress: async () => {
            setProcessing(true);
            try {
              // Call API to process refund
              const refundItems = selectedItems.map(item => ({
                sale_item_id: item.id,
                quantity: item.returnQuantity,
              }));
              
              await apiService.refundSale(
                selectedSale!.id,
                refundItems,
                user?.id?.toString()
              );

              Alert.alert(
                'Return Processed',
                `Refund of $${refundTotal.toFixed(2)} has been processed via ${refundMethod === 'original' ? 'original payment method' : 'store credit'}.`,
                [
                  {
                    text: 'OK',
                    onPress: () => {
                      setSelectedSale(null);
                      setReturnItems([]);
                      setNotes('');
                      loadSales(); // Refresh the sales list
                    },
                  },
                ]
              );
            } catch (_err) {
              Alert.alert('Error', 'Failed to process refund. Please try again.');
            } finally {
              setProcessing(false);
            }
          },
        },
      ]
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Returns & Refunds</Text>
      </View>

      {!selectedSale ? (
        /* Receipt Search */
        <View style={styles.searchSection}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={20} color="#64748b" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search by receipt # or customer name"
              placeholderTextColor="#64748b"
              value={searchQuery}
              onChangeText={setSearchQuery}
            />
            <TouchableOpacity style={styles.scanButton}>
              <Ionicons name="scan-outline" size={22} color="#3b82f6" />
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3b82f6" />
              <Text style={styles.loadingText}>Loading sales...</Text>
            </View>
          ) : (
          <FlatList
            data={filteredSales}
            keyExtractor={item => String(item.id)}
            contentContainerStyle={styles.salesList}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.saleCard}
                onPress={() => handleSelectSale(item)}
              >
                <View style={styles.saleHeader}>
                  <View>
                    <Text style={styles.receiptNumber}>{item.receipt_number || `#${item.id}`}</Text>
                    <Text style={styles.saleDate}>{formatDate(item.created_at)}</Text>
                  </View>
                  <Text style={styles.saleTotal}>${item.total.toFixed(2)}</Text>
                </View>
                {item.customer_name && (
                  <Text style={styles.customerName}>
                    <Ionicons name="person-outline" size={12} color="#64748b" /> {item.customer_name}
                  </Text>
                )}
                <View style={styles.saleFooter}>
                  <View style={styles.statusBadge}>
                    <Text style={styles.statusText}>{item.status}</Text>
                  </View>
                  <View style={styles.paymentBadge}>
                    <Ionicons
                      name={item.payment_method === 'cash' ? 'cash-outline' : 'card-outline'}
                      size={14}
                      color="#94a3b8"
                    />
                    <Text style={styles.paymentText}>{item.payment_method}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <Ionicons name="receipt-outline" size={64} color="#334155" />
                <Text style={styles.emptyText}>No receipts found</Text>
                <Text style={styles.emptySubtext}>
                  Search by receipt number or scan a receipt barcode
                </Text>
              </View>
            }
          />
        )}
        </View>
      ) : (
        /* Return Process */
        <ScrollView style={styles.returnProcess}>
          {/* Sale Info */}
          <View style={styles.saleInfo}>
            <View style={styles.saleInfoRow}>
              <Text style={styles.saleInfoLabel}>Receipt:</Text>
              <Text style={styles.saleInfoValue}>{selectedSale.receipt_number || `#${selectedSale.id}`}</Text>
            </View>
            <View style={styles.saleInfoRow}>
              <Text style={styles.saleInfoLabel}>Date:</Text>
              <Text style={styles.saleInfoValue}>{formatDate(selectedSale.created_at)}</Text>
            </View>
            <TouchableOpacity
              style={styles.changeSaleButton}
              onPress={() => setSelectedSale(null)}
            >
              <Text style={styles.changeSaleText}>Change Receipt</Text>
            </TouchableOpacity>
          </View>

          {/* Items Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Select Items to Return</Text>
            {returnItems.map(item => (
              <View key={item.id} style={styles.returnItemCard}>
                <TouchableOpacity
                  style={styles.checkbox}
                  onPress={() => toggleItemSelection(item.id)}
                >
                  <Ionicons
                    name={item.selected ? 'checkbox' : 'square-outline'}
                    size={24}
                    color={item.selected ? '#3b82f6' : '#64748b'}
                  />
                </TouchableOpacity>
                <View style={styles.returnItemInfo}>
                  <Text style={styles.returnItemName}>{item.name}</Text>
                  <Text style={styles.returnItemSku}>SKU: {item.sku}</Text>
                  <Text style={styles.returnItemPrice}>${item.price.toFixed(2)} each</Text>
                </View>
                {item.selected && (
                  <View style={styles.returnItemActions}>
                    <View style={styles.quantityControl}>
                      <TouchableOpacity
                        style={styles.qtyButton}
                        onPress={() => updateReturnQuantity(item.id, item.returnQuantity - 1)}
                        disabled={item.returnQuantity <= 1}
                      >
                        <Ionicons name="remove" size={18} color="#f1f5f9" />
                      </TouchableOpacity>
                      <Text style={styles.qtyValue}>{item.returnQuantity}</Text>
                      <TouchableOpacity
                        style={styles.qtyButton}
                        onPress={() => updateReturnQuantity(item.id, item.returnQuantity + 1)}
                        disabled={item.returnQuantity >= item.maxQuantity}
                      >
                        <Ionicons name="add" size={18} color="#f1f5f9" />
                      </TouchableOpacity>
                    </View>
                    <TouchableOpacity
                      style={[styles.reasonButton, item.reason && styles.reasonButtonSelected]}
                      onPress={() => openReasonModal(item.id)}
                    >
                      <Text style={[styles.reasonButtonText, item.reason && styles.reasonButtonTextSelected]}>
                        {item.reason || 'Select Reason'}
                      </Text>
                      <Ionicons name="chevron-down" size={16} color="#64748b" />
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            ))}
          </View>

          {/* Refund Method */}
          {selectedItems.length > 0 && (
            <>
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Refund Method</Text>
                <View style={styles.refundMethods}>
                  <TouchableOpacity
                    style={[styles.refundMethodCard, refundMethod === 'original' && styles.refundMethodActive]}
                    onPress={() => setRefundMethod('original')}
                  >
                    <Ionicons
                      name={selectedSale.paymentMethod === 'Cash' ? 'cash-outline' : 'card-outline'}
                      size={24}
                      color={refundMethod === 'original' ? '#3b82f6' : '#64748b'}
                    />
                    <Text style={[styles.refundMethodText, refundMethod === 'original' && styles.refundMethodTextActive]}>
                      Original Method ({selectedSale.paymentMethod})
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.refundMethodCard, refundMethod === 'store_credit' && styles.refundMethodActive]}
                    onPress={() => setRefundMethod('store_credit')}
                  >
                    <Ionicons
                      name="wallet-outline"
                      size={24}
                      color={refundMethod === 'store_credit' ? '#3b82f6' : '#64748b'}
                    />
                    <Text style={[styles.refundMethodText, refundMethod === 'store_credit' && styles.refundMethodTextActive]}>
                      Store Credit
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Notes */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Notes (Optional)</Text>
                <TextInput
                  style={styles.notesInput}
                  placeholder="Add any notes about this return..."
                  placeholderTextColor="#64748b"
                  value={notes}
                  onChangeText={setNotes}
                  multiline
                  numberOfLines={3}
                />
              </View>

              {/* Refund Summary */}
              <View style={styles.refundSummary}>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Items ({selectedItems.length})</Text>
                  <Text style={styles.summaryValue}>${refundSubtotal.toFixed(2)}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Tax Refund</Text>
                  <Text style={styles.summaryValue}>${refundTax.toFixed(2)}</Text>
                </View>
                <View style={[styles.summaryRow, styles.totalRow]}>
                  <Text style={styles.totalLabel}>Total Refund</Text>
                  <Text style={styles.totalValue}>${refundTotal.toFixed(2)}</Text>
                </View>
              </View>
            </>
          )}
        </ScrollView>
      )}

      {/* Process Button */}
      {selectedSale && selectedItems.length > 0 && (
        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.processButton, processing && styles.processButtonDisabled]}
            onPress={handleProcessReturn}
            disabled={processing}
          >
            {processing ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <>
                <Ionicons name="refresh-outline" size={22} color="#fff" />
                <Text style={styles.processButtonText}>
                  Process Return - ${refundTotal.toFixed(2)}
                </Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Reason Selection Modal */}
      <Modal
        visible={showReasonModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowReasonModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Select Return Reason</Text>
            {RETURN_REASONS.map(reason => (
              <TouchableOpacity
                key={reason}
                style={styles.reasonOption}
                onPress={() => selectReason(reason)}
              >
                <Text style={styles.reasonOptionText}>{reason}</Text>
                <Ionicons name="chevron-forward" size={20} color="#64748b" />
              </TouchableOpacity>
            ))}
            <TouchableOpacity
              style={styles.modalCancelButton}
              onPress={() => setShowReasonModal(false)}
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 16,
    paddingHorizontal: 16,
    backgroundColor: '#1e293b',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  searchSection: {
    flex: 1,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    margin: 16,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    color: '#f1f5f9',
    fontSize: 16,
  },
  scanButton: {
    padding: 8,
  },
  salesList: {
    padding: 16,
  },
  saleCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  saleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  receiptNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  saleDate: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  saleTotal: {
    fontSize: 18,
    fontWeight: '700',
    color: '#22c55e',
  },
  customerName: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 8,
  },
  saleFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  itemCount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  itemCountText: {
    fontSize: 13,
    color: '#64748b',
  },
  paymentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  paymentText: {
    fontSize: 13,
    color: '#94a3b8',
    textTransform: 'capitalize',
  },
  statusBadge: {
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 12,
    color: '#60a5fa',
    textTransform: 'capitalize',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 48,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#64748b',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 18,
    color: '#64748b',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#475569',
    marginTop: 4,
    textAlign: 'center',
  },
  returnProcess: {
    flex: 1,
  },
  saleInfo: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  saleInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  saleInfoLabel: {
    fontSize: 14,
    color: '#64748b',
  },
  saleInfoValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#f1f5f9',
  },
  changeSaleButton: {
    marginTop: 12,
  },
  changeSaleText: {
    fontSize: 14,
    color: '#3b82f6',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  returnItemCard: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  checkbox: {
    marginRight: 12,
    justifyContent: 'center',
  },
  returnItemInfo: {
    flex: 1,
  },
  returnItemName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  returnItemSku: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  returnItemPrice: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  returnItemActions: {
    alignItems: 'flex-end',
    gap: 8,
  },
  quantityControl: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  qtyButton: {
    backgroundColor: '#3b82f6',
    width: 28,
    height: 28,
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  qtyValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
    minWidth: 24,
    textAlign: 'center',
  },
  reasonButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: '#0f172a',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  reasonButtonSelected: {
    borderColor: '#3b82f6',
    backgroundColor: '#1e3a5f',
  },
  reasonButtonText: {
    fontSize: 12,
    color: '#64748b',
  },
  reasonButtonTextSelected: {
    color: '#3b82f6',
  },
  refundMethods: {
    gap: 8,
  },
  refundMethodCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1e293b',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  refundMethodActive: {
    borderColor: '#3b82f6',
    backgroundColor: '#1e3a5f',
  },
  refundMethodText: {
    fontSize: 15,
    color: '#94a3b8',
  },
  refundMethodTextActive: {
    color: '#f1f5f9',
  },
  notesInput: {
    backgroundColor: '#1e293b',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    color: '#f1f5f9',
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#334155',
    textAlignVertical: 'top',
  },
  refundSummary: {
    backgroundColor: '#1e293b',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#94a3b8',
  },
  summaryValue: {
    fontSize: 14,
    color: '#f1f5f9',
  },
  totalRow: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#22c55e',
  },
  footer: {
    padding: 16,
    paddingBottom: 32,
    backgroundColor: '#1e293b',
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  processButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#ef4444',
    paddingVertical: 16,
    borderRadius: 12,
  },
  processButtonDisabled: {
    opacity: 0.7,
  },
  processButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#1e293b',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 32,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f1f5f9',
    marginBottom: 16,
    textAlign: 'center',
  },
  reasonOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  reasonOptionText: {
    fontSize: 16,
    color: '#f1f5f9',
  },
  modalCancelButton: {
    marginTop: 16,
    paddingVertical: 14,
    alignItems: 'center',
  },
  modalCancelText: {
    fontSize: 16,
    color: '#94a3b8',
  },
});

export default ReturnsScreen;
