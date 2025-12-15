"use client";
import React, { useState } from "react";
import { API_URL } from "@/lib/api";

export default function ReturnsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState<"id" | "phone" | "name">("id");
  const [salesList, setSalesList] = useState<any[]>([]);
  const [sale, setSale] = useState<any>(null);
  const [selected, setSelected] = useState<{ [id: number]: number }>({});
  const [reason, setReason] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<"refund" | "return">("refund");

  async function fetchSales() {
    setError("");
    setSale(null);
    setSalesList([]);
    setSelected({});
    setResult(null);
    try {
      const token = localStorage.getItem("vendly_token");
      let url = "";
      if (searchType === "id") {
        // Direct sale lookup by ID
        const res = await fetch(`${API_URL}/api/v1/sales/${searchQuery}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error("Sale not found");
        setSale(await res.json());
        return;
      } else {
        // Search by phone or name (requires backend support)
        url = `${API_URL}/api/v1/sales?${searchType === "phone" ? "customer_phone" : "customer_name"}=${encodeURIComponent(searchQuery)}`;
      }
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("No sales found");
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        setSalesList(data);
      } else if (data.items && Array.isArray(data.items) && data.items.length > 0) {
        setSalesList(data.items);
      } else {
        throw new Error("No sales found for this customer");
      }
    } catch (e: any) {
      setError(e.message || "Error fetching sales");
    }
  }

  function selectSale(s: any) {
    setSale(s);
    setSalesList([]);
  }

  async function submitAction() {
    setError("");
    setResult(null);
    try {
      // Validate employee ID first
      if (!employeeId.trim()) {
        throw new Error("Employee ID is required to process refund/return");
      }
      const items = Object.entries(selected)
        .filter(([id, qty]) => qty > 0)
        .map(([id, qty]) => ({ sale_item_id: Number(id), quantity: qty }));
      if (items.length === 0) throw new Error("Select at least one item");
      if (!sale) throw new Error("No sale selected");
      const token = localStorage.getItem("vendly_token");
      const endpoint = mode === "refund"
        ? `${API_URL}/api/v1/sales/${sale.id}/refund`
        : `${API_URL}/api/v1/sales/${sale.id}/return`;
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ items, reason, employee_id: employeeId.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `${mode.charAt(0).toUpperCase() + mode.slice(1)} failed`);
      setResult(data);
      // Clear employee ID after successful action
      setEmployeeId("");
    } catch (e: any) {
      setError(e.message || `${mode.charAt(0).toUpperCase() + mode.slice(1)} error`);
    }
  }

  return (
    <div className="max-w-lg mx-auto p-4">
      <h2 className="text-xl font-bold mb-4">Refund/Return Sale</h2>
      <div className="mb-2 flex gap-2">
        <select
          value={searchType}
          onChange={e => setSearchType(e.target.value as "id" | "phone" | "name")}
          className="border p-2"
        >
          <option value="id">Sale ID</option>
          <option value="phone">Customer Phone</option>
          <option value="name">Customer Name</option>
        </select>
        <input
          type={searchType === "id" ? "number" : "text"}
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="border p-2 flex-1"
          placeholder={searchType === "id" ? "Enter Sale ID" : searchType === "phone" ? "Enter Phone" : "Enter Name"}
        />
        <button className="bg-gray-800 text-white px-4 py-2 rounded" onClick={fetchSales}>
          Lookup
        </button>
      </div>
      {salesList.length > 0 && (
        <div className="mb-4 border rounded p-2 bg-gray-50">
          <div className="font-semibold mb-2">Select a sale:</div>
          <ul>
            {salesList.map((s: any) => (
              <li key={s.id} className="flex justify-between items-center py-1 border-b last:border-b-0">
                <span>Sale #{s.id} - {s.created_at ? new Date(s.created_at).toLocaleString() : ""}</span>
                <button className="bg-gray-700 text-white px-2 py-1 rounded text-xs" onClick={() => selectSale(s)}>Select</button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="mb-4 flex gap-2">
        <button
          className={`px-4 py-2 rounded ${mode === "refund" ? "bg-gray-700 text-white" : "bg-gray-200"}`}
          onClick={() => setMode("refund")}
        >
          Refund
        </button>
        <button
          className={`px-4 py-2 rounded ${mode === "return" ? "bg-green-500 text-white" : "bg-gray-200"}`}
          onClick={() => setMode("return")}
        >
          Return
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
                <th>{mode === "refund" ? "Refund" : "Return"}</th>
              </tr>
            </thead>
            <tbody>
              {sale.items.map((item: any) => (
                <tr key={item.id}>
                  <td>{item.product_name || item.name}</td>
                  <td className="text-center">{item.quantity}</td>
                  <td className="text-center">
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={selected[item.id] || ""}
                      onChange={e => {
                        const raw = e.target.value;
                        if (raw === "") {
                          setSelected(s => ({ ...s, [item.id]: 0 }));
                        } else {
                          const num = parseInt(raw, 10);
                          if (!isNaN(num)) {
                            setSelected(s => ({ ...s, [item.id]: Math.min(Math.max(0, num), item.quantity) }));
                          }
                        }
                      }}
                      className="border p-1 w-16 text-center"
                      placeholder="0"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mb-3">
            <label className="block text-sm font-semibold mb-1 text-red-600">
              Employee ID *
            </label>
            <input
              type="text"
              className="border p-2 w-full"
              placeholder="Enter your Employee ID to authorize"
              value={employeeId}
              onChange={e => setEmployeeId(e.target.value)}
              required
            />
          </div>
          <textarea
            className="border p-2 w-full mb-2"
            placeholder={`Reason for ${mode} (optional)`}
            value={reason}
            onChange={e => setReason(e.target.value)}
          />
          <button 
            className={`bg-${mode === "refund" ? "blue" : "green"}-600 text-white px-4 py-2 rounded w-full ${!employeeId.trim() ? "opacity-50 cursor-not-allowed" : ""}`} 
            onClick={submitAction}
            disabled={!employeeId.trim()}
          >
            {mode === "refund" ? "Process Refund" : "Process Return"}
          </button>
        </div>
      )}
      {result && (
        <div className="bg-green-100 text-green-800 p-3 rounded mb-2">
          {mode.charAt(0).toUpperCase() + mode.slice(1)} successful! Amount: ${result.refund_amount || result.return_amount} | Status: {result.status}
        </div>
      )}
      {error && <div className="bg-red-100 text-red-800 p-3 rounded mb-2">{error}</div>}
    </div>
  );
}
