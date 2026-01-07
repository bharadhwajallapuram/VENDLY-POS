/**
 * Held Orders Modal - View and recall parked orders
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  FlatList,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useOrdersStore, HeldOrder } from '../store/ordersStore';

interface HeldOrdersModalProps {
  visible: boolean;
  onClose: () => void;
  onRecallOrder: (order: HeldOrder) => void;
}

export const HeldOrdersModal: React.FC<HeldOrdersModalProps> = ({
  visible,
  onClose,
  onRecallOrder,
}) => {
  const { heldOrders, deleteHeldOrder } = useOrdersStore();

  const handleRecall = (order: HeldOrder) => {
    Alert.alert(
      'Recall Order',
      `Load "${order.name}" into cart? Current cart items will be replaced.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Recall',
          onPress: () => {
            onRecallOrder(order);
            onClose();
          },
        },
      ]
    );
  };

  const handleDelete = (orderId: string, orderName: string) => {
    Alert.alert(
      'Delete Order',
      `Delete "${orderName}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteHeldOrder(orderId),
        },
      ]
    );
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (date: Date) => {
    const d = new Date(date);
    const today = new Date();
    const isToday = d.toDateString() === today.toDateString();
    
    if (isToday) {
      return `Today, ${formatTime(date)}`;
    }
    
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderOrder = ({ item }: { item: HeldOrder }) => (
    <View style={styles.orderCard}>
      <View style={styles.orderHeader}>
        <View>
          <Text style={styles.orderName}>{item.name}</Text>
          <Text style={styles.orderTime}>{formatDate(item.createdAt)}</Text>
        </View>
        <Text style={styles.orderTotal}>${item.total.toFixed(2)}</Text>
      </View>

      {item.customerName && (
        <View style={styles.customerRow}>
          <Ionicons name="person-outline" size={14} color="#64748b" />
          <Text style={styles.customerName}>{item.customerName}</Text>
        </View>
      )}

      <View style={styles.itemsList}>
        {item.items.slice(0, 3).map((orderItem, index) => (
          <Text key={index} style={styles.itemText}>
            {orderItem.quantity}× {orderItem.name}
          </Text>
        ))}
        {item.items.length > 3 && (
          <Text style={styles.moreItems}>
            +{item.items.length - 3} more items
          </Text>
        )}
      </View>

      {item.notes && (
        <View style={styles.notesRow}>
          <Ionicons name="document-text-outline" size={14} color="#64748b" />
          <Text style={styles.notesText} numberOfLines={1}>{item.notes}</Text>
        </View>
      )}

      <View style={styles.orderActions}>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDelete(item.id, item.name)}
        >
          <Ionicons name="trash-outline" size={18} color="#ef4444" />
          <Text style={styles.deleteButtonText}>Delete</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.recallButton}
          onPress={() => handleRecall(item)}
        >
          <Ionicons name="arrow-redo-outline" size={18} color="#fff" />
          <Text style={styles.recallButtonText}>Recall</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Held Orders</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#94a3b8" />
            </TouchableOpacity>
          </View>

          {/* Orders List */}
          <FlatList
            data={heldOrders}
            keyExtractor={item => item.id}
            renderItem={renderOrder}
            contentContainerStyle={styles.listContent}
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <Ionicons name="pause-circle-outline" size={64} color="#334155" />
                <Text style={styles.emptyTitle}>No Held Orders</Text>
                <Text style={styles.emptySubtext}>
                  Use the &quot;Hold&quot; button to save orders for later
                </Text>
              </View>
            }
          />

          {/* Order Count */}
          {heldOrders.length > 0 && (
            <View style={styles.footer}>
              <Text style={styles.footerText}>
                {heldOrders.length} order{heldOrders.length !== 1 ? 's' : ''} on hold
              </Text>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#1e293b',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    minHeight: '60%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  closeButton: {
    padding: 4,
  },
  listContent: {
    padding: 16,
  },
  orderCard: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  orderName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  orderTime: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  orderTotal: {
    fontSize: 18,
    fontWeight: '700',
    color: '#22c55e',
  },
  customerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
  },
  customerName: {
    fontSize: 13,
    color: '#94a3b8',
  },
  itemsList: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  itemText: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 4,
  },
  moreItems: {
    fontSize: 12,
    color: '#64748b',
    fontStyle: 'italic',
    marginTop: 4,
  },
  notesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  notesText: {
    flex: 1,
    fontSize: 12,
    color: '#64748b',
    fontStyle: 'italic',
  },
  orderActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  deleteButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    backgroundColor: '#450a0a',
    borderRadius: 8,
  },
  deleteButtonText: {
    fontSize: 14,
    color: '#ef4444',
    fontWeight: '500',
  },
  recallButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    backgroundColor: '#3b82f6',
    borderRadius: 8,
  },
  recallButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#64748b',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#475569',
    marginTop: 4,
    textAlign: 'center',
  },
  footer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#64748b',
  },
});

export default HeldOrdersModal;
