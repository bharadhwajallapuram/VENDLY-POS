'use client';

// ===========================================
// Vendly POS - Products Page
// ===========================================

import { useState, useEffect, useCallback, useRef } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { BarcodeScanner, useBarcodeScanner } from '@/components/BarcodeScanner';
import { Products, ProductOut, ProductIn } from '@/lib/api';
import { API_URL } from '@/lib/api';

function ProductsContent() {
  const [items, setItems] = useState<ProductOut[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductOut | null>(null);
  const [scanFeedback, setScanFeedback] = useState<string | null>(null);
  const [formData, setFormData] = useState<ProductIn>({
    name: '',
    sku: '',
    barcode: '',
    description: '',
    price: 0,
    cost: 0,
    quantity: 0,
    min_quantity: 0,
    tax_rate: 0,
    is_active: true,
    image_url: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await Products.list(query));
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    load();
  }, [load]);

  // Use barcode scanner hook - fetch product from backend
  useBarcodeScanner(
    async (barcode: string) => {
      try {
        // Check if product with this barcode already exists locally
        const existingProduct = items.find(
          (p) => p.barcode?.toLowerCase() === barcode.toLowerCase() || 
                 p.sku?.toLowerCase() === barcode.toLowerCase()
        );
        
        if (existingProduct) {
          // Open edit modal for existing product
          openEditModal(existingProduct);
          setScanFeedback(`✓ Found: ${existingProduct.name}`);
        } else {
          // Check backend to ensure barcode doesn't exist
          const token = localStorage.getItem('vendly_token');
          const response = await fetch(`${API_URL}/api/v1/products?query=${encodeURIComponent(barcode)}&limit=5`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });
          
          if (response.ok) {
            const data = await response.json();
            const backendItems = Array.isArray(data) ? data : (data.items || []);
            const backendProduct = backendItems.find((p: any) =>
              p.barcode?.toLowerCase() === barcode.toLowerCase()
            );
            
            if (backendProduct) {
              // Product exists in backend - open edit modal
              openEditModal(backendProduct);
              setScanFeedback(`✓ Found: ${backendProduct.name}`);
              return;
            }
          }
          
          // Barcode doesn't exist - Open add modal with barcode pre-filled
          setEditingProduct(null);
          setFormData({
            name: '',
            sku: '',
            barcode: barcode,
            description: '',
            price: 0,
            cost: 0,
            quantity: 0,
            min_quantity: 0,
            tax_rate: 8,
            is_active: true,
            image_url: '',
          });
          setShowModal(true);
          setScanFeedback(`✓ Ready to create product with barcode: ${barcode}`);
        }
      } catch (err) {
        console.error('Error processing barcode:', err);
        setScanFeedback(`✗ Error processing barcode`);
      }
    },
    6,
    150,
    true,
    'Products-Page'
  );

  function openAddModal() {
    setEditingProduct(null);
    setFormData({
      name: '',
      sku: '',
      barcode: '',
      description: '',
      price: 0,
      cost: 0,
      quantity: 0,
      min_quantity: 0,
      tax_rate: 8,
      is_active: true,
      image_url: '',
    });
    setShowModal(true);
  }

  function openEditModal(product: ProductOut) {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      sku: product.sku || '',
      barcode: product.barcode || '',
      description: product.description || '',
      price: product.price,
      cost: product.cost || 0,
      quantity: product.quantity,
      min_quantity: product.min_quantity,
      tax_rate: product.tax_rate,
      is_active: product.is_active,
      image_url: product.image_url || '',
    });
    setShowModal(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editingProduct) {
        const updated = await Products.update(editingProduct.id, formData);
        setItems(items.map((p) => (p.id === updated.id ? updated : p)));
      } else {
        const created = await Products.create(formData);
        setItems([created, ...items]);
      }
      setShowModal(false);
    } catch (err: any) {
      const errorMessage = err?.message || String(err);
      
      // Check for session expired errors
      if (errorMessage.includes('Session expired') || errorMessage.includes('401')) {
        alert('Your session has expired. Please log in again.');
        // Optionally redirect to login
        window.location.href = '/login';
      } else {
        alert('Failed to save product: ' + errorMessage);
      }
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this product?')) return;
    await Products.del(id);
    setItems(items.filter((x) => x.id !== id));
  }

  return (
    <div className="space-y-6">
      {/* Barcode Scanner */}
      <BarcodeScanner 
        onBarcodeScanned={(barcode) => {
          // Check if product with this barcode already exists
          const existingProduct = items.find(
            (p) => p.barcode?.toLowerCase() === barcode.toLowerCase() || 
                   p.sku?.toLowerCase() === barcode.toLowerCase()
          );
          
          if (existingProduct) {
            openEditModal(existingProduct);
            setScanFeedback(`✓ Found: ${existingProduct.name}`);
          } else {
            setEditingProduct(null);
            setFormData({
              name: '',
              sku: '',
              barcode: barcode,
              description: '',
              price: 0,
              cost: 0,
              quantity: 0,
              min_quantity: 0,
              tax_rate: 8,
              is_active: true,
              image_url: '',
            });
            setShowModal(true);
            setScanFeedback(`✓ Ready to create product with barcode: ${barcode}`);
          }
        }}
        feedback={scanFeedback}
        onFeedbackDismiss={() => setScanFeedback(null)}
      />

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Products</h1>
        <button className="btn btn-success" onClick={openAddModal}>
          + Add Product
        </button>
      </div>

      <div className="flex gap-2">
        <input
          className="input flex-1"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products..."
          onKeyDown={(e) => e.key === 'Enter' && load()}
        />
        <button className="btn btn-primary" onClick={load} disabled={loading}>
          {loading ? 'Loading...' : 'Search'}
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="p-4 text-left font-semibold">Image</th>
              <th className="p-4 text-left font-semibold">Name</th>
              <th className="p-4 text-left font-semibold">SKU</th>
              <th className="p-4 text-left font-semibold">Stock</th>
              <th className="p-4 text-left font-semibold">Price</th>
              <th className="p-4 text-left font-semibold">Status</th>
              <th className="p-4 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-8 text-center text-gray-500">
                  No products found
                </td>
              </tr>
            ) : (
              items.map((p) => (
                <tr key={p.id} className="border-b hover:bg-gray-50">
                  <td className="p-4">
                    {p.image_url ? (
                      <img 
                        src={p.image_url} 
                        alt={p.name}
                        className="w-12 h-12 object-cover rounded-lg bg-gray-100"
                        onError={(e) => {
                          // Hide broken image and show fallback
                          (e.target as HTMLImageElement).style.display = 'none';
                          const fallback = (e.target as HTMLImageElement).nextElementSibling;
                          if (fallback) (fallback as HTMLElement).style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div 
                      className={`w-12 h-12 bg-gray-200 rounded-lg items-center justify-center text-gray-500 text-lg ${p.image_url ? 'hidden' : 'flex'}`}
                      title={p.name}
                    >
                      {p.name.charAt(0).toUpperCase()}
                    </div>
                  </td>
                  <td className="p-4 font-medium">{p.name}</td>
                  <td className="p-4 text-gray-600">{p.sku || '—'}</td>
                  <td className="p-4 text-gray-600">{p.quantity}</td>
                  <td className="p-4">${p.price.toFixed(2)}</td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        p.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {p.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <button
                      className="btn btn-secondary text-sm mr-2"
                      onClick={() => openEditModal(p)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-danger text-sm"
                      onClick={() => handleDelete(p.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Product Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold">
                {editingProduct ? 'Edit Product' : 'Add New Product'}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Product Name *</label>
                <input
                  type="text"
                  className="input w-full"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="Enter product name"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">SKU</label>
                  <input
                    type="text"
                    className="input w-full"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    placeholder="e.g., SKU-001"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Barcode</label>
                  <input
                    type="text"
                    className="input w-full"
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    placeholder="e.g., 123456789"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  className="input w-full"
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Product description..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Price * {formData.price <= 0 && <span className="text-red-500 text-xs">(must be greater than 0)</span>}</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="input w-full"
                    value={formData.price || ''}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value ? parseFloat(e.target.value) : 0 })}
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Cost</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    className="input w-full"
                    value={formData.cost || ''}
                    onChange={(e) => setFormData({ ...formData, cost: e.target.value ? parseFloat(e.target.value) : 0 })}
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Quantity in Stock</label>
                  <input
                    type="number"
                    min="0"
                    className="input w-full"
                    value={formData.quantity || ''}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value ? parseInt(e.target.value) : 0 })}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Minimum Stock</label>
                  <input
                    type="number"
                    min="0"
                    className="input w-full"
                    value={formData.min_quantity || ''}
                    onChange={(e) => setFormData({ ...formData, min_quantity: e.target.value ? parseInt(e.target.value) : 0 })}
                    placeholder="0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Image URL</label>
                <input
                  type="url"
                  className="input w-full"
                  value={formData.image_url || ''}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  placeholder="https://example.com/image.jpg"
                />
                {formData.image_url && (
                  <div className="mt-2">
                    <img 
                      src={formData.image_url} 
                      alt="Preview" 
                      className="w-20 h-20 object-cover rounded-lg border"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Tax Rate (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    className="input w-full"
                    value={formData.tax_rate}
                    onChange={(e) => setFormData({ ...formData, tax_rate: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="flex items-center pt-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium">Active (visible in POS)</span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-success disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={formData.price <= 0}
                  title={formData.price <= 0 ? 'Price must be greater than 0' : ''}
                >
                  {editingProduct ? 'Save Changes' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ProductsPage() {
  return (
    <ProtectedRoute roles={['manager', 'admin']}>
      <ProductsContent />
    </ProtectedRoute>
  );
}
