import React, { useState, useEffect } from "react";


export type PaymentMethod = string;

export interface PaymentMethodOption {
  code: string;
  label: string;
  enabled: boolean;
}

export interface SplitPayment {
  method: PaymentMethod;
  amount: number;
  reference?: string;
}

interface SplitPaymentInputProps {
  total: number;
  onChange: (payments: SplitPayment[]) => void;
  initial?: SplitPayment[];
}

const SplitPaymentInput: React.FC<SplitPaymentInputProps> = ({ total, onChange, initial = [] }) => {
  const [payments, setPayments] = useState<SplitPayment[]>(initial);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethodOption[]>([]);
  const [newMethod, setNewMethod] = useState<string>("");
  const [newAmount, setNewAmount] = useState(0);
  const [newReference, setNewReference] = useState("");

  // Fetch payment methods from API (real-time: polling every 10s)
  useEffect(() => {
    let isMounted = true;
    async function fetchMethods() {
      try {
        const res = await fetch("/api/payment-methods");
        const data = await res.json();
        if (isMounted) {
          setPaymentMethods(data.filter((m: PaymentMethodOption) => m.enabled));
          if (!newMethod && data.length > 0) setNewMethod(data[0].code);
        }
      } catch {}
    }
    fetchMethods();
    const interval = setInterval(fetchMethods, 10000); // Poll every 10s
    return () => { isMounted = false; clearInterval(interval); };
  }, [newMethod]);

  const totalPaid = payments.reduce((sum, p) => sum + p.amount, 0);
  const remaining = Math.max(0, total - totalPaid);

  function addPayment() {
    if (newAmount <= 0 || newAmount > remaining) return;
    setPayments(ps => {
      const updated = [...ps, { method: newMethod as any, amount: newAmount, reference: newReference }];
      onChange(updated);
      return updated;
    });
    setNewAmount(0);
    setNewReference("");
  }

  function removePayment(idx: number) {
    setPayments(ps => {
      const updated = ps.filter((_, i) => i !== idx);
      onChange(updated);
      return updated;
    });
  }

  return (
    <div className="border rounded p-3 mb-4">
      <h4 className="font-semibold mb-2">Split Payment</h4>
      <div className="mb-2">
        {payments.map((p, i) => {
          const method = paymentMethods.find(m => m.code === p.method);
          return (
            <div key={i} className="flex items-center gap-2 mb-1">
              <span className="w-20">{method ? method.label : p.method}</span>
              <span className="w-24">₹{p.amount.toFixed(2)}</span>
              {p.reference && <span className="text-xs text-gray-500">Ref: {p.reference}</span>}
              <button className="text-red-500 ml-2" onClick={() => removePayment(i)}>Remove</button>
            </div>
          );
        })}
      </div>
      {remaining > 0 && paymentMethods.length > 0 && (
        <div className="flex flex-col md:flex-row gap-2 items-center mb-2">
          <select value={newMethod} onChange={e => setNewMethod(e.target.value)} className="border p-1">
            {paymentMethods.map((m) => (
              <option key={m.code} value={m.code}>{m.label}</option>
            ))}
          </select>
          <input
            type="number"
            min={1}
            max={remaining}
            value={newAmount}
            onChange={e => setNewAmount(Number(e.target.value))}
            className="border p-1 w-24"
            placeholder="Amount"
          />
          {(newMethod === "card" || newMethod === "upi" || newMethod === "wallet") && (
            <input
              type="text"
              value={newReference}
              onChange={e => setNewReference(e.target.value)}
              className="border p-1 w-32"
              placeholder="Reference/Txn ID"
            />
          )}
          <button className="bg-blue-600 text-white px-3 py-1 rounded" onClick={addPayment}>
            Add
          </button>
        </div>
      )}
      <div className="text-sm text-gray-700">Total: ₹{total.toFixed(2)} | Paid: ₹{totalPaid.toFixed(2)} | Remaining: ₹{remaining.toFixed(2)}</div>
    </div>
  );
}

export default SplitPaymentInput;
