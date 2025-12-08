'use client';

// ===========================================
// Vendly POS - Point of Sale Page
// ===========================================

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import PaymentModal from '@/components/PaymentModal';
import Receipt from '@/components/Receipt';
import { useRef } from 'react';
import { useCart } from '@/store/cart';
import { useAuth } from '@/store/auth';
import { API_URL } from '@/lib/api';

// Simple product type for now
interface SimpleProduct {
  id: number;
  name: string;
  price: number;
  sku?: string;
  quantity: number;
}

function POSContent() {
  const receiptRef = useRef<HTMLDivElement>(null);
  const cart = useCart();
  const { user } = useAuth();
  
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState<SimpleProduct[]>([]);
  const [payOpen, setPayOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastSaleId, setLastSaleId] = useState<number | null>(null);
  const [showReceiptPrompt, setShowReceiptPrompt] = useState(false);
  const [lastSale, setLastSale] = useState<any>(null);

  // Customer details state
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerId, setCustomerId] = useState<number | null>(null);

  // Load products on mount
  useEffect(() => {
    loadProducts();
  }, []);

  async function loadProducts() {
    setLoading(true);
    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/products`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setProducts(data.items || data || []);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  }

  // Filter products by search query
  const filteredProducts = products.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.sku?.toLowerCase().includes(query.toLowerCase())
  );

  // Add product to cart
  function addToCart(product: SimpleProduct) {
    cart.add({
      variantId: String(product.id),
      name: product.name,
      qty: 1,
      priceCents: Math.round(product.price * 100),
    });
  }

  // Calculate totals
  const subtotal = cart.lines.reduce((sum, line) => sum + line.priceCents * line.qty, 0);
  const tax = Math.round(subtotal * 0.08); // 8% tax
  const total = subtotal + tax;

  // Handle payment
  async function handlePayment(method: string, amountCents: number) {
    const token = localStorage.getItem('vendly_token');
    
    if (!token) {
      alert('You must be logged in to complete a sale');
      return;
    }
    
    // Create or find customer if details provided
    let finalCustomerId = customerId;
    if (!finalCustomerId && (customerName || customerPhone || customerEmail)) {
      try {
        const customerRes = await fetch(`${API_URL}/api/v1/customers`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: customerName || 'Guest',
            phone: customerPhone || null,
            email: customerEmail || null,
          }),
        });
        if (customerRes.ok) {
          const customerData = await customerRes.json();
          finalCustomerId = customerData.id;
        } else {
          console.error('Customer creation failed:', customerRes.status, await customerRes.text());
        }
      } catch (e) {
        console.error('Failed to create customer:', e);
      }
    }

    // Build sale payload
    const salePayload = {
      items: cart.lines.map((line) => ({
        product_id: parseInt(line.variantId),
        quantity: line.qty,
        unit_price: line.priceCents / 100,
        discount: 0,
      })),
      payment_method: method,
      payment_reference: method === 'card' ? `CARD-${Date.now()}` : null,
      discount: 0,
      notes: null,
      customer_id: finalCustomerId,
    };
    
    const response = await fetch(`${API_URL}/api/v1/sales`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(salePayload),
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to create sale');
    }
    
    const sale = await response.json();
    setLastSaleId(sale.id);
    setLastSale(sale);
    cart.clear();
    setPayOpen(false);
    setShowReceiptPrompt(true);
    // Reset customer info
    setCustomerName('');
    setCustomerPhone('');
    setCustomerEmail('');
    setCustomerId(null);
  }

  // Open customer modal before payment
  function openCustomerModal() {
    setShowCustomerModal(true);
  }

  // Proceed to payment after customer info
  function proceedToPayment() {
    setShowCustomerModal(false);
    setPayOpen(true);
  }

  // Print in-app receipt
  function printInAppReceipt() {
    if (!receiptRef.current) return;
    const printWindow = window.open('', '_blank', 'width=400,height=600');
    if (printWindow) {
      printWindow.document.write('<html><head><title>Receipt</title></head><body>');
      printWindow.document.write(receiptRef.current.innerHTML);
      printWindow.document.write('</body></html>');
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
    }
  }

  // Close receipt prompt
  function closeReceiptPrompt() {
    setShowReceiptPrompt(false);
    setLastSaleId(null);
  }

  return (
    <div className="flex h-[calc(100vh-100px)] gap-4">
      {/* Left: Product Search & Results */}
      <div className="flex-1 flex flex-col">
        {/* Search Bar */}
        <div className="mb-4 flex gap-2">
          <input
            className="input flex-1"
            placeholder="Search products by name or SKU..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-primary" onClick={loadProducts} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Product Grid */}
        <div className="flex-1 overflow-auto">
          {filteredProducts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {products.length === 0
                ? 'No products found. Add products in the Products page.'
                : 'No products match your search.'}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {filteredProducts.map((product) => (
                <button
                  key={product.id}
                  onClick={() => addToCart(product)}
                  className="card p-3 text-left hover:bg-blue-50 hover:border-blue-300 transition-colors"
                >
                  <div className="font-medium truncate">{product.name}</div>
                  <div className="text-sm text-gray-500">{product.sku || 'No SKU'}</div>
                  <div className="text-lg font-bold text-blue-600 mt-1">
                    ${product.price.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-400">Stock: {product.quantity}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Cart */}
      <div className="w-80 flex flex-col bg-white rounded-lg shadow-lg">
        <div className="p-4 border-b">
          <h2 className="text-lg font-bold">Cart</h2>
          <p className="text-sm text-gray-500">Cashier: {user?.full_name || user?.email}</p>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-auto p-4 space-y-2">
          {cart.lines.length === 0 ? (
            <div className="text-center py-8 text-gray-400">Cart is empty</div>
          ) : (
            cart.lines.map((line) => (
              <div
                key={line.variantId}
                className="flex items-center justify-between p-2 bg-gray-50 rounded"
              >
                <div className="flex-1">
                  <div className="font-medium text-sm">{line.name}</div>
                  <div className="text-xs text-gray-500">
                    ${(line.priceCents / 100).toFixed(2)} x {line.qty}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    className="w-6 h-6 rounded bg-gray-200 hover:bg-gray-300"
                    onClick={() => cart.dec(line.variantId)}
                  >
                    -
                  </button>
                  <span className="w-8 text-center">{line.qty}</span>
                  <button
                    className="w-6 h-6 rounded bg-gray-200 hover:bg-gray-300"
                    onClick={() => cart.inc(line.variantId)}
                  >
                    +
                  </button>
                  <button
                    className="w-6 h-6 rounded bg-red-100 hover:bg-red-200 text-red-600"
                    onClick={() => cart.remove(line.variantId)}
                  >
                    ×
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Totals */}
        <div className="p-4 border-t space-y-2">
          <div className="flex justify-between text-sm">
            <span>Subtotal</span>
            <span>${(subtotal / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Tax (8%)</span>
            <span>${(tax / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-lg font-bold">
            <span>Total</span>
            <span>${(total / 100).toFixed(2)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 border-t space-y-2">
          <button
            className="btn btn-success w-full"
            disabled={cart.lines.length === 0}
            onClick={openCustomerModal}
          >
            Pay ${(total / 100).toFixed(2)}
          </button>
          <button
            className="btn btn-secondary w-full"
            disabled={cart.lines.length === 0}
            onClick={() => cart.clear()}
          >
            Clear Cart
          </button>
        </div>
      </div>

      {/* Payment Modal */}
      <PaymentModal
        isOpen={payOpen}
        onClose={() => setPayOpen(false)}
        totalCents={total}
        onPay={handlePayment}
      />

      {/* Customer Details Modal */}
      {showCustomerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Customer Details</h2>
            <p className="text-gray-500 text-sm mb-4">Enter customer info (optional)</p>
            <div className="space-y-3 mb-4">
              <input
                type="text"
                className="input w-full"
                placeholder="Customer Name"
                value={customerName}
                onChange={e => setCustomerName(e.target.value)}
              />
              <input
                type="tel"
                className="input w-full"
                placeholder="Phone Number"
                value={customerPhone}
                onChange={e => setCustomerPhone(e.target.value)}
              />
              <input
                type="email"
                className="input w-full"
                placeholder="Email (optional)"
                value={customerEmail}
                onChange={e => setCustomerEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <button
                className="btn btn-success w-full"
                onClick={proceedToPayment}
              >
                Continue to Payment
              </button>
              <button
                className="btn btn-secondary w-full"
                onClick={() => { setShowCustomerModal(false); setPayOpen(true); }}
              >
                Skip (Guest Checkout)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Receipt Prompt Modal (in-app printable) */}
      {showReceiptPrompt && lastSale && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <div className="text-center mb-6">
              <div className="text-4xl mb-2">✅</div>
              <h2 className="text-xl font-semibold text-green-600">Payment Successful!</h2>
              <p className="text-gray-500 mt-2">Sale #{lastSaleId} completed</p>
            </div>
            <div className="mb-4 flex justify-center">
              <div ref={receiptRef}>
                <Receipt
                  saleId={lastSaleId!}
                  items={lastSale.items?.map((item: any) => ({
                    name: item.product_name || item.name,
                    price: Math.round(item.unit_price * 100),
                    quantity: item.quantity,
                  })) || []}
                  total={Math.round(lastSale.total * 100) || 0}
                  date={lastSale.created_at ? new Date(lastSale.created_at).toLocaleString() : new Date().toLocaleString()}
                  cashier={user?.full_name || user?.email}
                />
              </div>
            </div>
            <div className="space-y-3">
              <button
                onClick={printInAppReceipt}
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                🖨️ Print Receipt
              </button>
              <button
                onClick={closeReceiptPrompt}
                className="w-full py-2 text-gray-500 hover:text-gray-700"
              >
                Skip / New Sale
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function POSPage() {
  return (
    <ProtectedRoute>
      <POSContent />
    </ProtectedRoute>
  );
}
