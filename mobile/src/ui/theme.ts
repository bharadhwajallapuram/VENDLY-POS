/**
 * Shared Theme - Design tokens for consistent styling
 * Matches the web client's modern design with sky-blue primary
 */

export const colors = {
  // Primary - Modern Sky Blue (matches client tailwind primary-500)
  primary: '#0ea5e9',
  primaryDark: '#0284c7',
  primaryLight: '#38bdf8',
  primary50: '#f0f9ff',
  primary100: '#e0f2fe',
  primary200: '#bae6fd',
  primary300: '#7dd3fc',
  primary400: '#38bdf8',
  primary500: '#0ea5e9',
  primary600: '#0284c7',
  primary700: '#0369a1',
  primary800: '#075985',
  primary900: '#0c4a6e',

  // Accent - Purple gradient
  accent: '#8b5cf6',
  accentDark: '#7c3aed',
  accentLight: '#a78bfa',

  // Success - Modern Green
  success: '#10b981',
  successDark: '#059669',
  successLight: '#34d399',
  successBg: '#d1fae5',

  // Warning - Modern Amber
  warning: '#f59e0b',
  warningDark: '#d97706',
  warningLight: '#fbbf24',
  warningBg: '#fef3c7',

  // Danger - Modern Red
  danger: '#ef4444',
  dangerDark: '#dc2626',
  dangerLight: '#f87171',
  dangerBg: '#fee2e2',

  // Info - Cyan
  info: '#06b6d4',
  infoDark: '#0891b2',
  infoLight: '#22d3ee',
  infoBg: '#cffafe',

  // Neutrals - Modern Light theme
  background: '#f1f5f9',     // slate-100
  surface: '#ffffff',        // white
  surfaceHover: '#f8fafc',   // slate-50
  surfaceLight: '#e2e8f0',   // slate-200
  border: '#e2e8f0',         // slate-200
  borderLight: '#f1f5f9',    // slate-100

  // Text - Dark text on light background
  text: '#0f172a',           // slate-900
  textSecondary: '#475569',  // slate-600
  textMuted: '#94a3b8',      // slate-400
  textInverse: '#f8fafc',    // slate-50

  // Cards & Elevated surfaces
  card: '#ffffff',
  cardBorder: '#e2e8f0',
  cardShadow: 'rgba(0, 0, 0, 0.04)',

  // Gradient colors
  gradientStart: '#0ea5e9',
  gradientEnd: '#8b5cf6',

  // Misc
  white: '#ffffff',
  black: '#000000',
  transparent: 'transparent',
  overlay: 'rgba(15, 23, 42, 0.5)',
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
