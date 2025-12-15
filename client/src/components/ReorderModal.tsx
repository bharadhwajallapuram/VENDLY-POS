'use client';

import { useState } from 'react';
import ResponsiveModal from './ResponsiveModal';

interface ReorderModalProps {
  isOpen: boolean;
  productId: number;
  productName: string;
  currentStock: number;
  minStock: number;
  onClose: () => void;
  onSubmit: (quantity: number, supplierNote: string) => Promise<void>;
  isLoading?: boolean;
}

export default function ReorderModal({
  isOpen,
  productId,
  productName,
  currentStock,
  minStock,
  onClose,
  onSubmit,
  isLoading = false,
}: ReorderModalProps) {
  const [quantity, setQuantity] = useState<string>('');
  const [supplierNote, setSupplierNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      alert('Please enter a valid quantity');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(qty, supplierNote);
      setQuantity('');
      setSupplierNote('');
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ResponsiveModal isOpen={isOpen} onClose={onClose} title="Create Purchase Order">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Product Info */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
          <p className="text-sm text-gray-600">Product</p>
          <p className="text-lg font-semibold text-gray-900">{productName}</p>
          
          <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
            <div>
              <p className="text-gray-600">Current Stock</p>
              <p className="text-xl font-bold text-gray-900">{currentStock} units</p>
            </div>
            <div>
              <p className="text-gray-600">Minimum Required</p>
              <p className="text-xl font-bold text-orange-600">{minStock} units</p>
            </div>
          </div>
        </div>

        {/* Reorder Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Reorder Quantity *
          </label>
          <input
            type="number"
            min="1"
            step="1"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Enter quantity to order"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-600"
            required
            disabled={submitting}
          />
          <p className="text-xs text-gray-500 mt-1">
            💡 Suggested: {Math.max(minStock * 2, minStock - currentStock)} units
          </p>
        </div>

        {/* Supplier Note */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Supplier / Notes (Optional)
          </label>
          <textarea
            value={supplierNote}
            onChange={(e) => setSupplierNote(e.target.value)}
            placeholder="e.g., 'Supplier: ABC Wholesale', 'Urgent - needed by Friday'"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-600 resize-none"
            disabled={submitting}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !quantity}
            className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg font-medium hover:bg-gray-900 disabled:opacity-50"
          >
            {submitting ? 'Creating Order...' : 'Create Purchase Order'}
          </button>
        </div>
      </form>
    </ResponsiveModal>
  );
}
