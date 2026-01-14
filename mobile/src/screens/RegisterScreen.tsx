/**
 * Register Screen - Cash drawer management, open/close register
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useCashDrawerStore, CashMovement, RegisterSession } from '../store/cashDrawerStore';
import { useAuthStore } from '../store/authStore';

type MovementType = 'cash_in' | 'cash_out' | 'drop';

export const RegisterScreen: React.FC = () => {
  const { user } = useAuthStore();
  const {
    currentSession,
    sessionHistory,
    openRegister,
    closeRegister,
    addCashMovement,
    getExpectedCash,
  } = useCashDrawerStore();

  const [showOpenModal, setShowOpenModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [openingFloat, setOpeningFloat] = useState('');
  const [actualCash, setActualCash] = useState('');
  const [cashAmount, setCashAmount] = useState('');
  const [cashReason, setCashReason] = useState('');
  const [cashType, setCashType] = useState<MovementType>('cash_in');

  const expectedCash = getExpectedCash();

  const handleOpenRegister = () => {
    const amount = parseFloat(openingFloat);
    if (isNaN(amount) || amount < 0) {
      Alert.alert('Error', 'Please enter a valid opening float amount');
      return;
    }

    openRegister(amount, String(user?.id || 'unknown'), user?.full_name || 'Unknown User');
    setShowOpenModal(false);
    setOpeningFloat('');
    Alert.alert('Register Opened', `Opening float: $${amount.toFixed(2)}`);
  };

  const handleCloseRegister = () => {
    const amount = parseFloat(actualCash);
    if (isNaN(amount) || amount < 0) {
      Alert.alert('Error', 'Please enter the actual cash amount');
      return;
    }

    const variance = amount - expectedCash;
    const varianceText = variance === 0 
      ? 'Perfect count!' 
      : variance > 0 
        ? `Over by $${variance.toFixed(2)}` 
        : `Short by $${Math.abs(variance).toFixed(2)}`;

    Alert.alert(
      'Close Register',
      `Expected: $${expectedCash.toFixed(2)}\nActual: $${amount.toFixed(2)}\n${varianceText}\n\nClose register?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Close',
          onPress: () => {
            closeRegister(amount, String(user?.id || 'unknown'), user?.full_name || 'Unknown User');
            setShowCloseModal(false);
            setActualCash('');
            Alert.alert('Register Closed', 'End of day report saved');
          },
        },
      ]
    );
  };

  const handleCashMovement = () => {
    const amount = parseFloat(cashAmount);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    addCashMovement(cashType, amount, cashReason || undefined);
    setShowCashModal(false);
    setCashAmount('');
    setCashReason('');
    Alert.alert('Success', `$${amount.toFixed(2)} ${cashType === 'cash_in' ? 'added to' : 'removed from'} register`);
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getMovementIcon = (type: CashMovement['type']) => {
    switch (type) {
      case 'sale': return 'cart-outline';
      case 'refund': return 'arrow-undo-outline';
      case 'cash_in': return 'add-circle-outline';
      case 'cash_out': return 'remove-circle-outline';
      case 'float': return 'wallet-outline';
      case 'drop': return 'archive-outline';
      default: return 'cash-outline';
    }
  };

  const getMovementColor = (type: CashMovement['type']) => {
    switch (type) {
      case 'sale':
      case 'cash_in':
      case 'float':
        return '#22c55e';
      case 'refund':
      case 'cash_out':
        return '#ef4444';
      default:
        return '#64748b';
    }
  };

  const renderSessionCard = ({ item }: { item: RegisterSession }) => (
    <View style={styles.historyCard}>
      <View style={styles.historyHeader}>
        <Text style={styles.historyDate}>{formatDate(item.openedAt)}</Text>
        <View style={[styles.statusBadge, item.status === 'closed' && styles.statusClosed]}>
          <Text style={styles.statusText}>{item.status}</Text>
        </View>
      </View>
      <View style={styles.historyStats}>
        <View style={styles.historyStat}>
          <Text style={styles.historyStatLabel}>Sales</Text>
          <Text style={styles.historyStatValue}>${item.totalSales.toFixed(2)}</Text>
        </View>
        <View style={styles.historyStat}>
          <Text style={styles.historyStatLabel}>Transactions</Text>
          <Text style={styles.historyStatValue}>{item.transactionCount}</Text>
        </View>
        {item.variance !== undefined && (
          <View style={styles.historyStat}>
            <Text style={styles.historyStatLabel}>Variance</Text>
            <Text style={[
              styles.historyStatValue,
              { color: item.variance === 0 ? '#22c55e' : '#ef4444' }
            ]}>
              ${item.variance.toFixed(2)}
            </Text>
          </View>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Register</Text>
        <TouchableOpacity
          style={styles.historyButton}
          onPress={() => setShowHistoryModal(true)}
        >
          <Ionicons name="time-outline" size={24} color="#f1f5f9" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {!currentSession ? (
          /* Register Closed State */
          <View style={styles.closedState}>
            <View style={styles.closedIcon}>
              <Ionicons name="lock-closed" size={64} color="#64748b" />
            </View>
            <Text style={styles.closedTitle}>Register Closed</Text>
            <Text style={styles.closedSubtext}>
              Open the register to start processing transactions
            </Text>
            <TouchableOpacity
              style={styles.openButton}
              onPress={() => setShowOpenModal(true)}
            >
              <Ionicons name="lock-open-outline" size={22} color="#fff" />
              <Text style={styles.openButtonText}>Open Register</Text>
            </TouchableOpacity>
          </View>
        ) : (
          /* Register Open State */
          <>
            {/* Session Info */}
            <View style={styles.sessionCard}>
              <View style={styles.sessionHeader}>
                <View style={styles.sessionStatus}>
                  <View style={styles.statusDot} />
                  <Text style={styles.sessionStatusText}>Register Open</Text>
                </View>
                <Text style={styles.sessionTime}>
                  Since {formatTime(currentSession.openedAt)}
                </Text>
              </View>
              <Text style={styles.sessionUser}>
                Opened by {currentSession.openedByName}
              </Text>
            </View>

            {/* Cash Summary */}
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Cash in Drawer</Text>
              <Text style={styles.summaryAmount}>${expectedCash.toFixed(2)}</Text>
              <View style={styles.summaryDetails}>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Opening Float</Text>
                  <Text style={styles.summaryValue}>${currentSession.openingFloat.toFixed(2)}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Cash Sales</Text>
                  <Text style={[styles.summaryValue, styles.positiveValue]}>
                    +${currentSession.totalSales.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Cash In</Text>
                  <Text style={[styles.summaryValue, styles.positiveValue]}>
                    +${currentSession.totalCashIn.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Cash Out</Text>
                  <Text style={[styles.summaryValue, styles.negativeValue]}>
                    -${currentSession.totalCashOut.toFixed(2)}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Refunds</Text>
                  <Text style={[styles.summaryValue, styles.negativeValue]}>
                    -${currentSession.totalRefunds.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>

            {/* Quick Actions */}
            <View style={styles.actionsGrid}>
              <TouchableOpacity
                style={styles.actionCard}
                onPress={() => {
                  setCashType('cash_in');
                  setShowCashModal(true);
                }}
              >
                <View style={[styles.actionIcon, { backgroundColor: '#052e16' }]}>
                  <Ionicons name="add" size={28} color="#22c55e" />
                </View>
                <Text style={styles.actionLabel}>Cash In</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionCard}
                onPress={() => {
                  setCashType('cash_out');
                  setShowCashModal(true);
                }}
              >
                <View style={[styles.actionIcon, { backgroundColor: '#450a0a' }]}>
                  <Ionicons name="remove" size={28} color="#ef4444" />
                </View>
                <Text style={styles.actionLabel}>Cash Out</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionCard}
                onPress={() => {
                  setCashType('drop');
                  setShowCashModal(true);
                }}
              >
                <View style={[styles.actionIcon, { backgroundColor: '#1e3a5f' }]}>
                  <Ionicons name="archive-outline" size={28} color="#3b82f6" />
                </View>
                <Text style={styles.actionLabel}>Safe Drop</Text>
              </TouchableOpacity>
            </View>

            {/* Recent Activity */}
            <View style={styles.activitySection}>
              <Text style={styles.sectionTitle}>Recent Activity</Text>
              {currentSession.movements.slice(-10).reverse().map((movement) => (
                <View key={movement.id} style={styles.activityRow}>
                  <View style={styles.activityIcon}>
                    <Ionicons
                      name={getMovementIcon(movement.type) as any}
                      size={20}
                      color={getMovementColor(movement.type)}
                    />
                  </View>
                  <View style={styles.activityInfo}>
                    <Text style={styles.activityType}>
                      {movement.type.replace('_', ' ').toUpperCase()}
                    </Text>
                    {movement.reason && (
                      <Text style={styles.activityReason}>{movement.reason}</Text>
                    )}
                  </View>
                  <View style={styles.activityRight}>
                    <Text style={[
                      styles.activityAmount,
                      { color: getMovementColor(movement.type) }
                    ]}>
                      {movement.amount >= 0 ? '+' : ''}{movement.amount.toFixed(2)}
                    </Text>
                    <Text style={styles.activityTime}>
                      {formatTime(movement.timestamp)}
                    </Text>
                  </View>
                </View>
              ))}
            </View>

            {/* Close Register Button */}
            <TouchableOpacity
              style={styles.closeRegisterButton}
              onPress={() => setShowCloseModal(true)}
            >
              <Ionicons name="lock-closed-outline" size={22} color="#fff" />
              <Text style={styles.closeRegisterText}>Close Register</Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>

      {/* Open Register Modal */}
      <Modal visible={showOpenModal} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Open Register</Text>
            <Text style={styles.modalLabel}>Opening Float</Text>
            <View style={styles.modalInputRow}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="0.00"
                placeholderTextColor="#64748b"
                value={openingFloat}
                onChangeText={setOpeningFloat}
                keyboardType="decimal-pad"
              />
            </View>
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalCancel}
                onPress={() => {
                  setShowOpenModal(false);
                  setOpeningFloat('');
                }}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSubmit} onPress={handleOpenRegister}>
                <Text style={styles.modalSubmitText}>Open Register</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Close Register Modal */}
      <Modal visible={showCloseModal} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Close Register</Text>
            <View style={styles.expectedCashBox}>
              <Text style={styles.expectedLabel}>Expected Cash</Text>
              <Text style={styles.expectedAmount}>${expectedCash.toFixed(2)}</Text>
            </View>
            <Text style={styles.modalLabel}>Actual Cash in Drawer</Text>
            <View style={styles.modalInputRow}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="0.00"
                placeholderTextColor="#64748b"
                value={actualCash}
                onChangeText={setActualCash}
                keyboardType="decimal-pad"
              />
            </View>
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalCancel}
                onPress={() => {
                  setShowCloseModal(false);
                  setActualCash('');
                }}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalSubmit, { backgroundColor: '#ef4444' }]}
                onPress={handleCloseRegister}
              >
                <Text style={styles.modalSubmitText}>Close Register</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Cash In/Out Modal */}
      <Modal visible={showCashModal} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>
              {cashType === 'cash_in' ? 'Cash In' : cashType === 'cash_out' ? 'Cash Out' : 'Safe Drop'}
            </Text>
            <Text style={styles.modalLabel}>Amount</Text>
            <View style={styles.modalInputRow}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="0.00"
                placeholderTextColor="#64748b"
                value={cashAmount}
                onChangeText={setCashAmount}
                keyboardType="decimal-pad"
              />
            </View>
            <Text style={styles.modalLabel}>Reason (Optional)</Text>
            <TextInput
              style={styles.reasonInput}
              placeholder="Enter reason..."
              placeholderTextColor="#64748b"
              value={cashReason}
              onChangeText={setCashReason}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalCancel}
                onPress={() => {
                  setShowCashModal(false);
                  setCashAmount('');
                  setCashReason('');
                }}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSubmit} onPress={handleCashMovement}>
                <Text style={styles.modalSubmitText}>Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* History Modal */}
      <Modal visible={showHistoryModal} animationType="slide">
        <View style={styles.historyContainer}>
          <View style={styles.historyHeader}>
            <Text style={styles.historyTitle}>Session History</Text>
            <TouchableOpacity onPress={() => setShowHistoryModal(false)}>
              <Ionicons name="close" size={24} color="#f1f5f9" />
            </TouchableOpacity>
          </View>
          <FlatList
            data={sessionHistory}
            keyExtractor={item => String(item.id)}
            renderItem={renderSessionCard}
            contentContainerStyle={styles.historyList}
            ListEmptyComponent={
              <View style={styles.emptyHistory}>
                <Ionicons name="receipt-outline" size={48} color="#334155" />
                <Text style={styles.emptyHistoryText}>No session history</Text>
              </View>
            }
          />
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
  historyButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  closedState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  closedIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#1e293b',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  closedTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#f1f5f9',
    marginBottom: 8,
  },
  closedSubtext: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 32,
  },
  openButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#22c55e',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  openButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  sessionCard: {
    backgroundColor: '#052e16',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#166534',
  },
  sessionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sessionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#22c55e',
  },
  sessionStatusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#22c55e',
  },
  sessionTime: {
    fontSize: 14,
    color: '#4ade80',
  },
  sessionUser: {
    fontSize: 14,
    color: '#86efac',
    marginTop: 8,
  },
  summaryCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  summaryTitle: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 4,
  },
  summaryAmount: {
    fontSize: 40,
    fontWeight: '700',
    color: '#f1f5f9',
    marginBottom: 16,
  },
  summaryDetails: {
    width: '100%',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#94a3b8',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  positiveValue: {
    color: '#22c55e',
  },
  negativeValue: {
    color: '#ef4444',
  },
  actionsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  actionCard: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  actionIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionLabel: {
    fontSize: 13,
    color: '#94a3b8',
    fontWeight: '500',
  },
  activitySection: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  activityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  activityIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityInfo: {
    flex: 1,
    marginLeft: 12,
  },
  activityType: {
    fontSize: 14,
    fontWeight: '500',
    color: '#f1f5f9',
  },
  activityReason: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  activityRight: {
    alignItems: 'flex-end',
  },
  activityAmount: {
    fontSize: 14,
    fontWeight: '600',
  },
  activityTime: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  closeRegisterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#ef4444',
    paddingVertical: 16,
    borderRadius: 12,
  },
  closeRegisterText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContainer: {
    width: '100%',
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#f1f5f9',
    marginBottom: 20,
    textAlign: 'center',
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 8,
  },
  modalInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 8,
    paddingHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  currencySymbol: {
    fontSize: 24,
    color: '#64748b',
  },
  modalInput: {
    flex: 1,
    fontSize: 24,
    fontWeight: '600',
    color: '#f1f5f9',
    paddingVertical: 14,
    textAlign: 'center',
  },
  reasonInput: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#f1f5f9',
    fontSize: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#334155',
  },
  expectedCashBox: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 20,
  },
  expectedLabel: {
    fontSize: 14,
    color: '#64748b',
  },
  expectedAmount: {
    fontSize: 28,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancel: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 8,
  },
  modalCancelText: {
    fontSize: 16,
    color: '#94a3b8',
    fontWeight: '600',
  },
  modalSubmit: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: '#22c55e',
    borderRadius: 8,
  },
  modalSubmitText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
  historyContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  historyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingBottom: 16,
    paddingHorizontal: 16,
    backgroundColor: '#1e293b',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  historyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  historyList: {
    padding: 16,
  },
  historyCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  historyDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  statusBadge: {
    backgroundColor: '#052e16',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusClosed: {
    backgroundColor: '#1e293b',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#22c55e',
    textTransform: 'uppercase',
  },
  historyStats: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 16,
  },
  historyStat: {
    flex: 1,
  },
  historyStatLabel: {
    fontSize: 12,
    color: '#64748b',
  },
  historyStatValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
    marginTop: 2,
  },
  emptyHistory: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyHistoryText: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 12,
  },
});

export default RegisterScreen;
