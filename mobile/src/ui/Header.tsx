/**
 * Shared Header Component
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors, spacing, fontSize, fontWeight } from './theme';
import { IconButton } from './IconButton';
import { Badge } from './Badge';
import { Ionicons } from '@expo/vector-icons';

interface HeaderAction {
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  badge?: number;
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  leftAction?: HeaderAction;
  leftContent?: React.ReactNode;
  rightActions?: HeaderAction[];
  badge?: { label: string; variant?: 'primary' | 'success' | 'warning' | 'danger' };
  style?: ViewStyle;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  leftAction,
  leftContent,
  rightActions = [],
  badge,
  style,
}) => {
  return (
    <View style={[styles.container, style]}>
      <View style={styles.left}>
        {leftAction && (
          <IconButton
            icon={leftAction.icon}
            onPress={leftAction.onPress}
            badge={leftAction.badge}
            variant="ghost"
            style={styles.leftButton}
          />
        )}
        <View>
          <View style={styles.titleRow}>
            <Text style={styles.title}>{title}</Text>
            {leftContent}
            {badge && (
              <Badge label={badge.label} variant={badge.variant} size="sm" style={styles.badge} />
            )}
          </View>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      </View>
      {rightActions.length > 0 && (
        <View style={styles.right}>
          {rightActions.map((action, index) => (
            <IconButton
              key={index}
              icon={action.icon}
              onPress={action.onPress}
              badge={action.badge}
              variant="default"
            />
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  leftButton: {
    marginRight: spacing.md,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  title: {
    fontSize: fontSize.xxl,
    fontWeight: fontWeight.bold,
    color: colors.text,
  },
  subtitle: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
    marginTop: 2,
  },
  badge: {
    marginLeft: spacing.sm,
  },
  right: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
});

export default Header;
