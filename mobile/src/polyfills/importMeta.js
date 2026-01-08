// Polyfill for import.meta.env (needed for Zustand devtools on web)
if (typeof globalThis !== 'undefined' && typeof globalThis.importMeta === 'undefined') {
  globalThis.importMeta = {
    env: {
      MODE: __DEV__ ? 'development' : 'production',
      DEV: __DEV__,
      PROD: !__DEV__,
    },
  };
}

// Also set on window for web
if (typeof window !== 'undefined' && typeof window.importMeta === 'undefined') {
  window.importMeta = globalThis.importMeta;
}
