// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Fix for import.meta in web builds (Zustand devtools issue)
config.transformer = {
  ...config.transformer,
  unstable_allowRequireContext: true,
};

config.resolver = {
  ...config.resolver,
  sourceExts: [...config.resolver.sourceExts, 'mjs'],
};

module.exports = config;
