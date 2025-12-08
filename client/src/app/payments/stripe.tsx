import React, { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Elements, CardElement, useStripe, useElements } from "@stripe/react-stripe-js";

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "");

function PaymentForm({ clientSecret, amount, onSuccess, onError }: { clientSecret: string, amount: number, onSuccess: () => void, onError: (msg: string) => void }) {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProcessing(true);
    setError("");
    if (!stripe || !elements) {
      setError("Stripe not loaded");
      setProcessing(false);
      return;
    }
    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setError("Card input not found");
      setProcessing(false);
      return;
    }
    const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
      payment_method: { card: cardElement },
    });
    if (stripeError) {
      setError(stripeError.message || "Payment failed");
      setProcessing(false);
      onError(stripeError.message || "Payment failed");
    } else if (paymentIntent && paymentIntent.status === "succeeded") {
      setProcessing(false);
      onSuccess();
    } else {
      setError("Payment not completed");
      setProcessing(false);
      onError("Payment not completed");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <CardElement className="border p-2 rounded" />
      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-2 rounded w-full"
        disabled={processing}
      >
        {processing ? "Processing..." : `Pay $${(amount / 100).toFixed(2)}`}
      </button>
      {error && <p className="text-red-600 mt-2">{error}</p>}
    </form>
  );
}

export default function StripePaymentPage() {
  const [amount, setAmount] = useState(1000); // cents
  const [clientSecret, setClientSecret] = useState("");
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [success, setSuccess] = useState(false);

  async function createPaymentIntent() {
    setError("");
    setSuccess(false);
    try {
      const res = await fetch("/api/v1/payments/stripe-intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount, currency: "usd" }),
      });
      const data = await res.json();
      if (res.ok) {
        setClientSecret(data.client_secret);
        setShowModal(true);
      } else setError(data.detail || "Failed to create payment intent");
    } catch (e) {
      setError("Network error");
    }
  }

  return (
    <div className="max-w-md mx-auto p-4">
      <h2 className="text-xl font-bold mb-2">Stripe Payment Demo</h2>
      <input
        type="number"
        value={amount}
        onChange={e => setAmount(Number(e.target.value))}
        className="border p-2 mb-2 w-full"
        min={1}
        step={1}
      />
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded"
        onClick={createPaymentIntent}
      >
        Pay with Card / Wallet
      </button>
      {showModal && clientSecret && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative">
            <button className="absolute top-2 right-2 text-gray-500" onClick={() => setShowModal(false)}>&times;</button>
            <h3 className="text-lg font-semibold mb-2">Enter Card Details</h3>
            <Elements stripe={stripePromise} options={{ clientSecret }}>
              <PaymentForm
                clientSecret={clientSecret}
                amount={amount}
                onSuccess={() => { setSuccess(true); setShowModal(false); }}
                onError={msg => setError(msg)}
              />
            </Elements>
            <p className="text-sm text-gray-600 mt-4">Do not close this window until payment is complete.</p>
          </div>
        </div>
      )}
      {success && <p className="text-green-700 mt-4">Payment successful!</p>}
      {error && <p className="text-red-600 mt-2">{error}</p>}
    </div>
  );
}
