/**
 * Shared Divider Component
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors, spacing, fontSize } from './theme';

interface DividerProps {
  label?: string;
  style?: ViewStyle;
}

export const Divider: React.FC<DividerProps> = ({ label, style }) => {
  if (!label) {
    return <View style={[styles.line, style]} />;
  }

  return (
    <View style={[styles.container, style]}>
      <View style={styles.line} />
      <Text style={styles.label}>{label}</Text>
      <View style={styles.line} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.md,
  },
  line: {
    flex: 1,
    height: 1,
    backgroundColor: colors.border,
  },
  label: {
    marginHorizontal: spacing.md,
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
});

export default Divider;
