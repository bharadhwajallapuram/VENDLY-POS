'use client';

// ===========================================
// Vendly POS - Payment Modal Component
// ===========================================

import { useState } from 'react';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  totalCents: number;
  onPay: (method: string, amountCents: number) => Promise<void>;
}

const PAYMENT_METHODS = [
  { code: 'cash', label: 'Cash', icon: '💵' },
  { code: 'card', label: 'Card', icon: '💳' },
  { code: 'digital', label: 'Digital Wallet', icon: '📱' },
];

export default function PaymentModal({
  isOpen,
  onClose,
  totalCents,
  onPay,
}: PaymentModalProps) {
  const [selectedMethod, setSelectedMethod] = useState('cash');
  const [tendered, setTendered] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const total = totalCents / 100;
  const tenderedAmount = parseFloat(tendered) || 0;
  const change = tenderedAmount - total;

  const handlePay = async () => {
    setError('');
    setIsProcessing(true);

    try {
      const paymentAmount = selectedMethod === 'cash' 
        ? Math.round(tenderedAmount * 100) 
        : totalCents;

      if (selectedMethod === 'cash' && paymentAmount < totalCents) {
        setError('Insufficient amount tendered');
        setIsProcessing(false);
        return;
      }

      await onPay(selectedMethod, paymentAmount);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const quickAmounts = [20, 50, 100].filter((a) => a >= total);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Payment</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Total */}
        <div className="text-center mb-6">
          <div className="text-sm text-gray-500">Total Due</div>
          <div className="text-4xl font-bold">${total.toFixed(2)}</div>
        </div>

        {/* Payment Method Selection */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          {PAYMENT_METHODS.map((method) => (
            <button
              key={method.code}
              onClick={() => setSelectedMethod(method.code)}
              className={`p-4 rounded-lg border-2 text-center transition-colors ${
                selectedMethod === method.code
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">{method.icon}</div>
              <div className="text-sm font-medium">{method.label}</div>
            </button>
          ))}
        </div>

        {/* Cash-specific: Amount tendered */}
        {selectedMethod === 'cash' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount Tendered
            </label>
            <input
              type="number"
              step="0.01"
              value={tendered}
              onChange={(e) => setTendered(e.target.value)}
              className="input text-2xl text-center"
              placeholder="0.00"
              autoFocus
            />
            
            {/* Quick amounts */}
            <div className="flex gap-2 mt-2">
              {quickAmounts.map((amount) => (
                <button
                  key={amount}
                  onClick={() => setTendered(amount.toString())}
                  className="flex-1 py-2 border rounded-lg hover:bg-gray-50"
                >
                  ${amount}
                </button>
              ))}
              <button
                onClick={() => setTendered(total.toFixed(2))}
                className="flex-1 py-2 border rounded-lg hover:bg-gray-50"
              >
                Exact
              </button>
            </div>

            {/* Change display */}
            {tenderedAmount > 0 && (
              <div className="mt-4 text-center">
                <div className="text-sm text-gray-500">Change Due</div>
                <div
                  className={`text-2xl font-bold ${
                    change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  ${change >= 0 ? change.toFixed(2) : '—'}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 border rounded-lg hover:bg-gray-50"
            disabled={isProcessing}
          >
            Cancel
          </button>
          <button
            onClick={handlePay}
            className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            disabled={isProcessing || (selectedMethod === 'cash' && change < 0)}
          >
            {isProcessing ? 'Processing...' : 'Complete Payment'}
          </button>
        </div>
      </div>
    </div>
  );
}
