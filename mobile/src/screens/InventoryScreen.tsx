/**
 * Inventory Screen - Inventory management and stock adjustments
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
  Modal,
  Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';
import { useSyncStore } from '../store/syncStore';

interface InventoryItem {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  min_quantity: number;
  price: number;
  category: string;
  low_stock_threshold?: number;
  last_updated?: string;
}

type AdjustmentType = 'add' | 'remove' | 'set' | 'count';

export const InventoryScreen: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [adjustmentType, setAdjustmentType] = useState<AdjustmentType>('add');
  const [adjustmentQty, setAdjustmentQty] = useState('');
  const [adjustmentNotes, setAdjustmentNotes] = useState('');

  const { isOnline, addPendingAction } = useSyncStore();
  const queryClient = useQueryClient();

  const {
    data: inventory = [],
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<InventoryItem[]>({
    queryKey: ['inventory', searchQuery],
    queryFn: async () => {
      const data = await apiService.getInventory();
      let items = data as InventoryItem[];
      
      if (searchQuery) {
        const lower = searchQuery.toLowerCase();
        items = items.filter(
          (item) =>
            item.product_name.toLowerCase().includes(lower) ||
            item.sku.toLowerCase().includes(lower)
        );
      }
      
      return items;
    },
    enabled: isOnline,
  });

  const { data: lowStockAlerts = [] } = useQuery<InventoryItem[]>({
    queryKey: ['lowStockAlerts'],
    queryFn: () => apiService.getLowStockAlerts() as Promise<InventoryItem[]>,
    enabled: isOnline,
  });

  const adjustMutation = useMutation({
    mutationFn: async (data: { product_id: number; quantity: number; type: string; notes?: string }) => {
      if (isOnline) {
        return apiService.updateInventory(data);
      } else {
        addPendingAction('inventory_update', data);
        return data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['lowStockAlerts'] });
      setShowAdjustModal(false);
      resetAdjustForm();
      Alert.alert('Success', 'Inventory updated successfully');
    },
    onError: (error: unknown) => {
      Alert.alert('Error', error instanceof Error ? error.message : 'Failed to update inventory');
    },
  });

  const resetAdjustForm = () => {
    setSelectedItem(null);
    setAdjustmentType('add');
    setAdjustmentQty('');
    setAdjustmentNotes('');
  };

  const openAdjustModal = (item: InventoryItem) => {
    setSelectedItem(item);
    setShowAdjustModal(true);
  };

  const handleAdjust = () => {
    if (!selectedItem || !adjustmentQty) {
      Alert.alert('Error', 'Please enter a quantity');
      return;
    }

    const qty = parseInt(adjustmentQty, 10);
    if (isNaN(qty) || qty < 0) {
      Alert.alert('Error', 'Please enter a valid quantity');
      return;
    }

    let newQuantity: number;
    switch (adjustmentType) {
      case 'add':
        newQuantity = selectedItem.quantity + qty;
        break;
      case 'remove':
        newQuantity = Math.max(0, selectedItem.quantity - qty);
        break;
      case 'set':
      case 'count':
        newQuantity = qty;
        break;
      default:
        newQuantity = qty;
    }

    adjustMutation.mutate({
      product_id: selectedItem.product_id,
      quantity: newQuantity,
      type: adjustmentType,
      notes: adjustmentNotes || undefined,
    });
  };

  const getStockStatus = (item: InventoryItem) => {
    if (item.quantity <= 0) {
      return { icon: 'alert-circle', color: '#ef4444' };
    }
    if (item.quantity <= item.low_stock_threshold) {
      return { icon: 'warning', color: '#f59e0b' };
    }
    return { icon: 'checkmark-circle', color: '#22c55e' };
  };

  const renderItem = ({ item }: { item: InventoryItem }) => {
    const status = getStockStatus(item);
    
    return (
      <TouchableOpacity
        style={styles.itemCard}
        onPress={() => openAdjustModal(item)}
        activeOpacity={0.7}
      >
        <View style={styles.itemStatus}>
          <Ionicons name={status.icon as keyof typeof Ionicons.glyphMap} size={20} color={status.color} />
        </View>
        
        <View style={styles.itemInfo}>
          <Text style={styles.itemName} numberOfLines={1}>{item.product_name}</Text>
          <Text style={styles.itemSku}>SKU: {item.sku}</Text>
        </View>

        <View style={styles.itemQuantity}>
          <Text style={[styles.quantityValue, { color: status.color }]}>{item.quantity}</Text>
          <Text style={styles.quantityLabel}>units</Text>
        </View>

        <Ionicons name="chevron-forward" size={20} color="#475569" />
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Inventory</Text>
        {!isOnline && (
          <View style={styles.offlineBadge}>
            <Ionicons name="cloud-offline" size={14} color="#fbbf24" />
            <Text style={styles.offlineText}>Offline</Text>
          </View>
        )}
      </View>

      {/* Low Stock Alerts */}
      {lowStockAlerts.length > 0 && (
        <View style={styles.alertBanner}>
          <Ionicons name="warning" size={18} color="#f59e0b" />
          <Text style={styles.alertText}>
            {lowStockAlerts.length} product{lowStockAlerts.length > 1 ? 's' : ''} low on stock
          </Text>
        </View>
      )}

      {/* Search */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#64748b" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search inventory..."
          placeholderTextColor="#64748b"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color="#64748b" />
          </TouchableOpacity>
        )}
      </View>

      {/* Summary Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{inventory.length}</Text>
          <Text style={styles.statLabel}>Products</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statValue}>
            {inventory.reduce((sum, item) => sum + item.quantity, 0)}
          </Text>
          <Text style={styles.statLabel}>Total Units</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#f59e0b' }]}>{lowStockAlerts.length}</Text>
          <Text style={styles.statLabel}>Low Stock</Text>
        </View>
      </View>

      {/* Inventory List */}
      {isLoading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#0ea5e9" />
        </View>
      ) : (
        <FlatList
          data={inventory}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#0ea5e9"
              colors={['#0ea5e9']}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="cube-outline" size={64} color="#334155" />
              <Text style={styles.emptyText}>No inventory items</Text>
            </View>
          }
        />
      )}

      {/* Adjust Modal */}
      <Modal
        visible={showAdjustModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAdjustModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Adjust Inventory</Text>
              <TouchableOpacity onPress={() => setShowAdjustModal(false)}>
                <Ionicons name="close" size={24} color="#94a3b8" />
              </TouchableOpacity>
            </View>

            {selectedItem && (
              <>
                <View style={styles.selectedProduct}>
                  <Text style={styles.selectedProductName}>{selectedItem.product_name}</Text>
                  <Text style={styles.selectedProductStock}>
                    Current stock: {selectedItem.quantity}
                  </Text>
                </View>

                <Text style={styles.fieldLabel}>Adjustment Type</Text>
                <View style={styles.adjustmentTypes}>
                  {(['add', 'remove', 'set', 'count'] as AdjustmentType[]).map((type) => (
                    <TouchableOpacity
                      key={type}
                      style={[
                        styles.typeButton,
                        adjustmentType === type && styles.typeButtonActive,
                      ]}
                      onPress={() => setAdjustmentType(type)}
                    >
                      <Text
                        style={[
                          styles.typeButtonText,
                          adjustmentType === type && styles.typeButtonTextActive,
                        ]}
                      >
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <Text style={styles.fieldLabel}>Quantity</Text>
                <TextInput
                  style={styles.quantityInput}
                  value={adjustmentQty}
                  onChangeText={setAdjustmentQty}
                  placeholder="Enter quantity"
                  placeholderTextColor="#64748b"
                  keyboardType="number-pad"
                />

                <Text style={styles.fieldLabel}>Notes (Optional)</Text>
                <TextInput
                  style={[styles.quantityInput, styles.notesInput]}
                  value={adjustmentNotes}
                  onChangeText={setAdjustmentNotes}
                  placeholder="Add notes..."
                  placeholderTextColor="#64748b"
                  multiline
                />

                <TouchableOpacity
                  style={styles.saveButton}
                  onPress={handleAdjust}
                  disabled={adjustMutation.isPending}
                >
                  {adjustMutation.isPending ? (
                    <ActivityIndicator color="#ffffff" />
                  ) : (
                    <Text style={styles.saveButtonText}>Save Adjustment</Text>
                  )}
                </TouchableOpacity>
              </>
            )}
          </View>
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  offlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef3c7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  offlineText: {
    color: '#d97706',
    fontSize: 12,
    fontWeight: '500',
  },
  alertBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef3c7',
    marginHorizontal: 16,
    marginTop: 12,
    padding: 12,
    borderRadius: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: '#fcd34d',
  },
  alertText: {
    color: '#92400e',
    fontSize: 14,
    fontWeight: '500',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    color: '#0f172a',
    fontSize: 16,
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#e2e8f0',
    marginVertical: 4,
  },
  statValue: {
    color: '#0f172a',
    fontSize: 22,
    fontWeight: '700',
  },
  statLabel: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 2,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
  },
  itemCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  itemStatus: {
    marginRight: 12,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    color: '#0f172a',
    fontSize: 15,
    fontWeight: '600',
  },
  itemSku: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 2,
  },
  itemQuantity: {
    alignItems: 'center',
    marginRight: 8,
  },
  quantityValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  quantityLabel: {
    color: '#64748b',
    fontSize: 10,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    paddingTop: 64,
  },
  emptyText: {
    color: '#64748b',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    color: '#0f172a',
    fontSize: 20,
    fontWeight: '600',
  },
  selectedProduct: {
    backgroundColor: '#f1f5f9',
    padding: 12,
    borderRadius: 10,
    marginBottom: 20,
  },
  selectedProductName: {
    color: '#0f172a',
    fontSize: 16,
    fontWeight: '600',
  },
  selectedProductStock: {
    color: '#64748b',
    fontSize: 14,
    marginTop: 4,
  },
  fieldLabel: {
    color: '#64748b',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  adjustmentTypes: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  typeButton: {
    flex: 1,
    backgroundColor: '#f1f5f9',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  typeButtonActive: {
    backgroundColor: '#0ea5e9',
  },
  typeButtonText: {
    color: '#64748b',
    fontSize: 13,
    fontWeight: '500',
  },
  typeButtonTextActive: {
    color: '#ffffff',
  },
  quantityInput: {
    backgroundColor: '#f8fafc',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#0f172a',
    fontSize: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  notesInput: {
    height: 80,
    textAlignVertical: 'top',
  },
  saveButton: {
    backgroundColor: '#0ea5e9',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  saveButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default InventoryScreen;
