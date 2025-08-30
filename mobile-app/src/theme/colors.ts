import { DefaultTheme } from 'react-native-paper';

// On-the-Cheap brand colors (matching web app)
export const colors = {
  primary: '#ea580c',        // Orange-600
  primaryLight: '#fb923c',   // Orange-400  
  primaryDark: '#c2410c',    // Orange-700
  secondary: '#f97316',      // Orange-500
  background: '#fef3c7',     // Amber-100
  backgroundLight: '#fefbf3', // Amber-50
  surface: '#ffffff',
  accent: '#dc2626',         // Red-600 (for favorites)
  text: '#374151',           // Gray-700
  textLight: '#6b7280',      // Gray-500
  textDark: '#111827',       // Gray-900
  border: '#d1d5db',         // Gray-300
  success: '#059669',        // Emerald-600
  warning: '#d97706',        // Amber-600
  error: '#dc2626',          // Red-600
  info: '#2563eb',           // Blue-600
  
  // Food truck colors
  foodTruck: '#f59e0b',      // Amber-500
  restaurant: '#6b7280',     // Gray-500
};

export const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: colors.primary,
    accent: colors.accent,
    background: colors.background,
    surface: colors.surface,
    text: colors.text,
    disabled: colors.textLight,
    placeholder: colors.textLight,
    backdrop: 'rgba(0, 0, 0, 0.5)',
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
};

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};