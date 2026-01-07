/**
 * Customer Select Modal
 * Search and select customers, view loyalty points, create new customers
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  FlatList,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import debounce from 'lodash.debounce';
import {
  Button,
  Input,
  Avatar,
  Badge,
  EmptyState,
  colors,
  spacing,
  radius,
  fontSize,
  fontWeight,
} from '../ui';

interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  loyalty_points: number;
  total_purchases: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  created_at: string;
}

interface CustomerSelectModalProps {
  visible: boolean;
  onClose: () => void;
  onSelectCustomer: (customer: Customer | null) => void;
  currentCustomer: Customer | null;
}

// Mock customers - would come from API
const MOCK_CUSTOMERS: Customer[] = [
  { id: 1, name: 'John Smith', email: 'john@example.com', phone: '555-0101', loyalty_points: 1250, total_purchases: 45, tier: 'gold', created_at: '2024-01-15' },
  { id: 2, name: 'Sarah Johnson', email: 'sarah@example.com', phone: '555-0102', loyalty_points: 3500, total_purchases: 120, tier: 'platinum', created_at: '2023-06-20' },
  { id: 3, name: 'Michael Brown', email: 'mike@example.com', phone: '555-0103', loyalty_points: 450, total_purchases: 15, tier: 'silver', created_at: '2024-08-10' },
  { id: 4, name: 'Emily Davis', email: 'emily@example.com', phone: '555-0104', loyalty_points: 150, total_purchases: 5, tier: 'bronze', created_at: '2024-11-01' },
  { id: 5, name: 'David Wilson', email: 'david@example.com', phone: '555-0105', loyalty_points: 890, total_purchases: 32, tier: 'silver', created_at: '2024-03-25' },
];

const TIER_COLORS = {
  bronze: { bg: '#451a03', text: '#fbbf24' },
  silver: { bg: '#334155', text: '#cbd5e1' },
  gold: { bg: '#422006', text: '#fcd34d' },
  platinum: { bg: '#1e1b4b', text: '#a5b4fc' },
};

export const CustomerSelectModal: React.FC<CustomerSelectModalProps> = ({
  visible,
  onClose,
  onSelectCustomer,
  currentCustomer,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [customers, setCustomers] = useState<Customer[]>(MOCK_CUSTOMERS);
  const [loading, setLoading] = useState(false);
  const [showNewCustomerForm, setShowNewCustomerForm] = useState(false);
  const [newCustomer, setNewCustomer] = useState({ name: '', email: '', phone: '' });

  const searchCustomers = useCallback(
    debounce(async (query: string) => {
      setLoading(true);
      // Simulate API search
      await new Promise(resolve => setTimeout(resolve, 300));
      
      if (!query.trim()) {
        setCustomers(MOCK_CUSTOMERS);
      } else {
        const lower = query.toLowerCase();
        setCustomers(
          MOCK_CUSTOMERS.filter(
            c =>
              c.name.toLowerCase().includes(lower) ||
              c.email.toLowerCase().includes(lower) ||
              c.phone.includes(query)
          )
        );
      }
      setLoading(false);
    }, 300),
    []
  );

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    searchCustomers(query);
  };

  const handleSelectCustomer = (customer: Customer) => {
    onSelectCustomer(customer);
    onClose();
  };

  const handleRemoveCustomer = () => {
    onSelectCustomer(null);
    onClose();
  };

  const handleCreateCustomer = () => {
    if (!newCustomer.name.trim()) {
      Alert.alert('Error', 'Please enter customer name');
      return;
    }

    // Create new customer (would call API)
    const created: Customer = {
      id: Date.now(),
      name: newCustomer.name,
      email: newCustomer.email,
      phone: newCustomer.phone,
      loyalty_points: 0,
      total_purchases: 0,
      tier: 'bronze',
      created_at: new Date().toISOString(),
    };

    Alert.alert('Success', 'Customer created successfully', [
      {
        text: 'Use Customer',
        onPress: () => {
          onSelectCustomer(created);
          onClose();
        },
      },
    ]);
  };

  const renderCustomer = ({ item }: { item: Customer }) => {
    const tierColor = TIER_COLORS[item.tier];
    const isSelected = currentCustomer?.id === item.id;

    return (
      <TouchableOpacity
        style={[styles.customerCard, isSelected && styles.customerCardSelected]}
        onPress={() => handleSelectCustomer(item)}
      >
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{item.name.charAt(0).toUpperCase()}</Text>
        </View>
        <View style={styles.customerInfo}>
          <View style={styles.nameRow}>
            <Text style={styles.customerName}>{item.name}</Text>
            <View style={[styles.tierBadge, { backgroundColor: tierColor.bg }]}>
              <Text style={[styles.tierText, { color: tierColor.text }]}>
                {item.tier.toUpperCase()}
              </Text>
            </View>
          </View>
          <Text style={styles.customerEmail}>{item.email}</Text>
          <View style={styles.statsRow}>
            <View style={styles.stat}>
              <Ionicons name="star" size={12} color="#fbbf24" />
              <Text style={styles.statText}>{item.loyalty_points.toLocaleString()} pts</Text>
            </View>
            <View style={styles.stat}>
              <Ionicons name="bag-handle-outline" size={12} color="#64748b" />
              <Text style={styles.statText}>{item.total_purchases} orders</Text>
            </View>
          </View>
        </View>
        {isSelected && (
          <Ionicons name="checkmark-circle" size={24} color="#22c55e" />
        )}
      </TouchableOpacity>
    );
  };

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
            <Text style={styles.headerTitle}>
              {showNewCustomerForm ? 'New Customer' : 'Select Customer'}
            </Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#94a3b8" />
            </TouchableOpacity>
          </View>

          {!showNewCustomerForm ? (
            <>
              {/* Search */}
              <View style={styles.searchContainer}>
                <Ionicons name="search" size={20} color="#64748b" />
                <TextInput
                  style={styles.searchInput}
                  placeholder="Search by name, email, or phone"
                  placeholderTextColor="#64748b"
                  value={searchQuery}
                  onChangeText={handleSearch}
                  autoCapitalize="none"
                />
                {searchQuery.length > 0 && (
                  <TouchableOpacity onPress={() => handleSearch('')}>
                    <Ionicons name="close-circle" size={20} color="#64748b" />
                  </TouchableOpacity>
                )}
              </View>

              {/* Current Customer */}
              {currentCustomer && (
                <View style={styles.currentCustomerSection}>
                  <Text style={styles.sectionLabel}>Current Customer</Text>
                  <View style={styles.currentCustomerCard}>
                    <Text style={styles.currentCustomerName}>{currentCustomer.name}</Text>
                    <TouchableOpacity
                      style={styles.removeButton}
                      onPress={handleRemoveCustomer}
                    >
                      <Ionicons name="person-remove-outline" size={18} color="#ef4444" />
                      <Text style={styles.removeButtonText}>Remove</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}

              {/* Customer List */}
              {loading ? (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="large" color="#3b82f6" />
                </View>
              ) : (
                <FlatList
                  data={customers}
                  keyExtractor={item => item.id.toString()}
                  renderItem={renderCustomer}
                  contentContainerStyle={styles.listContent}
                  ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                      <Ionicons name="people-outline" size={48} color="#64748b" />
                      <Text style={styles.emptyText}>No customers found</Text>
                      <TouchableOpacity
                        style={styles.createButton}
                        onPress={() => setShowNewCustomerForm(true)}
                      >
                        <Ionicons name="add" size={20} color="#fff" />
                        <Text style={styles.createButtonText}>Create New Customer</Text>
                      </TouchableOpacity>
                    </View>
                  }
                />
              )}

              {/* New Customer Button */}
              {customers.length > 0 && (
                <TouchableOpacity
                  style={styles.newCustomerButton}
                  onPress={() => setShowNewCustomerForm(true)}
                >
                  <Ionicons name="person-add-outline" size={20} color="#3b82f6" />
                  <Text style={styles.newCustomerButtonText}>Create New Customer</Text>
                </TouchableOpacity>
              )}
            </>
          ) : (
            /* New Customer Form */
            <View style={styles.formContainer}>
              <View style={styles.formField}>
                <Text style={styles.formLabel}>Name *</Text>
                <TextInput
                  style={styles.formInput}
                  placeholder="Customer name"
                  placeholderTextColor="#64748b"
                  value={newCustomer.name}
                  onChangeText={name => setNewCustomer(prev => ({ ...prev, name }))}
                />
              </View>

              <View style={styles.formField}>
                <Text style={styles.formLabel}>Email</Text>
                <TextInput
                  style={styles.formInput}
                  placeholder="customer@email.com"
                  placeholderTextColor="#64748b"
                  value={newCustomer.email}
                  onChangeText={email => setNewCustomer(prev => ({ ...prev, email }))}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>

              <View style={styles.formField}>
                <Text style={styles.formLabel}>Phone</Text>
                <TextInput
                  style={styles.formInput}
                  placeholder="555-0100"
                  placeholderTextColor="#64748b"
                  value={newCustomer.phone}
                  onChangeText={phone => setNewCustomer(prev => ({ ...prev, phone }))}
                  keyboardType="phone-pad"
                />
              </View>

              <View style={styles.formButtons}>
                <TouchableOpacity
                  style={styles.cancelFormButton}
                  onPress={() => {
                    setShowNewCustomerForm(false);
                    setNewCustomer({ name: '', email: '', phone: '' });
                  }}
                >
                  <Text style={styles.cancelFormButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.submitFormButton}
                  onPress={handleCreateCustomer}
                >
                  <Text style={styles.submitFormButtonText}>Create Customer</Text>
                </TouchableOpacity>
              </View>
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
    minHeight: '70%',
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
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
  currentCustomerSection: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748b',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  currentCustomerCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#052e16',
    padding: 12,
    borderRadius: 8,
  },
  currentCustomerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#22c55e',
  },
  removeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  removeButtonText: {
    fontSize: 14,
    color: '#ef4444',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 48,
  },
  listContent: {
    padding: 16,
  },
  customerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  customerCardSelected: {
    borderColor: '#22c55e',
    backgroundColor: '#052e16',
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  customerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  customerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  tierBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  tierText: {
    fontSize: 10,
    fontWeight: '700',
  },
  customerEmail: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 6,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 12,
    color: '#64748b',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 12,
    marginBottom: 24,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  newCustomerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  newCustomerButtonText: {
    fontSize: 16,
    color: '#3b82f6',
    fontWeight: '600',
  },
  formContainer: {
    padding: 16,
  },
  formField: {
    marginBottom: 16,
  },
  formLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 8,
  },
  formInput: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#f1f5f9',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  formButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  cancelFormButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cancelFormButtonText: {
    color: '#94a3b8',
    fontSize: 16,
    fontWeight: '600',
  },
  submitFormButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: '#3b82f6',
    borderRadius: 8,
  },
  submitFormButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CustomerSelectModal;
