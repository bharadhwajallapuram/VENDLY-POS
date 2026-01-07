/**
 * Shared Badge Component
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors, spacing, radius, fontSize, fontWeight } from './theme';

type BadgeVariant = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  label?: string;
  children?: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  style?: ViewStyle;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  children,
  variant = 'primary',
  size = 'md',
  style,
}) => {
  const displayText = label || (typeof children === 'string' ? children : '');
  
  return (
    <View style={[styles.base, styles[variant], styles[`size_${size}`], style]}>
      <Text style={[styles.text, styles[`text_${variant}`], styles[`textSize_${size}`]]}>
        {displayText}
      </Text>
    </View>
  );
};

// Numeric badge for notifications
interface CountBadgeProps {
  count: number;
  max?: number;
  style?: ViewStyle;
}

export const CountBadge: React.FC<CountBadgeProps> = ({ count, max = 99, style }) => {
  if (count <= 0) return null;
  const displayCount = count > max ? `${max}+` : count.toString();

  return (
    <View style={[styles.countBadge, style]}>
      <Text style={styles.countText}>{displayCount}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  base: {
    alignSelf: 'flex-start',
    borderRadius: radius.full,
  },
  
  // Variants - background
  primary: { backgroundColor: `${colors.primary}20` },
  success: { backgroundColor: `${colors.success}20` },
  warning: { backgroundColor: `${colors.warning}20` },
  danger: { backgroundColor: `${colors.danger}20` },
  info: { backgroundColor: `${colors.info}20` },
  neutral: { backgroundColor: colors.surfaceLight },

  // Sizes
  size_sm: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs - 2,
  },
  size_md: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },

  // Text
  text: {
    fontWeight: fontWeight.medium,
  },
  text_primary: { color: colors.primary },
  text_success: { color: colors.success },
  text_warning: { color: colors.warning },
  text_danger: { color: colors.danger },
  text_info: { color: colors.info },
  text_neutral: { color: colors.textSecondary },

  textSize_sm: { fontSize: fontSize.xs },
  textSize_md: { fontSize: fontSize.sm },

  // Count badge
  countBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: colors.danger,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  countText: {
    color: colors.white,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.bold,
  },
});

export default Badge;
