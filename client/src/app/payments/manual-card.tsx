import React, { useState } from "react";

export default function ManualCardPaymentPage() {
  const [amount, setAmount] = useState(1000); // cents
  const [reference, setReference] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  function handleManualCardEntry() {
    setShowModal(true);
    setSuccess(false);
    setError("");
  }

  function confirmManualCardPayment() {
    if (!reference) {
      setError("Please enter the card approval/reference code.");
      return;
    }
    setSuccess(true);
    setShowModal(false);
  }

  return (
    <div className="max-w-md mx-auto p-4">
      <h2 className="text-xl font-bold mb-2">Manual Card Payment Entry</h2>
      <input
        type="number"
        value={amount}
        onChange={e => setAmount(Number(e.target.value))}
        className="border p-2 mb-2 w-full"
        min={1}
        step={1}
        placeholder="Amount in cents"
      />
      <button
        className="bg-purple-600 text-white px-4 py-2 rounded"
        onClick={handleManualCardEntry}
      >
        Enter Card Payment Manually
      </button>
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative">
            <button className="absolute top-2 right-2 text-gray-500" onClick={() => setShowModal(false)}>&times;</button>
            <h3 className="text-lg font-semibold mb-2">Manual Card Payment Entry</h3>
            <p className="mb-2 text-gray-700">Enter the card approval/reference code from the POS terminal after confirming payment.</p>
            <input
              type="text"
              value={reference}
              onChange={e => setReference(e.target.value)}
              className="border p-2 mb-2 w-full"
              placeholder="Card Approval/Reference Code"
            />
            <button
              className="bg-green-600 text-white px-4 py-2 rounded w-full"
              onClick={confirmManualCardPayment}
            >
              Confirm Card Payment
            </button>
            {error && <p className="text-red-600 mt-2">{error}</p>}
          </div>
        </div>
      )}
      {success && <p className="text-green-700 mt-4">Manual card payment recorded!</p>}
    </div>
  );
}
