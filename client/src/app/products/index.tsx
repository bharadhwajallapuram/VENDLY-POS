import { useEffect, useState } from "react";
import { Products, ProductOut, ProductIn } from "../../lib/api";

export default function ProductsPage(){
  const [items, setItems] = useState<ProductOut[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  async function load(){
    setLoading(true);
    try { setItems(await Products.list(q)); } finally { setLoading(false); }
  }
  useEffect(()=>{ load(); },[]);

  async function onCreate(){
    const body: ProductIn = { name: "Sample Product", sku: crypto.randomUUID().slice(0,8), variants: [{ sku: `VAR-${crypto.randomUUID().slice(0,6)}`, price_cents: 999 }] };
    const p = await Products.create(body);
    setItems([p, ...items]);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <input className="border rounded px-3 py-2" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search products..."/>
        <button className="px-3 py-2 rounded bg-black text-white" onClick={load}>{loading?"Loading...":"Search"}</button>
        <button className="px-3 py-2 rounded bg-green-600 text-white" onClick={onCreate}>+ Quick Add</button>
      </div>
      <table className="w-full border bg-white">
        <thead><tr className="bg-gray-50"><th className="p-2 text-left">Name</th><th className="p-2">SKU</th><th className="p-2">Variants</th><th className="p-2"></th></tr></thead>
        <tbody>
          {items.map(p=> (
            <tr key={p.id} className="border-t">
              <td className="p-2">{p.name}</td>
              <td className="p-2">{p.sku}</td>
              <td className="p-2">{p.variants.map(v=>v.sku).join(", ")}</td>
              <td className="p-2 text-right">
                <button className="px-2 py-1 border rounded" onClick={async()=>{ await Products.del(p.id); setItems(items.filter(x=>x.id!==p.id)); }}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}