/**
 * Shared ListItem Component
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, fontSize, fontWeight } from './theme';
import { Avatar } from './Avatar';
import { Badge } from './Badge';

interface ListItemProps {
  title: string;
  subtitle?: string;
  leftIcon?: keyof typeof Ionicons.glyphMap;
  leftAvatar?: { name?: string; imageUrl?: string };
  rightText?: string;
  rightBadge?: { label: string; variant?: 'success' | 'warning' | 'danger' | 'primary' };
  showChevron?: boolean;
  onPress?: () => void;
  style?: ViewStyle;
}

export const ListItem: React.FC<ListItemProps> = ({
  title,
  subtitle,
  leftIcon,
  leftAvatar,
  rightText,
  rightBadge,
  showChevron = false,
  onPress,
  style,
}) => {
  const Wrapper = onPress ? TouchableOpacity : View;

  return (
    <Wrapper
      style={[styles.container, style]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {leftIcon && (
        <View style={styles.iconContainer}>
          <Ionicons name={leftIcon} size={22} color={colors.primary} />
        </View>
      )}
      {leftAvatar && (
        <Avatar name={leftAvatar.name} imageUrl={leftAvatar.imageUrl} size="md" />
      )}
      <View style={styles.content}>
        <Text style={styles.title}>{title}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
      {rightText && <Text style={styles.rightText}>{rightText}</Text>}
      {rightBadge && <Badge label={rightBadge.label} variant={rightBadge.variant} size="sm" />}
      {showChevron && (
        <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
      )}
    </Wrapper>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    gap: spacing.md,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    backgroundColor: `${colors.primary}20`,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: fontSize.md,
    fontWeight: fontWeight.medium,
    color: colors.text,
  },
  subtitle: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
    marginTop: 2,
  },
  rightText: {
    fontSize: fontSize.md,
    fontWeight: fontWeight.semibold,
    color: colors.text,
  },
});

export default ListItem;
