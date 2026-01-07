/**
 * Shared Theme - Design tokens for consistent styling
 */

export const colors = {
  // Primary
  primary: '#3b82f6',
  primaryDark: '#2563eb',
  primaryLight: '#60a5fa',

  // Success
  success: '#22c55e',
  successDark: '#16a34a',
  successLight: '#4ade80',

  // Warning
  warning: '#f59e0b',
  warningDark: '#d97706',
  warningLight: '#fbbf24',

  // Danger
  danger: '#ef4444',
  dangerDark: '#dc2626',
  dangerLight: '#f87171',

  // Info
  info: '#06b6d4',
  infoDark: '#0891b2',
  infoLight: '#22d3ee',

  // Neutrals (Slate)
  background: '#0f172a',
  surface: '#1e293b',
  surfaceHover: '#334155',
  surfaceLight: '#334155',
  border: '#334155',
  borderLight: '#475569',

  // Text
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
  textInverse: '#0f172a',

  // Misc
  white: '#ffffff',
  black: '#000000',
  transparent: 'transparent',
  overlay: 'rgba(0, 0, 0, 0.7)',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const radius = {
  xs: 4,
  sm: 6,
  md: 8,
  lg: 10,
  xl: 12,
  xxl: 16,
  full: 9999,
};

export const fontSize = {
  xs: 10,
  sm: 12,
  md: 14,
  lg: 16,
  xl: 18,
  xxl: 22,
  xxxl: 28,
};

export const fontWeight = {
  normal: '400' as const,
  medium: '500' as const,
  semibold: '600' as const,
  bold: '700' as const,
};

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
};

export default { colors, spacing, radius, fontSize, fontWeight, shadows };
