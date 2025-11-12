import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Level = { id: string; store_id: string; variant_id: string; qty: number; min_qty: number };

export default function InventoryPage(){
  const [levels, setLevels] = useState<Level[]>([]);
  useEffect(()=>{ api<Level[]>(`/products/inventory/levels`).then(setLevels); },[]);
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Inventory Levels</h1>
      <table className="w-full border bg-white">
        <thead><tr className="bg-gray-50"><th className="p-2">Variant</th><th className="p-2">Store</th><th className="p-2">Qty</th><th className="p-2">Min</th></tr></thead>
        <tbody>
          {levels.map(l=> (
            <tr key={l.id} className="border-t">
              <td className="p-2">{l.variant_id}</td>
              <td className="p-2">{l.store_id}</td>
              <td className="p-2">{l.qty}</td>
              <td className="p-2">{l.min_qty}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}