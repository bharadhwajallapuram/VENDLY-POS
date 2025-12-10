// ===========================================
// Offline Mode Configuration
// ===========================================
// All offline mode settings in one place
// Can be overridden via environment variables

export const OFFLINE_CONFIG = {
  // Storage
  QUEUE_STORAGE_KEY: process.env.NEXT_PUBLIC_OFFLINE_QUEUE_KEY || 'vendly_offline_queue',
  
  // Retry logic
  MAX_RETRIES: parseInt(process.env.NEXT_PUBLIC_OFFLINE_MAX_RETRIES || '3', 10),
  
  // Timing (in milliseconds)
  RECONNECTION_DELAY: parseInt(process.env.NEXT_PUBLIC_OFFLINE_RECONNECTION_DELAY || '2000', 10),
  PERIODIC_SYNC_INTERVAL: parseInt(process.env.NEXT_PUBLIC_OFFLINE_PERIODIC_SYNC || '30000', 10),
  SYNC_TIMEOUT: parseInt(process.env.NEXT_PUBLIC_OFFLINE_SYNC_TIMEOUT || '30000', 10),
  
  // API Endpoints
  BATCH_SYNC_ENDPOINT: process.env.NEXT_PUBLIC_OFFLINE_BATCH_SYNC_ENDPOINT || '/api/v1/sales/batch-sync',
  SINGLE_SYNC_ENDPOINT: process.env.NEXT_PUBLIC_OFFLINE_SINGLE_SYNC_ENDPOINT || '/api/v1/sales',
  
  // Features
  ENABLE_OFFLINE_MODE: process.env.NEXT_PUBLIC_ENABLE_OFFLINE_MODE !== 'false',
  ENABLE_AUTO_SYNC: process.env.NEXT_PUBLIC_ENABLE_AUTO_SYNC !== 'false',
  ENABLE_PERIODIC_SYNC: process.env.NEXT_PUBLIC_ENABLE_PERIODIC_SYNC !== 'false',
  
  // Storage limits
  MAX_QUEUED_SALES: parseInt(process.env.NEXT_PUBLIC_OFFLINE_MAX_QUEUE_SIZE || '5000', 10),
};

// Validation
if (OFFLINE_CONFIG.MAX_RETRIES < 1) {
  console.warn('MAX_RETRIES must be at least 1, setting to 1');
  OFFLINE_CONFIG.MAX_RETRIES = 1;
}

if (OFFLINE_CONFIG.RECONNECTION_DELAY < 500) {
  console.warn('RECONNECTION_DELAY too low (< 500ms), setting to 500ms');
  OFFLINE_CONFIG.RECONNECTION_DELAY = 500;
}

if (OFFLINE_CONFIG.PERIODIC_SYNC_INTERVAL < 5000) {
  console.warn('PERIODIC_SYNC_INTERVAL too low (< 5s), setting to 5s');
  OFFLINE_CONFIG.PERIODIC_SYNC_INTERVAL = 5000;
}

export default OFFLINE_CONFIG;
