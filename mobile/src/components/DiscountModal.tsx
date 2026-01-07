/**
 * Discount Modal Component
 * Apply discounts, coupon codes, and promotions
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import {
  Modal,
  Button,
  Input,
  Card,
  colors,
  spacing,
  radius,
  fontSize,
  fontWeight,
} from '../ui';

interface DiscountModalProps {
  visible: boolean;
  onClose: () => void;
  onApplyDiscount: (discount: DiscountData) => void;
  currentSubtotal: number;
}

export interface DiscountData {
  type: 'percentage' | 'fixed' | 'coupon';
  value: number;
  code?: string;
  description?: string;
}

interface Coupon {
  code: string;
  type: 'percentage' | 'fixed';
  value: number;
  description: string;
  minPurchase?: number;
  expiresAt?: string;
}

// Mock coupons - would come from API
const MOCK_COUPONS: Coupon[] = [
  { code: 'SAVE10', type: 'percentage', value: 10, description: '10% off entire order' },
  { code: 'FLAT5', type: 'fixed', value: 5, description: '$5 off your purchase', minPurchase: 25 },
  { code: 'VIP20', type: 'percentage', value: 20, description: '20% VIP discount' },
];

export const DiscountModal: React.FC<DiscountModalProps> = ({
  visible,
  onClose,
  onApplyDiscount,
  currentSubtotal,
}) => {
  const [activeTab, setActiveTab] = useState<'quick' | 'coupon' | 'custom'>('quick');
  const [couponCode, setCouponCode] = useState('');
  const [customType, setCustomType] = useState<'percentage' | 'fixed'>('percentage');
  const [customValue, setCustomValue] = useState('');
  const [validating, setValidating] = useState(false);

  const quickDiscounts = [5, 10, 15, 20, 25, 50];

  const handleQuickDiscount = (percentage: number) => {
    onApplyDiscount({
      type: 'percentage',
      value: percentage,
      description: `${percentage}% discount`,
    });
    onClose();
  };

  const validateCoupon = async () => {
    if (!couponCode.trim()) {
      Alert.alert('Error', 'Please enter a coupon code');
      return;
    }

    setValidating(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const coupon = MOCK_COUPONS.find(
      c => c.code.toLowerCase() === couponCode.trim().toLowerCase()
    );

    setValidating(false);

    if (!coupon) {
      Alert.alert('Invalid Coupon', 'This coupon code is not valid or has expired.');
      return;
    }

    if (coupon.minPurchase && currentSubtotal < coupon.minPurchase) {
      Alert.alert(
        'Minimum Not Met',
        `This coupon requires a minimum purchase of $${coupon.minPurchase.toFixed(2)}`
      );
      return;
    }

    onApplyDiscount({
      type: coupon.type,
      value: coupon.value,
      code: coupon.code,
      description: coupon.description,
    });
    setCouponCode('');
    onClose();
  };

  const handleCustomDiscount = () => {
    const value = parseFloat(customValue);
    
    if (isNaN(value) || value <= 0) {
      Alert.alert('Error', 'Please enter a valid discount value');
      return;
    }

    if (customType === 'percentage' && value > 100) {
      Alert.alert('Error', 'Percentage cannot exceed 100%');
      return;
    }

    if (customType === 'fixed' && value > currentSubtotal) {
      Alert.alert('Error', 'Discount cannot exceed order subtotal');
      return;
    }

    onApplyDiscount({
      type: customType,
      value,
      description: customType === 'percentage' 
        ? `${value}% custom discount` 
        : `$${value.toFixed(2)} off`,
    });
    setCustomValue('');
    onClose();
  };

  return (
    <Modal
      visible={visible}
      onClose={onClose}
      title="Apply Discount"
      size="lg"
    >
      {/* Tabs */}
      <View style={styles.tabs}>
        {(['quick', 'coupon', 'custom'] as const).map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {/* Quick Discounts */}
        {activeTab === 'quick' && (
          <View style={styles.quickGrid}>
            {quickDiscounts.map(percent => (
              <TouchableOpacity
                key={percent}
                style={styles.quickButton}
                onPress={() => handleQuickDiscount(percent)}
              >
                <Text style={styles.quickButtonText}>{percent}%</Text>
                <Text style={styles.quickButtonSubtext}>
                  -${((currentSubtotal * percent) / 100).toFixed(2)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Coupon Code */}
        {activeTab === 'coupon' && (
          <View style={styles.couponSection}>
            <View style={styles.inputRow}>
              <View style={styles.couponInputWrapper}>
                <Input
                  placeholder="Enter coupon code"
                  value={couponCode}
                  onChangeText={setCouponCode}
                  autoCapitalize="characters"
                  autoCorrect={false}
                />
              </View>
              <Button
                title="Apply"
                onPress={validateCoupon}
                loading={validating}
                size="md"
              />
            </View>

            <Text style={styles.sectionTitle}>Available Coupons</Text>
            {MOCK_COUPONS.map(coupon => (
              <TouchableOpacity
                key={coupon.code}
                style={styles.couponCard}
                onPress={() => setCouponCode(coupon.code)}
              >
                <View style={styles.couponBadge}>
                  <Text style={styles.couponBadgeText}>{coupon.code}</Text>
                </View>
                <View style={styles.couponInfo}>
                  <Text style={styles.couponDescription}>{coupon.description}</Text>
                  {coupon.minPurchase && (
                    <Text style={styles.couponMin}>
                      Min. purchase: ${coupon.minPurchase.toFixed(2)}
                    </Text>
                  )}
                </View>
                <Text style={styles.couponValue}>
                  {coupon.type === 'percentage' ? `${coupon.value}%` : `$${coupon.value}`}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Custom Discount */}
        {activeTab === 'custom' && (
          <View style={styles.customSection}>
            <Text style={styles.sectionTitle}>Discount Type</Text>
            <View style={styles.typeRow}>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  customType === 'percentage' && styles.typeButtonActive,
                ]}
                onPress={() => setCustomType('percentage')}
              >
                <Ionicons 
                  name="pricetag-outline" 
                  size={20} 
                  color={customType === 'percentage' ? colors.primary : colors.textMuted} 
                />
                <Text style={[
                  styles.typeButtonText,
                  customType === 'percentage' && styles.typeButtonTextActive,
                ]}>
                  Percentage
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  customType === 'fixed' && styles.typeButtonActive,
                ]}
                onPress={() => setCustomType('fixed')}
              >
                <Ionicons 
                  name="cash-outline" 
                  size={20} 
                  color={customType === 'fixed' ? colors.primary : colors.textMuted} 
                />
                <Text style={[
                  styles.typeButtonText,
                  customType === 'fixed' && styles.typeButtonTextActive,
                ]}>
                  Fixed Amount
                </Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.sectionTitle}>
              {customType === 'percentage' ? 'Discount Percentage' : 'Discount Amount'}
            </Text>
            <View style={styles.customInputRow}>
              {customType === 'fixed' && (
                <Text style={styles.currencySymbol}>$</Text>
              )}
              <Input
                placeholder={customType === 'percentage' ? '0' : '0.00'}
                value={customValue}
                onChangeText={setCustomValue}
                keyboardType="decimal-pad"
                containerStyle={styles.customInputContainer}
              />
              {customType === 'percentage' && (
                <Text style={styles.percentSymbol}>%</Text>
              )}
            </View>

            {customValue && !isNaN(parseFloat(customValue)) && (
              <Card variant="elevated" style={styles.previewCard}>
                <Text style={styles.previewLabel}>Discount Preview</Text>
                <Text style={styles.previewValue}>
                  -${customType === 'percentage'
                    ? ((currentSubtotal * parseFloat(customValue)) / 100).toFixed(2)
                    : parseFloat(customValue).toFixed(2)
                  }
                </Text>
              </Card>
            )}

            <Button
              title="Apply Discount"
              onPress={handleCustomDiscount}
              fullWidth
              size="lg"
              style={styles.customApplyButton}
            />
          </View>
        )}
      </ScrollView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: radius.sm,
  },
  tabActive: {
    backgroundColor: colors.primary,
  },
  tabText: {
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
    color: colors.textSecondary,
  },
  tabTextActive: {
    color: colors.white,
  },
  content: {
    padding: spacing.lg,
  },
  quickGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  quickButton: {
    width: '30%',
    aspectRatio: 1.2,
    backgroundColor: colors.background,
    borderRadius: radius.md,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  quickButtonText: {
    fontSize: fontSize.xxl,
    fontWeight: fontWeight.bold,
    color: colors.primary,
  },
  quickButtonSubtext: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: spacing.xs,
  },
  couponSection: {},
  inputRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.xxl,
    alignItems: 'flex-start',
  },
  couponInputWrapper: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  couponCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  couponBadge: {
    backgroundColor: colors.primaryLight + '30',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.sm,
  },
  couponBadgeText: {
    fontSize: fontSize.xs,
    fontWeight: fontWeight.bold,
    color: colors.primary,
  },
  couponInfo: {
    flex: 1,
    marginLeft: spacing.md,
  },
  couponDescription: {
    fontSize: fontSize.sm,
    color: colors.text,
  },
  couponMin: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: 2,
  },
  couponValue: {
    fontSize: fontSize.lg,
    fontWeight: fontWeight.bold,
    color: colors.success,
  },
  customSection: {},
  typeRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.xxl,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.background,
    paddingVertical: spacing.md,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  typeButtonActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight + '20',
  },
  typeButtonText: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
  typeButtonTextActive: {
    color: colors.primary,
  },
  customInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  customInputContainer: {
    flex: 1,
    marginBottom: 0,
  },
  currencySymbol: {
    fontSize: fontSize.xxl,
    color: colors.textMuted,
    marginRight: spacing.xs,
  },
  percentSymbol: {
    fontSize: fontSize.xxl,
    color: colors.textMuted,
    marginLeft: spacing.sm,
  },
  previewCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
    backgroundColor: colors.successLight + '15',
  },
  previewLabel: {
    fontSize: fontSize.sm,
    color: colors.successLight,
  },
  previewValue: {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.bold,
    color: colors.success,
  },
  customApplyButton: {
    marginTop: spacing.md,
  },
});

export default DiscountModal;
