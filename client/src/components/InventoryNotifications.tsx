'use client';

import { useEffect } from 'react';
import { useInventorySync } from '@/hooks/useInventorySync';
import { toastManager } from './Toast';

export default function InventoryNotifications() {
  const { isConnected } = useInventorySync({
    endpoint: 'inventory',
    onLowStock: (data) => {
      toastManager.warning(
        `⚠️ Low Stock: ${data.product_name} (${data.new_qty}/${data.min_qty})`,
        5000
      );
    },
    onOutOfStock: (data) => {
      toastManager.error(
        `🔴 Out of Stock: ${data.product_name}`,
        5000
      );
    },
    onInventoryUpdate: (data) => {
      if (data.change > 0) {
        toastManager.success(
          `✓ Restocked: ${data.product_name} (+${data.change} units)`,
          3000
        );
      }
    },
  });

  return null;
}
