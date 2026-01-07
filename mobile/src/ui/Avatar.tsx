/**
 * Shared Avatar Component
 */

import React from 'react';
import { View, Text, Image, StyleSheet, ViewStyle, ImageStyle } from 'react-native';
import { colors, radius, fontSize, fontWeight } from './theme';

type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  name?: string;
  imageUrl?: string;
  size?: AvatarSize;
  color?: string;
  style?: ViewStyle;
}

export const Avatar: React.FC<AvatarProps> = ({
  name,
  imageUrl,
  size = 'md',
  color = colors.primary,
  style,
}) => {
  const initials = name
    ? name
        .split(' ')
        .map((n) => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : '?';

  if (imageUrl) {
    return (
      <Image
        source={{ uri: imageUrl }}
        style={[imageStyles.base, imageStyles[`size_${size}`], style as ImageStyle]}
      />
    );
  }

  return (
    <View style={[styles.base, styles[`size_${size}`], { backgroundColor: color }, style]}>
      <Text style={[styles.text, styles[`textSize_${size}`]]}>{initials}</Text>
    </View>
  );
};

const sizes = {
  sm: 28,
  md: 36,
  lg: 48,
  xl: 64,
};

const styles = StyleSheet.create({
  base: {
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: radius.full,
  },
  size_sm: { width: sizes.sm, height: sizes.sm },
  size_md: { width: sizes.md, height: sizes.md },
  size_lg: { width: sizes.lg, height: sizes.lg },
  size_xl: { width: sizes.xl, height: sizes.xl },

  text: {
    color: colors.white,
    fontWeight: fontWeight.semibold,
  },
  textSize_sm: { fontSize: fontSize.xs },
  textSize_md: { fontSize: fontSize.md },
  textSize_lg: { fontSize: fontSize.lg },
  textSize_xl: { fontSize: fontSize.xxl },
});

// Separate image styles to avoid TypeScript issues
const imageStyles = StyleSheet.create({
  base: {
    borderRadius: radius.full,
  },
  size_sm: { width: sizes.sm, height: sizes.sm, borderRadius: sizes.sm / 2 },
  size_md: { width: sizes.md, height: sizes.md, borderRadius: sizes.md / 2 },
  size_lg: { width: sizes.lg, height: sizes.lg, borderRadius: sizes.lg / 2 },
  size_xl: { width: sizes.xl, height: sizes.xl, borderRadius: sizes.xl / 2 },
});

export default Avatar;
