import React, { useState } from "react";

export default function UPIPaymentPage() {
  const [amount, setAmount] = useState(10000); // paise (₹100)
  const [vpa, setVpa] = useState("");
  const [upiUrl, setUpiUrl] = useState("");
  const [qr, setQr] = useState("");
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [success, setSuccess] = useState(false);

  async function createUPIPayment() {
    setError("");
    setUpiUrl("");
    setQr("");
    setSuccess(false);
    try {
      const res = await fetch("/api/v1/payments/upi-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount, vpa }),
      });
      const data = await res.json();
      if (res.ok) {
        setUpiUrl(data.upi_url);
        setQr(data.qr_code_base64);
        setShowModal(true);
      } else setError(data.detail || "Failed to create UPI request");
    } catch (e) {
      setError("Network error");
    }
  }

  return (
    <div className="max-w-md mx-auto p-4">
      <h2 className="text-xl font-bold mb-2">UPI Payment Demo</h2>
      <input
        type="number"
        value={amount}
        onChange={e => setAmount(Number(e.target.value))}
        className="border p-2 mb-2 w-full"
        min={1}
        step={1}
        placeholder="Amount in paise (e.g., 10000 = ₹100)"
      />
      <input
        type="text"
        value={vpa}
        onChange={e => setVpa(e.target.value)}
        className="border p-2 mb-2 w-full"
        placeholder="Enter UPI ID (e.g., user@upi)"
      />
      <button
        className="bg-green-600 text-white px-4 py-2 rounded"
        onClick={createUPIPayment}
      >
        Pay with UPI
      </button>
      {showModal && upiUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative">
            <button className="absolute top-2 right-2 text-gray-500" onClick={() => setShowModal(false)}>&times;</button>
            <h3 className="text-lg font-semibold mb-2">Scan QR or Pay with UPI App</h3>
            {qr && (
              <img src={`data:image/png;base64,${qr}`} alt="UPI QR" className="w-48 h-48 mx-auto mb-2" />
            )}
            <a href={upiUrl} target="_blank" rel="noopener noreferrer" className="block text-blue-600 underline mt-2 mb-2">Open in UPI App</a>
            <p className="text-sm text-gray-600 mb-2">After payment, click below to confirm:</p>
            <button
              className="bg-green-600 text-white px-4 py-2 rounded w-full"
              onClick={() => { setSuccess(true); setShowModal(false); }}
            >
              I have paid
            </button>
          </div>
        </div>
      )}
      {success && <p className="text-green-700 mt-4">Payment marked as complete!</p>}
      {error && <p className="text-red-600 mt-2">{error}</p>}
    </div>
  );
}
