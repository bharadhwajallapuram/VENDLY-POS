"use client";

import React, { useState } from "react";
import SplitPaymentInput, { SplitPayment } from "../../components/SplitPaymentInput";


export default function RefundPage() {
  const [saleId, setSaleId] = useState("");
  const [sale, setSale] = useState<any>(null);
  const [selected, setSelected] = useState<{ [id: number]: number }>({});
  const [reason, setReason] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [splitPayments, setSplitPayments] = useState<SplitPayment[]>([]);

  async function fetchSale() {
    setError("");
    setSale(null);
    setSelected({});
    setResult(null);
    try {
      const token = localStorage.getItem("vendly_token");
      const res = await fetch(`/api/v1/sales/${saleId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Sale not found");
      setSale(await res.json());
    } catch (e: any) {
      setError(e.message || "Error fetching sale");
    }
  }

  async function submitRefund() {
    setError("");
    setResult(null);
    try {
      const items = Object.entries(selected)
        .filter(([id, qty]) => qty > 0)
        .map(([id, qty]) => ({ sale_item_id: Number(id), quantity: qty }));
      if (items.length === 0) throw new Error("Select at least one item to refund");
      if (splitPayments.length === 0) throw new Error("Enter at least one payment method");
      const token = localStorage.getItem("vendly_token");
      const refundPayload = {
        items,
        reason,
        payments: splitPayments,
      };
      const res = await fetch(`/api/v1/sales/${saleId}/refund`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(refundPayload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Refund failed");
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Refund error");
    }
  }

  return (
    <div className="max-w-lg mx-auto p-4">
      <h2 className="text-xl font-bold mb-4">Refund/Return Sale</h2>
      <div className="mb-4 flex gap-2">
        <input
          type="number"
          value={saleId}
          onChange={e => setSaleId(e.target.value)}
          className="border p-2 flex-1"
          placeholder="Enter Sale ID"
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={fetchSale}>
          Lookup
        </button>
      </div>
      {sale && (
        <div className="mb-4">
          <h3 className="font-semibold mb-2">Items in Sale #{sale.id}</h3>
          <table className="w-full text-sm mb-2">
            <thead>
              <tr>
                <th>Item</th>
                <th>Sold</th>
                <th>Refund</th>
              </tr>
            </thead>
            <tbody>
              {sale.items.map((item: any) => (
                <tr key={item.id}>
                  <td>{item.product_name || item.name}</td>
                  <td className="text-center">{item.quantity}</td>
                  <td className="text-center">
                    <input
                      type="number"
                      min={0}
                      max={item.quantity}
                      value={selected[item.id] || 0}
                      onChange={e => setSelected(s => ({ ...s, [item.id]: Number(e.target.value) }))}
                      className="border p-1 w-16 text-center"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <textarea
            className="border p-2 w-full mb-2"
            placeholder="Reason for refund (optional)"
            value={reason}
            onChange={e => setReason(e.target.value)}
          />
          {/* Split Payment UI */}
          <SplitPaymentInput
            total={sale.items.reduce((sum: number, item: any) => sum + (selected[item.id] || 0) * item.unit_price, 0)}
            onChange={setSplitPayments}
          />
          <button className="bg-green-600 text-white px-4 py-2 rounded w-full" onClick={submitRefund}>
            Process Refund
          </button>
        </div>
      )}
      {result && (
        <div className="bg-green-100 text-green-800 p-3 rounded mb-2">
          Refund successful! Refunded: ${result.refund_amount} | Status: {result.status}
        </div>
      )}
      {error && <div className="bg-red-100 text-red-800 p-3 rounded mb-2">{error}</div>}
    </div>
  );
}
