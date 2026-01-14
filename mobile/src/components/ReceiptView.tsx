/**
 * Receipt View Component
 * Digital receipt display with email/SMS options and print support
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  Share,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';

interface ReceiptItem {
  name: string;
  quantity: number;
  price: number;
  discount?: number;
}

interface ReceiptData {
  saleId?: number;
  receiptNumber: string;
  date: Date;
  items: ReceiptItem[];
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  paymentMethod: string;
  cashier: string;
  customerId?: number;
  customerName?: string;
  storeInfo: {
    name: string;
    address: string;
    phone: string;
    website?: string;
  };
}

interface ReceiptViewProps {
  visible: boolean;
  onClose: () => void;
  receipt: ReceiptData;
}

export const ReceiptView: React.FC<ReceiptViewProps> = ({
  visible,
  onClose,
  receipt,
}) => {
  const [showSendModal, setShowSendModal] = useState(false);
  const [sendType, setSendType] = useState<'email' | 'sms'>('email');
  const [sendTo, setSendTo] = useState('');
  const [sending, setSending] = useState(false);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const generateReceiptText = () => {
    let text = `
${receipt.storeInfo.name}
${receipt.storeInfo.address}
${receipt.storeInfo.phone}
${receipt.storeInfo.website || ''}

Receipt #${receipt.receiptNumber}
Date: ${formatDate(receipt.date)}
Cashier: ${receipt.cashier}
${receipt.customerName ? `Customer: ${receipt.customerName}` : ''}

--------------------------------
`;

    receipt.items.forEach(item => {
      const itemTotal = (item.price * item.quantity).toFixed(2);
      text += `${item.name}
  ${item.quantity} x $${item.price.toFixed(2)} = $${itemTotal}
`;
      if (item.discount && item.discount > 0) {
        text += `  Discount: -${item.discount}%\n`;
      }
    });

    text += `--------------------------------
Subtotal: $${receipt.subtotal.toFixed(2)}
`;

    if (receipt.discount > 0) {
      text += `Discount: -$${receipt.discount.toFixed(2)}\n`;
    }

    text += `Tax: $${receipt.tax.toFixed(2)}
TOTAL: $${receipt.total.toFixed(2)}

Payment: ${receipt.paymentMethod}

Thank you for your purchase!
    `;

    return text;
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: generateReceiptText(),
        title: `Receipt #${receipt.receiptNumber}`,
      });
    } catch (error) {
      console.error('Share error:', error);
    }
  };

  const handleSend = async () => {
    if (!sendTo.trim()) {
      Alert.alert('Error', `Please enter ${sendType === 'email' ? 'an email address' : 'a phone number'}`);
      return;
    }

    setSending(true);
    
    try {
      // If we have a sale ID, use the backend API for sending
      if (receipt.saleId) {
        const options = sendType === 'email' 
          ? { email: sendTo.trim() }
          : { phone: sendTo.trim() };
        
        const result = await apiService.sendReceipt(receipt.saleId, options);
        
        setShowSendModal(false);
        setSendTo('');
        
        if (result && (result as { success?: boolean }).success) {
          Alert.alert(
            'Receipt Sent!',
            `Receipt has been sent to ${sendTo}`,
            [{ text: 'OK' }]
          );
        } else {
          const errors = (result as { errors?: string[] })?.errors;
          Alert.alert(
            'Sending Issue',
            errors ? errors.join(', ') : 'Receipt may have been sent. Check your inbox.',
            [{ text: 'OK' }]
          );
        }
      } else {
        // Fallback to device native apps if no saleId (offline mode)
        const receiptText = generateReceiptText();
        
        if (sendType === 'sms') {
          const cleanedPhone = sendTo.replace(/\D/g, '');
          const smsUrl = `sms:${cleanedPhone}?body=${encodeURIComponent(receiptText)}`;
          
          const canOpen = await Linking.canOpenURL(smsUrl);
          if (canOpen) {
            await Linking.openURL(smsUrl);
            setShowSendModal(false);
            setSendTo('');
            Alert.alert('SMS Ready', `SMS app opened with receipt for ${sendTo}. Press send to complete.`);
          } else {
            Alert.alert('Error', 'Unable to open SMS app. Please make sure your device supports SMS.');
          }
        } else {
          const subject = `Receipt #${receipt.receiptNumber} - ${receipt.storeInfo.name}`;
          const mailUrl = `mailto:${encodeURIComponent(sendTo)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(receiptText)}`;
          
          const canOpen = await Linking.canOpenURL(mailUrl);
          if (canOpen) {
            await Linking.openURL(mailUrl);
            setShowSendModal(false);
            setSendTo('');
            Alert.alert('Email Ready', `Email app opened with receipt for ${sendTo}. Press send to complete.`);
          } else {
            Alert.alert('Error', 'Unable to open email app. Please make sure you have an email app configured.');
          }
        }
      }
    } catch (error) {
      console.error('Send error:', error);
      Alert.alert('Error', `Failed to send receipt via ${sendType === 'email' ? 'email' : 'SMS'}. Please try again.`);
    } finally {
      setSending(false);
    }
  };

  const handlePrint = () => {
    Alert.alert(
      'Print Receipt',
      'Connect to a thermal printer to print receipts. This feature requires Bluetooth printer setup.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Setup Printer', onPress: () => console.log('Setup printer') },
      ]
    );
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.headerButton}>
            <Ionicons name="close" size={24} color="#f1f5f9" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Receipt</Text>
          <TouchableOpacity onPress={handleShare} style={styles.headerButton}>
            <Ionicons name="share-outline" size={24} color="#f1f5f9" />
          </TouchableOpacity>
        </View>

        {/* Receipt Content */}
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.receiptContent}>
          <View style={styles.receiptPaper}>
            {/* Store Header */}
            <View style={styles.storeHeader}>
              <Text style={styles.storeName}>{receipt.storeInfo.name}</Text>
              <Text style={styles.storeAddress}>{receipt.storeInfo.address}</Text>
              <Text style={styles.storePhone}>{receipt.storeInfo.phone}</Text>
            </View>

            {/* Receipt Meta */}
            <View style={styles.receiptMeta}>
              <View style={styles.metaRow}>
                <Text style={styles.metaLabel}>Receipt #:</Text>
                <Text style={styles.metaValue}>{receipt.receiptNumber}</Text>
              </View>
              <View style={styles.metaRow}>
                <Text style={styles.metaLabel}>Date:</Text>
                <Text style={styles.metaValue}>{formatDate(receipt.date)}</Text>
              </View>
              <View style={styles.metaRow}>
                <Text style={styles.metaLabel}>Cashier:</Text>
                <Text style={styles.metaValue}>{receipt.cashier}</Text>
              </View>
              {receipt.customerName && (
                <View style={styles.metaRow}>
                  <Text style={styles.metaLabel}>Customer:</Text>
                  <Text style={styles.metaValue}>{receipt.customerName}</Text>
                </View>
              )}
            </View>

            {/* Divider */}
            <View style={styles.divider} />

            {/* Items */}
            {receipt.items.map((item, index) => (
              <View key={index} style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemQty}>
                    {item.quantity} × ${item.price.toFixed(2)}
                  </Text>
                </View>
                <Text style={styles.itemTotal}>
                  ${(item.price * item.quantity).toFixed(2)}
                </Text>
              </View>
            ))}

            {/* Divider */}
            <View style={styles.divider} />

            {/* Totals */}
            <View style={styles.totalsSection}>
              <View style={styles.totalRow}>
                <Text style={styles.totalLabel}>Subtotal</Text>
                <Text style={styles.totalValue}>${receipt.subtotal.toFixed(2)}</Text>
              </View>
              {receipt.discount > 0 && (
                <View style={styles.totalRow}>
                  <Text style={styles.totalLabel}>Discount</Text>
                  <Text style={[styles.totalValue, styles.discountValue]}>
                    -${receipt.discount.toFixed(2)}
                  </Text>
                </View>
              )}
              <View style={styles.totalRow}>
                <Text style={styles.totalLabel}>Tax</Text>
                <Text style={styles.totalValue}>${receipt.tax.toFixed(2)}</Text>
              </View>
              <View style={[styles.totalRow, styles.grandTotalRow]}>
                <Text style={styles.grandTotalLabel}>TOTAL</Text>
                <Text style={styles.grandTotalValue}>${receipt.total.toFixed(2)}</Text>
              </View>
            </View>

            {/* Payment Method */}
            <View style={styles.paymentSection}>
              <View style={styles.paymentRow}>
                <Ionicons 
                  name={receipt.paymentMethod === 'Cash' ? 'cash-outline' : 'card-outline'} 
                  size={18} 
                  color="#64748b" 
                />
                <Text style={styles.paymentText}>
                  Paid with {receipt.paymentMethod}
                </Text>
              </View>
            </View>

            {/* Footer */}
            <View style={styles.receiptFooter}>
              <Text style={styles.thankYou}>Thank you for your purchase!</Text>
              <View style={styles.barcodeArea}>
                <Ionicons name="barcode-outline" size={48} color="#94a3b8" />
                <Text style={styles.barcodeText}>{receipt.receiptNumber}</Text>
              </View>
            </View>
          </View>
        </ScrollView>

        {/* Action Buttons */}
        <View style={styles.actionBar}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => {
              setSendType('email');
              setShowSendModal(true);
            }}
          >
            <Ionicons name="mail-outline" size={22} color="#3b82f6" />
            <Text style={styles.actionButtonText}>Email</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => {
              setSendType('sms');
              setShowSendModal(true);
            }}
          >
            <Ionicons name="chatbubble-outline" size={22} color="#3b82f6" />
            <Text style={styles.actionButtonText}>SMS</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={handlePrint}>
            <Ionicons name="print-outline" size={22} color="#3b82f6" />
            <Text style={styles.actionButtonText}>Print</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButtonPrimary} onPress={onClose}>
            <Text style={styles.actionButtonPrimaryText}>Done</Text>
          </TouchableOpacity>
        </View>

        {/* Send Modal */}
        <Modal
          visible={showSendModal}
          animationType="fade"
          transparent
          onRequestClose={() => setShowSendModal(false)}
        >
          <View style={styles.sendModalOverlay}>
            <View style={styles.sendModalContainer}>
              <View style={styles.sendModalHeader}>
                <Ionicons 
                  name={sendType === 'email' ? 'mail-outline' : 'chatbubble-outline'} 
                  size={28} 
                  color="#3b82f6" 
                />
                <Text style={styles.sendModalTitle}>
                  Send via {sendType === 'email' ? 'Email' : 'SMS'}
                </Text>
              </View>
              <Text style={styles.sendModalHint}>
                {sendType === 'email' 
                  ? 'Enter customer email address' 
                  : 'Enter mobile number with country code'}
              </Text>
              <TextInput
                style={styles.sendInput}
                placeholder={sendType === 'email' ? 'customer@email.com' : '+1 555-123-4567'}
                placeholderTextColor="#64748b"
                value={sendTo}
                onChangeText={setSendTo}
                keyboardType={sendType === 'email' ? 'email-address' : 'phone-pad'}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <View style={styles.sendModalButtons}>
                <TouchableOpacity
                  style={styles.sendModalCancel}
                  onPress={() => {
                    setShowSendModal(false);
                    setSendTo('');
                  }}
                >
                  <Text style={styles.sendModalCancelText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.sendModalSubmit, !sendTo.trim() && styles.sendModalSubmitDisabled]}
                  onPress={handleSend}
                  disabled={sending || !sendTo.trim()}
                >
                  {sending ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <Text style={styles.sendModalSubmitText}>Send</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
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
  scrollView: {
    flex: 1,
  },
  receiptContent: {
    padding: 16,
  },
  receiptPaper: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  storeHeader: {
    alignItems: 'center',
    marginBottom: 16,
  },
  storeName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0f172a',
  },
  storeAddress: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
    textAlign: 'center',
  },
  storePhone: {
    fontSize: 12,
    color: '#64748b',
  },
  receiptMeta: {
    marginBottom: 16,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  metaLabel: {
    fontSize: 12,
    color: '#64748b',
  },
  metaValue: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '500',
  },
  divider: {
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    borderStyle: 'dashed',
    marginVertical: 12,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 14,
    color: '#0f172a',
    fontWeight: '500',
  },
  itemQty: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  itemTotal: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0f172a',
  },
  totalsSection: {
    marginTop: 8,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  totalLabel: {
    fontSize: 14,
    color: '#64748b',
  },
  totalValue: {
    fontSize: 14,
    color: '#334155',
    fontWeight: '500',
  },
  discountValue: {
    color: '#22c55e',
  },
  grandTotalRow: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  grandTotalLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
  },
  grandTotalValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
  },
  paymentSection: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  paymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  paymentText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#64748b',
  },
  receiptFooter: {
    alignItems: 'center',
    marginTop: 24,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  thankYou: {
    fontSize: 14,
    color: '#64748b',
    fontStyle: 'italic',
  },
  barcodeArea: {
    marginTop: 16,
    alignItems: 'center',
  },
  barcodeText: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 4,
    fontFamily: 'monospace',
  },
  actionBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    paddingBottom: 32,
    backgroundColor: '#1e293b',
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  actionButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    backgroundColor: '#0f172a',
    borderRadius: 8,
    marginHorizontal: 4,
  },
  actionButtonText: {
    fontSize: 12,
    color: '#3b82f6',
    fontWeight: '500',
  },
  actionButtonPrimary: {
    flex: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    backgroundColor: '#22c55e',
    borderRadius: 8,
  },
  actionButtonPrimaryText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
  sendModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  sendModalContainer: {
    width: '100%',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 20,
  },
  sendModalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  sendModalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f1f5f9',
    marginLeft: 8,
  },
  sendModalHint: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 16,
  },
  sendInput: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: '#f1f5f9',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: 16,
  },
  sendModalButtons: {
    flexDirection: 'row',
  },
  sendModalCancel: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderRadius: 8,
    marginRight: 12,
  },
  sendModalCancelText: {
    color: '#94a3b8',
    fontSize: 16,
    fontWeight: '600',
  },
  sendModalSubmit: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: '#3b82f6',
    borderRadius: 8,
  },
  sendModalSubmitDisabled: {
    backgroundColor: '#475569',
  },
  sendModalSubmitText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ReceiptView;
