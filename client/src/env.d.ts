interface ImportMetaEnv {
  VITE_API_URL?: string;
  // add other VITE_ variables here if needed
}

interface ImportMeta {
  env: ImportMetaEnv;
}
