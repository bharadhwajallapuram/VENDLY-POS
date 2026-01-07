/**
 * Payment Modal Component
 * Advanced payment processing with multiple payment methods
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import {
  Button,
  Input,
  Card,
  colors,
  spacing,
  radius,
  fontSize,
  fontWeight,
} from '../ui';

interface PaymentModalProps {
  visible: boolean;
  onClose: () => void;
  onProcessPayment: (paymentData: PaymentData) => Promise<void>;
  total: number;
  subtotal: number;
  tax: number;
  discount: number;
}

export interface PaymentData {
  method: PaymentMethod;
  amount: number;
  splitPayments?: SplitPayment[];
  giftCardCode?: string;
  storeCredit?: number;
  cashTendered?: number;
  change?: number;
  tipAmount?: number;
}

export type PaymentMethod = 'cash' | 'card' | 'digital' | 'gift_card' | 'store_credit' | 'split';

interface SplitPayment {
  method: Exclude<PaymentMethod, 'split'>;
  amount: number;
}

const PAYMENT_METHODS = [
  { id: 'cash', label: 'Cash', icon: 'cash-outline' as const },
  { id: 'card', label: 'Card', icon: 'card-outline' as const },
  { id: 'digital', label: 'Apple/Google Pay', icon: 'phone-portrait-outline' as const },
  { id: 'gift_card', label: 'Gift Card', icon: 'gift-outline' as const },
  { id: 'store_credit', label: 'Store Credit', icon: 'wallet-outline' as const },
  { id: 'split', label: 'Split Payment', icon: 'git-branch-outline' as const },
];

const QUICK_CASH_AMOUNTS = [10, 20, 50, 100];

export const PaymentModal: React.FC<PaymentModalProps> = ({
  visible,
  onClose,
  onProcessPayment,
  total,
  subtotal,
  tax,
  discount,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('cash');
  const [cashTendered, setCashTendered] = useState('');
  const [giftCardCode, setGiftCardCode] = useState('');
  const [tipAmount, setTipAmount] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [splitPayments, setSplitPayments] = useState<SplitPayment[]>([]);
  const [splitMethod, setSplitMethod] = useState<Exclude<PaymentMethod, 'split'>>('cash');
  const [splitAmount, setSplitAmount] = useState('');

  const totalWithTip = total + tipAmount;
  const cashAmount = parseFloat(cashTendered) || 0;
  const change = cashAmount - totalWithTip;
  const splitRemaining = totalWithTip - splitPayments.reduce((sum, p) => sum + p.amount, 0);

  const handleTipSelection = (percentage: number) => {
    setTipAmount(Math.round(subtotal * percentage) / 100);
  };

  const handleAddSplitPayment = () => {
    const amount = parseFloat(splitAmount);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }
    if (amount > splitRemaining) {
      Alert.alert('Error', 'Amount exceeds remaining balance');
      return;
    }

    setSplitPayments([...splitPayments, { method: splitMethod, amount }]);
    setSplitAmount('');
  };

  const handleRemoveSplitPayment = (index: number) => {
    setSplitPayments(splitPayments.filter((_, i) => i !== index));
  };

  const handleProcessPayment = async () => {
    if (selectedMethod === 'cash' && cashAmount < totalWithTip) {
      Alert.alert('Insufficient Cash', 'Please enter amount equal to or greater than total');
      return;
    }

    if (selectedMethod === 'gift_card' && !giftCardCode.trim()) {
      Alert.alert('Error', 'Please enter gift card code');
      return;
    }

    if (selectedMethod === 'split' && splitRemaining > 0.01) {
      Alert.alert('Error', `Please add payments totaling $${splitRemaining.toFixed(2)} more`);
      return;
    }

    setProcessing(true);

    const paymentData: PaymentData = {
      method: selectedMethod,
      amount: totalWithTip,
      tipAmount: tipAmount > 0 ? tipAmount : undefined,
      cashTendered: selectedMethod === 'cash' ? cashAmount : undefined,
      change: selectedMethod === 'cash' && change > 0 ? change : undefined,
      giftCardCode: selectedMethod === 'gift_card' ? giftCardCode : undefined,
      splitPayments: selectedMethod === 'split' ? splitPayments : undefined,
    };

    try {
      await onProcessPayment(paymentData);
    } finally {
      setProcessing(false);
    }
  };

  const renderPaymentContent = () => {
    switch (selectedMethod) {
      case 'cash':
        return (
          <View style={styles.paymentContent}>
            <Text style={styles.amountDue}>Amount Due: ${totalWithTip.toFixed(2)}</Text>
            
            <View style={styles.quickAmounts}>
              {QUICK_CASH_AMOUNTS.map(amount => (
                <TouchableOpacity
                  key={amount}
                  style={[
                    styles.quickAmountButton,
                    amount >= totalWithTip && styles.quickAmountValid,
                  ]}
                  onPress={() => setCashTendered(amount.toString())}
                >
                  <Text style={styles.quickAmountText}>${amount}</Text>
                </TouchableOpacity>
              ))}
              <TouchableOpacity
                style={[styles.quickAmountButton, styles.quickAmountExact]}
                onPress={() => setCashTendered(totalWithTip.toFixed(2))}
              >
                <Text style={styles.quickAmountText}>Exact</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.cashInputRow}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.cashInput}
                placeholder="0.00"
                placeholderTextColor="#64748b"
                value={cashTendered}
                onChangeText={setCashTendered}
                keyboardType="decimal-pad"
              />
            </View>

            {cashAmount >= totalWithTip && (
              <View style={styles.changeBox}>
                <Text style={styles.changeLabel}>Change Due</Text>
                <Text style={styles.changeAmount}>${change.toFixed(2)}</Text>
              </View>
            )}
          </View>
        );

      case 'card':
        return (
          <View style={styles.paymentContent}>
            <View style={styles.cardReaderSection}>
              <Ionicons name="card" size={64} color="#3b82f6" />
              <Text style={styles.cardReaderText}>Ready for Card</Text>
              <Text style={styles.cardReaderSubtext}>
                Insert, swipe, or tap card on reader
              </Text>
            </View>

            {/* Tip Selection */}
            <View style={styles.tipSection}>
              <Text style={styles.tipLabel}>Add Tip?</Text>
              <View style={styles.tipButtons}>
                {[0, 15, 18, 20, 25].map(pct => (
                  <TouchableOpacity
                    key={pct}
                    style={[
                      styles.tipButton,
                      tipAmount === Math.round(subtotal * pct) / 100 && styles.tipButtonActive,
                    ]}
                    onPress={() => handleTipSelection(pct)}
                  >
                    <Text style={[
                      styles.tipButtonText,
                      tipAmount === Math.round(subtotal * pct) / 100 && styles.tipButtonTextActive,
                    ]}>
                      {pct === 0 ? 'No Tip' : `${pct}%`}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              {tipAmount > 0 && (
                <Text style={styles.tipAmount}>Tip: ${tipAmount.toFixed(2)}</Text>
              )}
            </View>
          </View>
        );

      case 'digital':
        return (
          <View style={styles.paymentContent}>
            <View style={styles.digitalSection}>
              <View style={styles.digitalIcons}>
                <View style={styles.digitalIcon}>
                  <Ionicons name="logo-apple" size={32} color="#fff" />
                  <Text style={styles.digitalIconText}>Apple Pay</Text>
                </View>
                <View style={styles.digitalIcon}>
                  <Ionicons name="logo-google" size={32} color="#fff" />
                  <Text style={styles.digitalIconText}>Google Pay</Text>
                </View>
              </View>
              <Text style={styles.digitalInstructions}>
                Hold device near payment terminal
              </Text>
            </View>
          </View>
        );

      case 'gift_card':
        return (
          <View style={styles.paymentContent}>
            <Text style={styles.inputLabel}>Gift Card Number</Text>
            <TextInput
              style={styles.giftCardInput}
              placeholder="Enter gift card code"
              placeholderTextColor="#64748b"
              value={giftCardCode}
              onChangeText={setGiftCardCode}
              autoCapitalize="characters"
            />
            <TouchableOpacity style={styles.scanGiftCardButton}>
              <Ionicons name="scan-outline" size={20} color="#3b82f6" />
              <Text style={styles.scanGiftCardText}>Scan Gift Card</Text>
            </TouchableOpacity>
          </View>
        );

      case 'store_credit':
        return (
          <View style={styles.paymentContent}>
            <View style={styles.storeCreditInfo}>
              <Ionicons name="wallet" size={48} color="#22c55e" />
              <Text style={styles.storeCreditBalance}>Available Credit</Text>
              <Text style={styles.storeCreditAmount}>$150.00</Text>
            </View>
            <Text style={styles.storeCreditNote}>
              ${Math.min(150, totalWithTip).toFixed(2)} will be applied from store credit
            </Text>
          </View>
        );

      case 'split':
        return (
          <View style={styles.paymentContent}>
            <Text style={styles.splitRemaining}>
              Remaining: ${splitRemaining.toFixed(2)}
            </Text>

            {/* Existing splits */}
            {splitPayments.map((payment, index) => (
              <View key={index} style={styles.splitPaymentRow}>
                <View style={styles.splitPaymentInfo}>
                  <Ionicons 
                    name={PAYMENT_METHODS.find(m => m.id === payment.method)?.icon || 'cash-outline'} 
                    size={18} 
                    color="#64748b" 
                  />
                  <Text style={styles.splitPaymentMethod}>
                    {PAYMENT_METHODS.find(m => m.id === payment.method)?.label}
                  </Text>
                </View>
                <Text style={styles.splitPaymentAmount}>${payment.amount.toFixed(2)}</Text>
                <TouchableOpacity onPress={() => handleRemoveSplitPayment(index)}>
                  <Ionicons name="close-circle" size={24} color="#ef4444" />
                </TouchableOpacity>
              </View>
            ))}

            {/* Add split */}
            {splitRemaining > 0.01 && (
              <View style={styles.addSplitSection}>
                <View style={styles.splitMethodRow}>
                  {(['cash', 'card', 'gift_card'] as const).map(method => (
                    <TouchableOpacity
                      key={method}
                      style={[
                        styles.splitMethodButton,
                        splitMethod === method && styles.splitMethodButtonActive,
                      ]}
                      onPress={() => setSplitMethod(method)}
                    >
                      <Ionicons
                        name={PAYMENT_METHODS.find(m => m.id === method)?.icon || 'cash-outline'}
                        size={18}
                        color={splitMethod === method ? '#fff' : '#64748b'}
                      />
                    </TouchableOpacity>
                  ))}
                </View>
                <View style={styles.splitInputRow}>
                  <Text style={styles.currencySymbol}>$</Text>
                  <TextInput
                    style={styles.splitInput}
                    placeholder={splitRemaining.toFixed(2)}
                    placeholderTextColor="#64748b"
                    value={splitAmount}
                    onChangeText={setSplitAmount}
                    keyboardType="decimal-pad"
                  />
                  <TouchableOpacity
                    style={styles.addSplitButton}
                    onPress={handleAddSplitPayment}
                  >
                    <Ionicons name="add" size={24} color="#fff" />
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </View>
        );
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.headerButton}>
            <Ionicons name="close" size={24} color="#f1f5f9" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Payment</Text>
          <View style={styles.headerButton} />
        </View>

        {/* Order Summary */}
        <View style={styles.summarySection}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Subtotal</Text>
            <Text style={styles.summaryValue}>${subtotal.toFixed(2)}</Text>
          </View>
          {discount > 0 && (
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Discount</Text>
              <Text style={styles.discountValue}>-${discount.toFixed(2)}</Text>
            </View>
          )}
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Tax</Text>
            <Text style={styles.summaryValue}>${tax.toFixed(2)}</Text>
          </View>
          {tipAmount > 0 && (
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Tip</Text>
              <Text style={styles.summaryValue}>${tipAmount.toFixed(2)}</Text>
            </View>
          )}
          <View style={[styles.summaryRow, styles.totalRow]}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalValue}>${totalWithTip.toFixed(2)}</Text>
          </View>
        </View>

        <ScrollView style={styles.scrollView}>
          {/* Payment Methods */}
          <View style={styles.methodsSection}>
            <Text style={styles.sectionTitle}>Payment Method</Text>
            <View style={styles.methodsGrid}>
              {PAYMENT_METHODS.map(method => (
                <TouchableOpacity
                  key={method.id}
                  style={[
                    styles.methodButton,
                    selectedMethod === method.id && styles.methodButtonActive,
                  ]}
                  onPress={() => setSelectedMethod(method.id as PaymentMethod)}
                >
                  <Ionicons
                    name={method.icon}
                    size={24}
                    color={selectedMethod === method.id ? '#fff' : '#64748b'}
                  />
                  <Text style={[
                    styles.methodLabel,
                    selectedMethod === method.id && styles.methodLabelActive,
                  ]}>
                    {method.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Payment Content */}
          {renderPaymentContent()}
        </ScrollView>

        {/* Process Button */}
        <View style={styles.footer}>
          <TouchableOpacity
            style={[
              styles.processButton,
              processing && styles.processButtonDisabled,
            ]}
            onPress={handleProcessPayment}
            disabled={processing}
          >
            {processing ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={24} color="#fff" />
                <Text style={styles.processButtonText}>
                  Charge ${totalWithTip.toFixed(2)}
                </Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
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
  headerButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  summarySection: {
    backgroundColor: '#1e293b',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
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
  discountValue: {
    fontSize: 14,
    color: '#22c55e',
  },
  totalRow: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#22c55e',
  },
  scrollView: {
    flex: 1,
  },
  methodsSection: {
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
  methodsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  methodButton: {
    width: '31%',
    aspectRatio: 1.1,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  methodButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  methodLabel: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 6,
    textAlign: 'center',
  },
  methodLabelActive: {
    color: '#fff',
  },
  paymentContent: {
    padding: 16,
  },
  amountDue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
    textAlign: 'center',
    marginBottom: 16,
  },
  quickAmounts: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  quickAmountButton: {
    flex: 1,
    minWidth: '18%',
    paddingVertical: 12,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  quickAmountValid: {
    borderColor: '#22c55e',
  },
  quickAmountExact: {
    backgroundColor: '#1e3a5f',
    borderColor: '#3b82f6',
  },
  quickAmountText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  cashInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  currencySymbol: {
    fontSize: 32,
    color: '#64748b',
  },
  cashInput: {
    flex: 1,
    fontSize: 40,
    fontWeight: '600',
    color: '#f1f5f9',
    paddingVertical: 16,
    textAlign: 'center',
  },
  changeBox: {
    backgroundColor: '#052e16',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginTop: 16,
  },
  changeLabel: {
    fontSize: 14,
    color: '#4ade80',
  },
  changeAmount: {
    fontSize: 36,
    fontWeight: '700',
    color: '#22c55e',
    marginTop: 4,
  },
  cardReaderSection: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  cardReaderText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f1f5f9',
    marginTop: 16,
  },
  cardReaderSubtext: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  tipSection: {
    marginTop: 24,
  },
  tipLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 12,
  },
  tipButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  tipButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  tipButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  tipButtonText: {
    fontSize: 13,
    color: '#94a3b8',
    fontWeight: '500',
  },
  tipButtonTextActive: {
    color: '#fff',
  },
  tipAmount: {
    fontSize: 14,
    color: '#22c55e',
    textAlign: 'center',
    marginTop: 12,
  },
  digitalSection: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  digitalIcons: {
    flexDirection: 'row',
    gap: 32,
    marginBottom: 24,
  },
  digitalIcon: {
    alignItems: 'center',
    backgroundColor: '#1e293b',
    padding: 20,
    borderRadius: 16,
    width: 100,
  },
  digitalIconText: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 8,
  },
  digitalInstructions: {
    fontSize: 16,
    color: '#64748b',
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 8,
  },
  giftCardInput: {
    backgroundColor: '#1e293b',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#f1f5f9',
    fontSize: 18,
    textAlign: 'center',
    letterSpacing: 2,
    borderWidth: 1,
    borderColor: '#334155',
  },
  scanGiftCardButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 16,
    paddingVertical: 12,
  },
  scanGiftCardText: {
    fontSize: 16,
    color: '#3b82f6',
  },
  storeCreditInfo: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  storeCreditBalance: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 12,
  },
  storeCreditAmount: {
    fontSize: 32,
    fontWeight: '700',
    color: '#22c55e',
  },
  storeCreditNote: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
  },
  splitRemaining: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f59e0b',
    textAlign: 'center',
    marginBottom: 16,
  },
  splitPaymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  splitPaymentInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  splitPaymentMethod: {
    fontSize: 14,
    color: '#f1f5f9',
  },
  splitPaymentAmount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#22c55e',
    marginRight: 12,
  },
  addSplitSection: {
    marginTop: 16,
  },
  splitMethodRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  splitMethodButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  splitMethodButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  splitInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  splitInput: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#f1f5f9',
    fontSize: 18,
    borderWidth: 1,
    borderColor: '#334155',
  },
  addSplitButton: {
    backgroundColor: '#3b82f6',
    padding: 14,
    borderRadius: 8,
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
    backgroundColor: '#22c55e',
    paddingVertical: 18,
    borderRadius: 12,
  },
  processButtonDisabled: {
    opacity: 0.7,
  },
  processButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
});

export default PaymentModal;
