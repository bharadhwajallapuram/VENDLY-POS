/**
 * Shared IconButton Component
 */

import React from 'react';
import { TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from './theme';
import { CountBadge } from './Badge';

type IconButtonVariant = 'default' | 'primary' | 'secondary' | 'surface' | 'ghost';
type IconButtonSize = 'sm' | 'md' | 'lg';

interface IconButtonProps {
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  variant?: IconButtonVariant;
  size?: IconButtonSize;
  color?: string;
  badge?: number;
  disabled?: boolean;
  style?: ViewStyle;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  onPress,
  variant = 'default',
  size = 'md',
  color,
  badge,
  disabled = false,
  style,
}) => {
  const iconSizes = { sm: 18, md: 22, lg: 26 };
  const iconColor = color || (variant === 'ghost' ? colors.text : colors.text);

  return (
    <TouchableOpacity
      style={[
        styles.base,
        styles[variant],
        styles[`size_${size}`],
        disabled && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.7}
    >
      <Ionicons name={icon} size={iconSizes[size]} color={iconColor} />
      {badge !== undefined && badge > 0 && <CountBadge count={badge} />}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  base: {
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: radius.full,
  },
  disabled: {
    opacity: 0.5,
  },

  // Variants
  default: {
    backgroundColor: colors.background,
  },
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: colors.surface,
  },
  surface: {
    backgroundColor: colors.surface,
  },
  ghost: {
    backgroundColor: colors.transparent,
  },

  // Sizes
  size_sm: {
    width: 32,
    height: 32,
  },
  size_md: {
    width: 40,
    height: 40,
  },
  size_lg: {
    width: 48,
    height: 48,
  },
});

export default IconButton;
