import { useState } from "react";
import Keypad from "./Keypad";

export default function PaymentModal({
  open, totalCents, onPay, onClose
}:{
  open: boolean;
  totalCents: number;
  onPay: (method: string, amountCents: number) => Promise<void>;
  onClose: () => void;
}){
  const [method, setMethod] = useState("cash");
  const [amount, setAmount] = useState(totalCents);
  if(!open) return null;
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white p-6 rounded-2xl shadow-xl w-[420px] space-y-4">
        <h2 className="text-lg font-semibold">Take Payment</h2>
        <div className="space-y-2">
          <label className="block text-sm">Method</label>
          <select className="border rounded p-2 w-full" value={method} onChange={e=>setMethod(e.target.value)}>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
          </select>
        </div>
        <div className="space-y-2">
          <label className="block text-sm">Amount (¢)</label>
          <input className="border rounded p-2 w-full" value={amount} onChange={e=>setAmount(parseInt(e.target.value||"0",10))}/>
          <Keypad onEnter={(v)=>setAmount(v)} />
        </div>
        <div className="flex gap-2 justify-end">
          <button className="px-3 py-2" onClick={onClose}>Cancel</button>
          <button className="px-4 py-2 bg-black text-white rounded" onClick={async()=>{ await onPay(method, amount); onClose(); }}>Pay</button>
        </div>
      </div>
    </div>
  );
}