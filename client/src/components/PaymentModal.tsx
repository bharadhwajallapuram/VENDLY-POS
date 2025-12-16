'use client';

// ===========================================
// Vendly POS - Payment Modal Component
// ===========================================


import { useState, useEffect, useRef } from 'react';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import SplitPaymentInput, { SplitPayment } from './SplitPaymentInput';
import { API_URL } from '@/lib/api';

// Initialize Stripe outside the component to avoid re-creating on every render
const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

// Card Payment Form Component - must be inside Elements provider
interface CardPaymentFormProps {
  clientSecret: string;
  onSuccess: () => void;
  onError: (error: string) => void;
  isProcessing: boolean;
  setIsProcessing: (value: boolean) => void;
  submitRef: React.MutableRefObject<(() => Promise<void>) | null>;
}

const CardPaymentForm: React.FC<CardPaymentFormProps> = ({ 
  clientSecret, 
  onSuccess, 
  onError, 
  isProcessing, 
  setIsProcessing,
  submitRef 
}) => {
  const stripe = useStripe();
  const elements = useElements();

  const handleSubmit = async () => {
    if (!stripe || !elements) {
      onError('Payment system not ready. Please refresh and try again.');
      return;
    }

    setIsProcessing(true);
    try {
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error('Card input not found');
      }

      const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
        payment_method: { card: cardElement },
      });

      if (error) {
        // Provide user-friendly error messages
        let errorMessage = error.message || 'Payment failed';
        
        switch (error.code) {
          case 'card_declined':
            errorMessage = 'Your card was declined. Please try a different card.';
            break;
          case 'insufficient_funds':
            errorMessage = 'Insufficient funds. Please try a different card.';
            break;
          case 'expired_card':
            errorMessage = 'Your card has expired. Please use a different card.';
            break;
          case 'incorrect_cvc':
            errorMessage = 'Incorrect CVC code. Please check and try again.';
            break;
          case 'processing_error':
            errorMessage = 'An error occurred while processing. Please try again.';
            break;
          case 'incorrect_number':
            errorMessage = 'Invalid card number. Please check and try again.';
            break;
        }
        
        throw new Error(errorMessage);
      }

      if (!paymentIntent) {
        throw new Error('Payment was cancelled or could not be completed.');
      }
      
      if (paymentIntent.status === 'requires_action') {
        throw new Error('Additional authentication required. Please complete the verification.');
      }
      
      if (paymentIntent.status !== 'succeeded') {
        throw new Error(`Payment not completed. Status: ${paymentIntent.status}`);
      }

      onSuccess();
    } catch (err: any) {
      onError(err.message || 'Card payment failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Expose submit function to parent
  submitRef.current = handleSubmit;

  return (
    <div>
      <CardElement 
        className="border p-3 rounded-lg" 
        options={{
          style: {
            base: {
              fontSize: '16px',
              color: '#424770',
              '::placeholder': { color: '#aab7c4' },
            },
          },
        }}
      />
      <div className="text-xs text-gray-500 mt-2">Enter your card details above</div>
    </div>
  );
};

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  totalCents: number;
  onPay: (payments: SplitPayment[]) => Promise<void>;
}

const PaymentModal: React.FC<PaymentModalProps> = ({
  isOpen,
  onClose,
  totalCents,
  onPay,
}) => {
  const [splitPayments, setSplitPayments] = useState<SplitPayment[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [showCardInput, setShowCardInput] = useState(false);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [cardAmount, setCardAmount] = useState<number>(0);
  const [useSplitPayment, setUseSplitPayment] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState<string>('cash');
  const [paymentMethods, setPaymentMethods] = useState<Array<{code: string; label: string; enabled: boolean}>>([]);
  
  // Ref to call card payment submit from parent
  const cardSubmitRef = useRef<(() => Promise<void>) | null>(null);

  const total = totalCents / 100;
  const totalPaid = splitPayments.reduce((sum, p) => sum + p.amount, 0);
  const remaining = Math.max(0, total - totalPaid);

  // Fetch payment methods
  useEffect(() => {
    async function fetchMethods() {
      try {
        const res = await fetch('/api/payment-methods');
        const data = await res.json();
        const enabled = data.filter((m: any) => m.enabled);
        setPaymentMethods(enabled);
        if (enabled.length > 0) setSelectedMethod(enabled[0].code);
      } catch {}
    }
    fetchMethods();
  }, []);

  // Watch for card payment in splitPayments OR full payment card selection
  useEffect(() => {
    if (useSplitPayment) {
      const card = splitPayments.find(p => p.method === 'card');
      if (card && card.amount > 0) {
        setShowCardInput(true);
        setCardAmount(card.amount);
      } else {
        setShowCardInput(false);
        setClientSecret(null);
      }
    } else {
      // Full payment mode - show card input if card is selected
      if (selectedMethod === 'card') {
        setShowCardInput(true);
        setCardAmount(total);
      } else {
        setShowCardInput(false);
        setClientSecret(null);
      }
    }
  }, [splitPayments, useSplitPayment, selectedMethod, total]);

  // Fetch Stripe client secret when card payment is added
  useEffect(() => {
    async function fetchClientSecret() {
      if (showCardInput && cardAmount > 0) {
        try {
          const token = typeof window !== 'undefined' ? localStorage.getItem('vendly_token') : null;
          const res = await fetch(`${API_URL}/api/v1/payments/stripe-intent`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              ...(token && { Authorization: `Bearer ${token}` }),
            },
            body: JSON.stringify({ amount: Math.round(cardAmount * 100) }),
          });
          const data = await res.json();
          if (res.ok && data.client_secret) setClientSecret(data.client_secret);
          else setError(data.detail || 'Failed to create payment intent');
        } catch {
          setError('Network error creating payment intent');
        }
      }
    }
    fetchClientSecret();
  }, [showCardInput, cardAmount]);

  // Early return AFTER all hooks
  if (!isOpen) return null;

  // Handle card payment success
  const handleCardSuccess = async () => {
    try {
      const paymentsToProcess = useSplitPayment 
        ? splitPayments 
        : [{ method: 'card', amount: total }];
      await onPay(paymentsToProcess);
      setShowCardInput(false);
      setClientSecret(null);
      onClose();
    } catch (err: any) {
      // Show error but don't close modal - payment was charged but sale failed
      setError(err.message || 'Sale failed after payment. Please contact support.');
    }
  };

  // Handle card payment error (declined, insufficient funds, cancelled, etc.)
  const handleCardError = (errorMessage: string) => {
    setError(errorMessage);
    // Don't close modal - let user try again or choose different payment method
  };

  const handlePay = async () => {
    setError('');
    
    // If card payment, use the card form submit
    if (showCardInput && clientSecret && cardSubmitRef.current) {
      try {
        await cardSubmitRef.current();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Card payment failed. Please try again.');
      }
      return;
    }

    setIsProcessing(true);
    try {
      let paymentsToProcess: SplitPayment[];
      
      if (useSplitPayment) {
        // Split payment mode
        if (splitPayments.length === 0) {
          setError('Enter at least one payment method');
          setIsProcessing(false);
          return;
        }
        if (remaining > 0) {
          setError(`Remaining amount ₹${remaining.toFixed(2)} not covered. Please add another payment method.`);
          setIsProcessing(false);
          return;
        }
        paymentsToProcess = splitPayments;
      } else {
        // Full payment mode - single payment with selected method
        if (!selectedMethod) {
          setError('Please select a payment method');
          setIsProcessing(false);
          return;
        }
        paymentsToProcess = [{ method: selectedMethod, amount: total }];
      }
      
      try {
        await onPay(paymentsToProcess);
        onClose();
      } catch (paymentErr) {
        const errorMessage = paymentErr instanceof Error ? paymentErr.message : 'Payment processing failed';
        console.error('Payment error:', paymentErr);
        setError(errorMessage || 'Unable to process payment. Please check your connection and try again.');
      }
    } finally {
      setIsProcessing(false);
    }
  };

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
          <div className="text-4xl font-bold">₹{total.toFixed(2)}</div>
        </div>

        {/* Payment Mode Toggle */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useSplitPayment}
              onChange={(e) => {
                setUseSplitPayment(e.target.checked);
                setSplitPayments([]);
              }}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-600">Split Payment</span>
          </label>
        </div>

        {/* Full Payment Mode (Default) */}
        {!useSplitPayment && (
          <div className="border rounded-lg p-4 mb-4">
            <h4 className="font-medium mb-3">Select Payment Method</h4>
            <div className="grid grid-cols-2 gap-2">
              {paymentMethods.map((method) => (
                <button
                  key={method.code}
                  onClick={() => setSelectedMethod(method.code)}
                  className={`p-3 rounded-lg border-2 text-center transition-colors ${
                    selectedMethod === method.code
                      ? 'border-gray-500 bg-gray-50 text-gray-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {method.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Split Payment UI (Optional) */}
        {useSplitPayment && (
          <SplitPaymentInput
            total={total}
            onChange={setSplitPayments}
          />
        )}

        {/* Stripe Card Input (inline) */}
        {showCardInput && stripePromise && (
          <div className="my-4 border rounded-lg p-4">
            <h4 className="font-medium mb-3">Card Details</h4>
            {clientSecret ? (
              <Elements stripe={stripePromise} options={{ clientSecret }}>
                <CardPaymentForm
                  clientSecret={clientSecret}
                  onSuccess={handleCardSuccess}
                  onError={handleCardError}
                  isProcessing={isProcessing}
                  setIsProcessing={setIsProcessing}
                  submitRef={cardSubmitRef}
                />
              </Elements>
            ) : (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-800"></div>
                <span className="ml-2 text-gray-500">Loading payment form...</span>
              </div>
            )}
          </div>
        )}
        {showCardInput && !stripePromise && (
          <div className="my-4 p-3 bg-yellow-50 text-yellow-700 rounded-lg text-sm">
            Stripe is not configured. Please set NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY environment variable.
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
            disabled={isProcessing || (useSplitPayment && remaining > 0) || (showCardInput && !clientSecret)}
          >
            {isProcessing ? 'Processing...' : `Pay ₹${total.toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
}

export default PaymentModal;
