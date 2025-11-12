import { useEffect, useMemo, useState } from "react";
import { Products, Sales, ProductOut } from "../../lib/api";
import { useCart } from "../../store/cart";
import { useAuth } from "../../contexts/AuthContext";
import PaymentModal from "../../components/PaymentModal";

const STORE_ID = "11111111-1111-1111-1111-111111111111"; // replace with real
const REGISTER_ID = "22222222-2222-2222-2222-222222222222"; // replace with real

export default function POSPage(){
  const cart = useCart();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ProductOut[]>([]);
  const [sale, setSale] = useState<{id:string}|null>(null);
  const [payOpen, setPayOpen] = useState(false);
  const [wsMsg, setWsMsg] = useState<string>("");

  // Open a sale on first interaction
  useEffect(()=>{
    (async()=>{
      const s = await Sales.open(STORE_ID, REGISTER_ID);
      setSale({id: s.id});
    })();
  },[]);

  // Search products
  async function search(){ setResults(await Products.list(query)); }

  // Add product (first variant) to cart
  function addProduct(p: ProductOut){
    if(!p.variants?.length) return;
    const v = p.variants[0];
    cart.add({ variantId: v.id, name: p.name, qty: 1, priceCents: v.price_cents });
  }

  // Push cart to backend as lines
  async function syncLines(){
    if(!sale) return;
    for(const l of cart.lines){
      await Sales.addLine(sale.id, { variant_id: l.variantId, qty: l.qty, unit_price_cents: l.priceCents });
    }
  }

  async function onPay(method: string, amountCents: number){
    if(!sale) return;
    await syncLines();
    await Sales.addPayment(sale.id, { method_code: method, amount_cents: amountCents });
    const done = await Sales.complete(sale.id);
    setWsMsg(`Sale ${done.id} completed: $${(done.total_cents/100).toFixed(2)}`);
    cart.clear();
    const s = await Sales.open(STORE_ID, REGISTER_ID); // new sale
    setSale({id: s.id});
  }

  // WebSocket to receive broadcasts (sale.completed)
  useEffect(()=>{
    const url = (import.meta.env.VITE_API_URL || "").replace(/^http/,'ws') + "/api/v1/ws";
    const ws = new WebSocket(url);
    ws.onmessage = (evt)=>{ try{ const msg = JSON.parse(evt.data); if(msg.event){ setWsMsg(`${msg.event}: $${(msg.total_cents/100).toFixed(2)}`);} }catch{} };
    return ()=> ws.close();
  },[]);

  const subtotal = useMemo(()=> cart.subtotal(), [cart.lines]);
  
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const isManagerOrAdmin = user?.role === 'admin' || user?.role === 'manager';

  return (
    <div className="p-6">
      {/* Header with User Role Info */}
      <div className="mb-6 bg-gray-50 rounded-lg p-4 border">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold">Point of Sale</h1>
            <p className="text-sm text-gray-600">Logged in as {user?.full_name || user?.email} ({user?.role})</p>
          </div>
          <div className="flex items-center space-x-3">
            {user?.role === 'cashier' && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Cashier Access</span>
            )}
            {user?.role === 'manager' && (
              <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">Manager Access</span>
            )}
            {user?.role === 'admin' && (
              <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">Admin Access</span>
            )}
          </div>
        </div>
        
        {/* Role-specific features notification */}
        <div className="mt-3 text-sm">
          {user?.role === 'cashier' && (
            <div className="text-blue-700">
              <strong>Available:</strong> Process sales, search products, handle payments
            </div>
          )}
          {user?.role === 'manager' && (
            <div className="text-purple-700">
              <strong>Available:</strong> All cashier features + discounts, refunds, manager override
            </div>
          )}
          {user?.role === 'admin' && (
            <div className="text-red-700">
              <strong>Available:</strong> All features + system administration, user management
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left: Search & Catalog */}
      <div className="col-span-1 space-y-3">
        <div className="space-y-2">
          <div className="flex gap-2">
            <input className="border rounded px-3 py-2 w-full" placeholder="Scan or search..." value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={(e)=>{ if(e.key==='Enter') search(); }}/>
            <button className="px-3 py-2 rounded bg-black text-white" onClick={search}>Search</button>
          </div>
          
          {/* Role-specific search features */}
          {isManagerOrAdmin && (
            <div className="flex gap-2">
              <button className="px-2 py-1 text-xs border rounded bg-gray-50 hover:bg-gray-100">
                Advanced Search
              </button>
              <button className="px-2 py-1 text-xs border rounded bg-gray-50 hover:bg-gray-100">
                Low Stock
              </button>
            </div>
          )}
          {isAdmin && (
            <div className="text-xs text-gray-500">Admin: Access to all products including inactive items</div>
          )}
        </div>
        <div className="border rounded divide-y max-h-[60vh] overflow-auto">
          {results.map(p=> (
            <div key={p.id} className="p-3 hover:bg-gray-50 cursor-pointer" onClick={()=>addProduct(p)}>
              <div className="font-medium">{p.name}</div>
              <div className="text-sm text-gray-600">{p.sku} · {p.variants?.[0]?.sku} · ${(p.variants?.[0]?.price_cents||0/100).toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Middle: Cart */}
      <div className="col-span-1">
        <h2 className="text-lg font-semibold mb-2">Cart</h2>
        <div className="border rounded divide-y min-h-[300px]">
          {cart.lines.map(l=> (
            <div key={l.variantId} className="flex items-center gap-2 p-3">
              <div className="flex-1">{l.name}</div>
              <div className="flex items-center gap-2">
                <button className="px-2 border rounded" onClick={()=>cart.dec(l.variantId)}>-</button>
                <span>{l.qty}</span>
                <button className="px-2 border rounded" onClick={()=>cart.inc(l.variantId)}>+</button>
              </div>
              <div className="w-24 text-right">${((l.priceCents*l.qty)/100).toFixed(2)}</div>
              <button className="px-2 border rounded" onClick={()=>cart.remove(l.variantId)}>x</button>
            </div>
          ))}
          {cart.lines.length===0 && <div className="p-6 text-center text-gray-500">Scan or search to add items</div>}
        </div>
      </div>

      {/* Right: Totals & Payment */}
      <div className="col-span-1 space-y-3">
        <div className="border rounded p-4 space-y-2">
          <div className="flex justify-between"><span>Subtotal</span><span>${(subtotal/100).toFixed(2)}</span></div>
          <div className="flex justify-between text-gray-500"><span>Tax</span><span>$0.00</span></div>
          <div className="flex justify-between text-gray-500"><span>Discount</span><span>$0.00</span></div>
          <div className="border-t pt-2 flex justify-between font-semibold text-lg"><span>Total</span><span>${(subtotal/100).toFixed(2)}</span></div>
          
          {/* Role-specific payment options */}
          {user?.role === 'cashier' && (
            <div className="text-xs text-blue-600 mb-2">Cashier: Standard payments only</div>
          )}
          {isManagerOrAdmin && (
            <div className="text-xs text-purple-600 mb-2">Manager+: All payment methods available</div>
          )}
          
          <button className="w-full py-3 rounded bg-green-600 text-white text-lg" disabled={!cart.lines.length || !sale} onClick={()=>setPayOpen(true)}>Take Payment</button>
          {wsMsg && <div className="text-sm text-green-700">{wsMsg}</div>}
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-2 border rounded" onClick={()=>cart.clear()}>Clear</button>
          {isManagerOrAdmin && (
            <button className="px-3 py-2 border rounded bg-yellow-50 text-yellow-800 hover:bg-yellow-100" 
                    title="Manager/Admin: Apply discount">
              Discount
            </button>
          )}
          {isManagerOrAdmin && (
            <button className="px-3 py-2 border rounded bg-orange-50 text-orange-800 hover:bg-orange-100" 
                    title="Manager/Admin: Process refund">
              Refund
            </button>
          )}
          {isAdmin && (
            <button className="px-3 py-2 border rounded bg-red-50 text-red-800 hover:bg-red-100" 
                    title="Admin: Void transaction">
              Void
            </button>
          )}
        </div>
      </div>

      <PaymentModal open={payOpen} totalCents={subtotal} onPay={onPay} onClose={()=>setPayOpen(false)} />
      </div>
    </div>
  );
}