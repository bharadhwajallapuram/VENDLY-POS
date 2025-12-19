'use client';

// ===========================================
// Vendly POS - Point of Sale Page
// ===========================================

import { useEffect, useState, useCallback, useRef } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import PaymentModal from '@/components/PaymentModal';
import { SplitPayment } from '@/components/SplitPaymentInput';
import Receipt from '@/components/Receipt';
import OfflineIndicator, { OfflineBanner } from '@/components/OfflineIndicator';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import { useCart } from '@/store/cart';
import { useAuth } from '@/store/auth';
import { API_URL } from '@/lib/api';
import { useOffline } from '@/lib/useOffline';
import { toastManager } from '@/components/Toast';
import { useInventorySync } from '@/hooks/useInventorySync';

// Simple product type for now
interface SimpleProduct {
  id: number;
  name: string;
  price: number;
  sku?: string;
  quantity: number;
  image_url?: string;
  category_id?: number;
}

// Category type
interface Category {
  id: number;
  name: string;
  description?: string;
}

// Category icons mapping
function getCategoryIcon(categoryName: string): string {
  const name = categoryName.toLowerCase();
  if (name.includes('beverage') || name.includes('drink')) return '🥤';
  if (name.includes('snack') || name.includes('cookie')) return '🍪';
  if (name.includes('dairy') || name.includes('milk')) return '🥛';
  if (name.includes('bakery') || name.includes('bread')) return '🥐';
  if (name.includes('electronic') || name.includes('tech')) return '📱';
  if (name.includes('grocery') || name.includes('groceries')) return '🛒';
  if (name.includes('personal') || name.includes('care')) return '🧴';
  if (name.includes('frozen') || name.includes('ice')) return '🧊';
  if (name.includes('home') || name.includes('kitchen')) return '🏠';
  if (name.includes('fruit') || name.includes('vegetable')) return '🍎';
  if (name.includes('meat') || name.includes('poultry')) return '🥩';
  if (name.includes('seafood') || name.includes('fish')) return '🐟';
  if (name.includes('candy') || name.includes('sweet')) return '🍬';
  if (name.includes('health') || name.includes('medicine')) return '💊';
  if (name.includes('pet')) return '🐾';
  if (name.includes('baby')) return '👶';
  if (name.includes('toy')) return '🧸';
  if (name.includes('cleaning') || name.includes('household')) return '🧹';
  return '📦'; // default
}

// Basic coupons in sync with backend
const COUPONS: Record<string, { type: 'percent' | 'amount'; value: number; max_off?: number; stackable: boolean }> = {
  SAVE10: { type: 'percent', value: 10, stackable: true },
  WELCOME15: { type: 'percent', value: 15, max_off: 25, stackable: false },
  FLAT5: { type: 'amount', value: 5, stackable: true },
};

function POSContent() {
  const receiptRef = useRef<HTMLDivElement>(null);
  const lastScanTimeRef = useRef<number>(0);
  const cart = useCart();
  const { user } = useAuth();
  const { isOnline, pendingCount, queueOfflineSale, syncNow, isSyncing } = useOffline();
  
  const [query, setQuery] = useState('');
  const [scanFeedback, setScanFeedback] = useState<string | null>(null);
  const [isOfflineSale, setIsOfflineSale] = useState(false);
  const [products, setProducts] = useState<SimpleProduct[]>([]);
  const [scannedProduct, setScannedProduct] = useState<SimpleProduct | null>(null);
  const [showScannedProductModal, setShowScannedProductModal] = useState(false);
  const [payOpen, setPayOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastSaleId, setLastSaleId] = useState<number | null>(null);
  const [showReceiptPrompt, setShowReceiptPrompt] = useState(false);
  const [lastSale, setLastSale] = useState<any>(null);
  const [orderDiscount, setOrderDiscount] = useState(0); // dollars
  const [couponCode, setCouponCode] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState<string | null>(null);
  const [couponDiscountCents, setCouponDiscountCents] = useState(0);
  const [couponMessage, setCouponMessage] = useState<string | null>(null);
  
  // Pagination state for large product catalogs
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [totalProducts, setTotalProducts] = useState(0);
  const PRODUCTS_PER_PAGE = 50;
  
  // Category state
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);

  // Customer details state
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerId, setCustomerId] = useState<number | null>(null);

  // Loyalty points (1 point = $0.01, 100 points = $1)
  const [customerLoyaltyPoints, setCustomerLoyaltyPoints] = useState(0);
  const [redeemingPoints, setRedeemingPoints] = useState(0);
  const [showLoyaltyRedeem, setShowLoyaltyRedeem] = useState(false);
  const loyaltyDiscountCents = Math.min(redeemingPoints, customerLoyaltyPoints); // 1 point = 1 cent

  // Load only categories on mount - products load when segment is selected
  useEffect(() => {
    loadCategories();
  }, []);

  // Listen for inventory updates via WebSocket
  useInventorySync({
    endpoint: 'inventory',
    onInventoryUpdate: (data) => {
      // Update product stock in real-time - force complete array update
      setProducts((prev) => {
        const updated = prev.map((p) =>
          p.id === data.product_id 
            ? { ...p, quantity: data.new_qty } 
            : p
        );
        // Create new array reference to force re-render
        return [...updated];
      });
      
      // Update cart stock limits if product is in cart
      const variantId = String(data.product_id);
      cart.updateStock(variantId, data.new_qty);
      
      console.log(`📦 Stock updated: Product ${data.product_id} → ${data.new_qty} units`);
    },
    onLowStock: (data) => {
      setProducts((prev) => [...prev.map((p) =>
        p.id === data.product_id ? { ...p, quantity: data.new_qty } : p
      )]);
      
      cart.updateStock(String(data.product_id), data.new_qty);
    },
    onOutOfStock: (data) => {
      setProducts((prev) => [...prev.map((p) =>
        p.id === data.product_id ? { ...p, quantity: 0 } : p
      )]);
      
      cart.updateStock(String(data.product_id), 0);
      console.log(`🔴 Out of stock: Product ${data.product_id}`);
    },
  });

  // Load categories on mount
  async function loadCategories() {
    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/categories`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setCategories(data.items || data || []);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  async function loadProducts(page = 0, searchQuery = '', categoryId: number | null = selectedCategory) {
    setLoading(true);
    try {
      const token = localStorage.getItem('vendly_token');
      const skip = page * PRODUCTS_PER_PAGE;
      const queryParam = searchQuery ? `&q=${encodeURIComponent(searchQuery)}` : '';
      const categoryParam = categoryId ? `&category_id=${categoryId}` : '';
      const response = await fetch(
        `${API_URL}/api/v1/products?skip=${skip}&limit=${PRODUCTS_PER_PAGE}${queryParam}${categoryParam}`, 
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      if (response.ok) {
        const data = await response.json();
        const items = data.items || data || [];
        
        if (page === 0) {
          // First page - replace products
          setProducts(items);
        } else {
          // Subsequent pages - append
          setProducts(prev => [...prev, ...items]);
        }
        
        // Check if there are more products
        setHasMore(items.length === PRODUCTS_PER_PAGE);
        setCurrentPage(page);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  }
  
  // Load more products when scrolling
  function loadMoreProducts() {
    if (!loading && hasMore) {
      loadProducts(currentPage + 1, query, selectedCategory);
    }
  }
  
  // Handle category/segment selection
  function handleCategorySelect(categoryId: number | null) {
    setSelectedCategory(categoryId);
    setCurrentPage(0);
    setProducts([]);
    setQuery(''); // Reset search when changing segments
    // Only load products if a category is selected
    if (categoryId !== null) {
      loadProducts(0, '', categoryId);
    }
  }

  // Go back to segment view
  function handleBackToSegments() {
    setSelectedCategory(null);
    setProducts([]);
    setQuery('');
    setCurrentPage(0);
  }
  
  // Search products with debounce - use server-side search for large catalogs
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  function handleSearch(searchQuery: string) {
    setQuery(searchQuery);
    
    // Debounce search to avoid too many API calls
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      setCurrentPage(0);
      loadProducts(0, searchQuery, selectedCategory);
    }, 300); // 300ms debounce
  }
  
  // For small catalogs, also filter client-side for instant feedback
  // For large catalogs (>100), rely on server-side search
  const filteredProducts = products.length <= 100 
    ? products.filter(
        (p) =>
          p.name.toLowerCase().includes(query.toLowerCase()) ||
          p.sku?.toLowerCase().includes(query.toLowerCase())
      )
    : products; // Server already filtered

  // Handle barcode scan - fetch product from backend
  const handleBarcodeScanned = useCallback(async (barcode: string) => {
    // Prevent duplicate scans within 500ms
    const now = Date.now();
    if (now - lastScanTimeRef.current < 500) {
      return;
    }
    lastScanTimeRef.current = now;

    try {
      const token = localStorage.getItem('vendly_token');
      
      // Check if token exists
      if (!token) {
        setScanFeedback(`✗ Session expired. Please log in again.`);
        return;
      }
      
      console.log('📱 Scanning barcode:', barcode);
      
      // Search for product by barcode or SKU
      const response = await fetch(`${API_URL}/api/v1/products?query=${encodeURIComponent(barcode)}&limit=10`, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
      });
      
      if (response.status === 401) {
        // Token invalid - clear it and show error
        localStorage.removeItem('vendly_token');
        setScanFeedback(`✗ Session expired. Please log in again.`);
        return;
      }
      
      if (!response.ok) {
        console.error('Backend error:', response.status, response.statusText);
        setScanFeedback(`✗ Error fetching product. Try again.`);
        return;
      }
      
      const data = await response.json();
      console.log('📦 Backend response:', data);
      const items = Array.isArray(data) ? data : (data.items || []);
      
      console.log('🔍 All matching items:', items.map((p: any) => ({ id: p.id, name: p.name, barcode: p.barcode, sku: p.sku })));
      
      // IMPORTANT: Only accept products with EXACT barcode or SKU match
      // This prevents partial matches from the backend search
      let product = items.find((p: any) => 
        (p.barcode && p.barcode.toLowerCase() === barcode.toLowerCase()) ||
        (p.sku && p.sku.toLowerCase() === barcode.toLowerCase())
      );
      
      console.log('🎯 Exact match found:', product ? { id: product.id, name: product.name, barcode: product.barcode, sku: product.sku } : 'None');
      
      if (product) {
        // Automatically add product to cart
        console.log('✅ Adding to cart:', product.name);
        cart.add({
          variantId: String(product.id),
          name: product.name,
          qty: 1,
          priceCents: Math.round(product.price * 100),
        });
        // No feedback for successful additions
        setScanFeedback(null);
      } else {
        // Product not found - show message with error styling
        console.log('❌ No exact barcode match found');
        setScanFeedback(`✗ Product not found`);
      }
    } catch (err) {
      console.error('Error scanning barcode:', err);
      setScanFeedback(`✗ Error processing barcode`);
    }
  }, [cart]);

  // Add product to cart
  function addToCart(product: SimpleProduct) {
    // Check if product has available stock
    if (product.quantity <= 0) {
      toastManager.error(`${product.name} is out of stock`);
      return;
    }

    const success = cart.add({
      variantId: String(product.id),
      name: product.name,
      qty: 1,
      priceCents: Math.round(product.price * 100),
      availableStock: product.quantity,
    });

    if (!success) {
      toastManager.warning(`Cannot add more. Only ${product.quantity} units available.`);
    }
  }

  // Calculate totals
  const subtotal = cart.lines.reduce((sum, line) => sum + line.priceCents * line.qty, 0);
  const tax = Math.round(subtotal * 0.08); // 8% tax
  const orderDiscountCents = Math.max(0, Math.round(orderDiscount * 100));
  const totalDiscountCents = Math.min(orderDiscountCents + couponDiscountCents + loyaltyDiscountCents, subtotal + tax);
  const total = Math.max(0, subtotal + tax - totalDiscountCents);

  // Check if applied coupon is non-stackable
  const isNonStackableCouponApplied = appliedCoupon ? !COUPONS[appliedCoupon]?.stackable : false;

  const calculateCouponDiscount = useCallback((code: string, baseCents: number) => {
    const coupon = COUPONS[code];
    if (!coupon) return 0;
    if (coupon.type === 'percent') {
      const raw = (baseCents * coupon.value) / 100;
      const capped = coupon.max_off ? Math.min(raw, Math.round(coupon.max_off * 100)) : raw;
      return Math.round(capped);
    }
    return Math.round(coupon.value * 100);
  }, []);

  function applyCoupon() {
    const code = couponCode.trim().toUpperCase();
    if (!code) {
      setAppliedCoupon(null);
      setCouponDiscountCents(0);
      setCouponMessage('');
      return;
    }
    
    const coupon = COUPONS[code];
    if (!coupon) {
      setAppliedCoupon(null);
      setCouponDiscountCents(0);
      setCouponMessage('Invalid coupon');
      return;
    }

    // Check if applying non-stackable coupon while loyalty points are being used
    if (!coupon.stackable && loyaltyDiscountCents > 0) {
      setCouponMessage('This coupon cannot be combined with loyalty points');
      return;
    }

    const discount = calculateCouponDiscount(code, subtotal);
    if (discount === 0) {
      setAppliedCoupon(null);
      setCouponDiscountCents(0);
      setCouponMessage('Invalid coupon');
      return;
    }
    
    // If non-stackable, clear loyalty points
    if (!coupon.stackable) {
      setRedeemingPoints(0);
    }
    
    setAppliedCoupon(code);
    setCouponDiscountCents(discount);
    setCouponMessage(`Applied ${code}${!coupon.stackable ? ' (exclusive)' : ''}`);
  }

  function applyLoyaltyPoints(points: number) {
    if (isNonStackableCouponApplied) {
      alert('Cannot use loyalty points with this coupon');
      return;
    }
    setRedeemingPoints(Math.min(points, customerLoyaltyPoints, subtotal + tax));
    setShowLoyaltyRedeem(false);
  }

  // Re-evaluate coupon when cart subtotal changes
  useEffect(() => {
    if (appliedCoupon) {
      setCouponDiscountCents(calculateCouponDiscount(appliedCoupon, subtotal));
    }
  }, [appliedCoupon, subtotal, calculateCouponDiscount]);

  // Handle payment (supports offline mode)
  async function handlePayment(payments: SplitPayment[]) {
    try {
      const token = localStorage.getItem('vendly_token');
      if (!token) {
        alert('You must be logged in to complete a sale');
        return;
      }

      // Build sale items
      const saleItems = cart.lines.map((line) => ({
        product_id: parseInt(line.variantId),
        quantity: line.qty,
        unit_price: line.priceCents / 100,
        discount: 0,
      }));

    // Check if we're offline
    if (!isOnline) {
      try {
        // Queue the sale for later sync
        const offlineSale = queueOfflineSale({
          items: saleItems,
          payments: payments.map(p => ({ method: p.method, amount: p.amount / 100 })),
          discount: orderDiscountCents / 100,
          coupon_code: appliedCoupon || undefined,
          notes: undefined,
          customer_id: customerId || undefined,
          customer_name: customerName || undefined,
          customer_phone: customerPhone || undefined,
          customer_email: customerEmail || undefined,
        });

        // Create a local sale object for receipt display
        const localSale = {
          id: offlineSale.id,
          items: cart.lines.map((line) => ({
            product_name: line.name,
            quantity: line.qty,
            unit_price: line.priceCents / 100,
          })),
          subtotal: subtotal / 100,
          tax: tax / 100,
          discount: totalDiscountCents / 100,
          coupon_code: appliedCoupon,
          total: total / 100,
          created_at: offlineSale.created_at,
          is_offline: true,
        };

        setLastSaleId(null);
        setLastSale(localSale);
        setIsOfflineSale(true);
        cart.clear();
        setPayOpen(false);
        setShowReceiptPrompt(true);
        
        // Reset customer info
        setCustomerName('');
        setCustomerPhone('');
        setCustomerEmail('');
        setCustomerId(null);
        setCustomerLoyaltyPoints(0);
        setRedeemingPoints(0);
        setCouponCode('');
        setAppliedCoupon(null);
        setCouponDiscountCents(0);
        setOrderDiscount(0);
        return;
      } catch (err) {
        console.error('Error queueing offline sale:', err);
        alert('Failed to queue sale offline. Please try again.');
        return;
      }
    }

    // Online mode - proceed with normal API call
    try {
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
        items: saleItems,
        payments,
        discount: orderDiscountCents / 100,
        coupon_code: appliedCoupon || undefined,
        notes: null,
        customer_id: finalCustomerId,
      };

      console.log('[POS] Attempting to create sale online:', salePayload);

      const response = await fetch(`${API_URL}/api/v1/sales`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(salePayload),
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error(`[POS] Sale creation failed with status ${response.status}:`, errText);
        throw new Error(`HTTP ${response.status}: ${errText}`);
      }

      const saleData = await response.json();
      console.log('[POS] Sale created successfully:', saleData);

      setLastSaleId(saleData.id);
      setLastSale(saleData);
      setIsOfflineSale(false);

      // Clear cart and show receipt
      cart.clear();
      setPayOpen(false);
      setShowReceiptPrompt(true);

      // Reset customer info
      setCustomerName('');
      setCustomerPhone('');
      setCustomerEmail('');
      setCustomerId(null);
      setCustomerLoyaltyPoints(0);
      setRedeemingPoints(0);
      setCouponCode('');
      setAppliedCoupon(null);
      setCouponDiscountCents(0);
      setOrderDiscount(0);
    } catch (error) {
      // ANY error - queue as offline sale
      console.warn('[POS] Online sale failed, queuing offline:', error);
      
      try {
        const offlineSale = queueOfflineSale({
          items: saleItems,
          payments: payments.map(p => ({ method: p.method, amount: p.amount / 100 })),
          discount: orderDiscountCents / 100,
          coupon_code: appliedCoupon || undefined,
          notes: undefined,
          customer_id: customerId || undefined,
          customer_name: customerName || undefined,
          customer_phone: customerPhone || undefined,
          customer_email: customerEmail || undefined,
        });

        const localSale = {
          id: offlineSale.id,
          items: cart.lines.map((line) => ({
            product_name: line.name,
            quantity: line.qty,
            unit_price: line.priceCents / 100,
          })),
          subtotal: subtotal / 100,
          tax: tax / 100,
          discount: totalDiscountCents / 100,
          coupon_code: appliedCoupon,
          total: total / 100,
          created_at: offlineSale.created_at,
          is_offline: true,
        };

        setLastSaleId(null);
        setLastSale(localSale);
        setIsOfflineSale(true);

        // Clear cart and show receipt
        cart.clear();
        setPayOpen(false);
        setShowReceiptPrompt(true);

        // Reset customer info
        setCustomerName('');
        setCustomerPhone('');
        setCustomerEmail('');
        setCustomerId(null);
        setCustomerLoyaltyPoints(0);
        setRedeemingPoints(0);
        setCouponCode('');
        setAppliedCoupon(null);
        setCouponDiscountCents(0);
        setOrderDiscount(0);

        // Show user-friendly message
        toastManager.warning('Sale queued offline. Will sync when connection is restored.');
      } catch (queueErr) {
        console.error('[POS] Failed to queue offline sale:', queueErr);
        alert('Failed to process sale. Please check your connection and try again.');
      }
    }
    } catch (err) {
      console.error('[POS] Unexpected error in handlePayment:', err);
      alert('An unexpected error occurred. Please try again.');
    }
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
    setIsOfflineSale(false);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] overflow-hidden">
      {/* Offline Banner */}
      <OfflineBanner />

      {/* Barcode Scanner */}
      <BarcodeScanner 
        onBarcodeScanned={handleBarcodeScanned}
        feedback={scanFeedback}
        onFeedbackDismiss={() => setScanFeedback(null)}
        debounceMs={300}
      />

      <div className="flex flex-col lg:flex-row flex-1 gap-4 overflow-hidden">
        {/* Left: Product Search & Results - This area scrolls */}
        <div className="flex-1 flex flex-col min-h-0 overflow-auto">
          {/* Search Bar - Only show when viewing products in a segment */}
          {selectedCategory !== null && (
            <div className="mb-3 sm:mb-4 flex gap-2">
              <input
                className="input flex-1 text-sm sm:text-base py-2 sm:py-3"
                placeholder="Search products..."
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
              />
              <button className="btn btn-secondary text-sm sm:text-base px-3 sm:px-4" onClick={() => loadProducts(0, query, selectedCategory)} disabled={loading}>
                {loading ? '...' : 'Refresh'}
              </button>
            </div>
          )}
          
          {/* Segment/Category View */}
          {selectedCategory === null ? (
            /* Show Segment Tiles */
            <div className="pb-4">
              <div className="mb-3 sm:mb-4">
                <h2 className="text-lg sm:text-xl font-bold text-gray-800">Select a Segment</h2>
                <p className="text-xs sm:text-sm text-gray-500">Choose a category to view products</p>
              </div>
              {categories.length === 0 ? (
                <div className="text-center py-8 sm:py-12 text-gray-500">
                  <div className="text-4xl sm:text-5xl mb-3 sm:mb-4">📦</div>
                  <p className="text-sm sm:text-base">No segments found.</p>
                  <p className="text-xs sm:text-sm">Add categories in the admin panel.</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => handleCategorySelect(category.id)}
                      className="card p-4 sm:p-6 text-center hover:bg-blue-50 hover:border-blue-300 active:bg-blue-100 transition-all transform hover:scale-[1.02] active:scale-[0.98] touch-manipulation"
                    >
                      <div className="text-3xl sm:text-4xl md:text-5xl mb-2 sm:mb-3">
                        {getCategoryIcon(category.name)}
                      </div>
                      <div className="font-semibold text-sm sm:text-base md:text-lg text-gray-800 leading-tight">{category.name}</div>
                      {category.description && (
                        <div className="text-xs sm:text-sm text-gray-500 mt-1 truncate hidden sm:block">{category.description}</div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Show Products for Selected Segment */
            <>
              {/* Back Button and Segment Header */}
              <div className="mb-3 sm:mb-4 flex items-center gap-2 sm:gap-4 flex-wrap">
                <button
                  onClick={handleBackToSegments}
                  className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 bg-gray-100 hover:bg-gray-200 active:bg-gray-300 rounded-lg transition-colors text-sm sm:text-base touch-manipulation"
                >
                  <span>←</span>
                  <span className="hidden xs:inline">Back</span>
                </button>
                <div className="flex items-center gap-2">
                  <span className="text-xl sm:text-2xl">{getCategoryIcon(categories.find(c => c.id === selectedCategory)?.name || '')}</span>
                  <h2 className="text-base sm:text-xl font-bold text-gray-800">
                    {categories.find(c => c.id === selectedCategory)?.name || 'Products'}
                  </h2>
                </div>
              </div>
              
              {/* Product count */}
              <div className="mb-2 text-xs sm:text-sm text-gray-500">
                {products.length} products {hasMore && '(scroll for more)'}
              </div>

              {/* Product Grid */}
              <div className="pb-4">
                {loading && products.length === 0 ? (
                  <div className="text-center py-6 sm:py-8 text-gray-500">
                    <div className="animate-spin text-2xl sm:text-3xl mb-2">⏳</div>
                    <span className="text-sm sm:text-base">Loading products...</span>
                  </div>
                ) : filteredProducts.length === 0 ? (
                  <div className="text-center py-6 sm:py-8 text-gray-500">
                    <div className="text-3xl sm:text-4xl mb-2">📭</div>
                    <span className="text-sm sm:text-base">No products in this segment.</span>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
                    {filteredProducts.map((product) => (
                      <button
                        key={product.id}
                        onClick={() => addToCart(product)}
                        className="card p-2 sm:p-3 text-left hover:bg-gray-50 hover:border-gray-300 active:bg-gray-100 transition-colors touch-manipulation"
                      >
                        {/* Product Image with offline fallback */}
                        <div className="w-full h-16 sm:h-20 mb-2 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center">
                          {product.image_url ? (
                            <img 
                              src={product.image_url} 
                              alt={product.name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                                const fallback = (e.target as HTMLImageElement).nextElementSibling;
                                if (fallback) (fallback as HTMLElement).style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <div 
                            className={`w-full h-full bg-gradient-to-br from-blue-100 to-blue-200 items-center justify-center text-blue-600 text-xl sm:text-2xl font-bold ${product.image_url ? 'hidden' : 'flex'}`}
                          >
                            {product.name.charAt(0).toUpperCase()}
                          </div>
                        </div>
                        <div className="font-medium text-xs sm:text-sm truncate">{product.name}</div>
                        <div className="text-xs text-gray-500 truncate">{product.sku || 'No SKU'}</div>
                        <div className="text-sm sm:text-lg font-bold text-gray-900 mt-1">
                          ${product.price.toFixed(2)}
                        </div>
                        <div className="text-[10px] sm:text-xs text-gray-400">Stock: {product.quantity}</div>
                      </button>
                    ))}
                  </div>
                )}
                
                {/* Load More Button */}
                {hasMore && products.length > 0 && (
                  <div className="mt-4 text-center">
                    <button 
                      className="btn btn-secondary px-8"
                      onClick={loadMoreProducts}
                      disabled={loading}
                    >
                      {loading ? 'Loading...' : 'Load More Products'}
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
      </div>

      {/* Right: Cart - Fixed sidebar, doesn't scroll */}
      <div className="w-full lg:w-80 xl:w-96 flex flex-col bg-white rounded-lg shadow-lg flex-shrink-0 lg:h-full lg:overflow-hidden">
        <div className="p-3 sm:p-4 border-b flex-shrink-0">
          <h2 className="text-base sm:text-lg font-bold">Cart</h2>
          <p className="text-xs sm:text-sm text-gray-500 truncate">Cashier: {user?.full_name || user?.email}</p>
        </div>

        {/* Cart Items - Only this section scrolls within the cart */}
        <div className="flex-1 overflow-auto p-3 sm:p-4 space-y-2 min-h-0">
          {cart.lines.length === 0 ? (
            <div className="text-center py-8 text-gray-400">Cart is empty</div>
          ) : (
            cart.lines.map((line) => (
              <div
                key={line.variantId}
                className="flex items-center justify-between p-2 bg-gray-50 rounded"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-xs sm:text-sm truncate">{line.name}</div>
                  <div className="text-[10px] sm:text-xs text-gray-500">
                    ${(line.priceCents / 100).toFixed(2)} x {line.qty}
                  </div>
                </div>
                <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                  <button
                    className="w-7 h-7 sm:w-6 sm:h-6 rounded bg-gray-200 hover:bg-gray-300 active:bg-gray-400 touch-manipulation text-sm sm:text-base"
                    onClick={() => cart.dec(line.variantId)}
                  >
                    -
                  </button>
                  <span className="w-6 sm:w-8 text-center text-sm">{line.qty}</span>
                  <button
                    className="w-7 h-7 sm:w-6 sm:h-6 rounded bg-gray-200 hover:bg-gray-300 active:bg-gray-400 touch-manipulation text-sm sm:text-base"
                    onClick={() => {
                      const success = cart.inc(line.variantId);
                      if (!success) {
                        const maxStock = line.availableStock || '?';
                        toastManager.warning(`Only ${maxStock} units available in stock.`);
                      }
                    }}
                  >
                    +
                  </button>
                  <button
                    className="w-7 h-7 sm:w-6 sm:h-6 rounded bg-red-100 hover:bg-red-200 active:bg-red-300 text-red-600 touch-manipulation text-sm sm:text-base"
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
        <div className="p-3 sm:p-4 border-t space-y-1 sm:space-y-2 flex-shrink-0">
          <div className="flex justify-between text-xs sm:text-sm">
            <span>Subtotal</span>
            <span>${(subtotal / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-xs sm:text-sm">
            <span>Tax (8%)</span>
            <span>${(tax / 100).toFixed(2)}</span>
          </div>
          {couponDiscountCents > 0 && (
            <div className="flex justify-between text-xs sm:text-sm text-green-700">
              <span>Coupon {appliedCoupon && <span className="text-[10px] sm:text-xs">({appliedCoupon})</span>}</span>
              <span>- ${(couponDiscountCents / 100).toFixed(2)}</span>
            </div>
          )}
          {loyaltyDiscountCents > 0 && (
            <div className="flex justify-between text-xs sm:text-sm text-purple-700">
              <span>Loyalty <span className="text-[10px] sm:text-xs">({redeemingPoints} pts)</span></span>
              <span>- ${(loyaltyDiscountCents / 100).toFixed(2)}</span>
            </div>
          )}
          <div className="flex justify-between text-base sm:text-lg font-bold border-t pt-2">
            <span>Total</span>
            <span>${(total / 100).toFixed(2)}</span>
          </div>
        </div>

        {/* Coupon Input */}
        <div className="px-3 sm:px-4 pb-2 flex-shrink-0">
          {!appliedCoupon ? (
            <div className="flex gap-2">
              <input
                type="text"
                className="input flex-1 text-xs sm:text-sm py-1.5 sm:py-2"
                placeholder="Coupon code"
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && applyCoupon()}
              />
              <button 
                className="px-2 sm:px-3 py-1.5 bg-emerald-600 text-white text-xs sm:text-sm rounded-lg hover:bg-emerald-700 active:bg-emerald-800 transition-colors touch-manipulation"
                onClick={applyCoupon}
              >
                Apply
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between bg-emerald-50 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2">
              <div className="flex items-center gap-1 sm:gap-2">
                <svg className="w-3 h-3 sm:w-4 sm:h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span className="text-xs sm:text-sm font-medium text-emerald-700">{appliedCoupon}</span>
                <span className="text-[10px] sm:text-xs text-emerald-600">(-${(couponDiscountCents / 100).toFixed(2)})</span>
              </div>
              <button 
                className="text-emerald-600 hover:text-emerald-800 text-xs sm:text-sm touch-manipulation"
                onClick={() => { setAppliedCoupon(null); setCouponDiscountCents(0); setCouponCode(''); }}
              >
                Remove
              </button>
            </div>
          )}
          {couponMessage && !appliedCoupon && (
            <p className="text-[10px] sm:text-xs text-red-500 mt-1">{couponMessage}</p>
          )}
        </div>

        {/* Loyalty Points */}
        {customerId && customerLoyaltyPoints > 0 && (
          <div className="px-4 pb-2">
            {redeemingPoints === 0 ? (
              <button
                onClick={() => setShowLoyaltyRedeem(true)}
                disabled={isNonStackableCouponApplied}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                  isNonStackableCouponApplied 
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                    : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                }`}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{customerLoyaltyPoints} loyalty points available</span>
                </div>
                <span className="font-medium">Redeem</span>
              </button>
            ) : (
              <div className="flex items-center justify-between bg-purple-50 rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm font-medium text-purple-700">{redeemingPoints} points</span>
                  <span className="text-xs text-purple-600">(-${(loyaltyDiscountCents / 100).toFixed(2)})</span>
                </div>
                <button 
                  className="text-purple-600 hover:text-purple-800 text-sm"
                  onClick={() => setRedeemingPoints(0)}
                >
                  Remove
                </button>
              </div>
            )}
            {isNonStackableCouponApplied && redeemingPoints === 0 && (
              <p className="text-xs text-gray-500 mt-1">Cannot combine with current coupon</p>
            )}
          </div>
        )}

        {/* Loyalty Points Redemption Modal */}
        {showLoyaltyRedeem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-xs p-5">
              <h3 className="text-lg font-semibold mb-2">Redeem Loyalty Points</h3>
              <p className="text-sm text-gray-500 mb-4">
                Available: <span className="font-medium text-purple-600">{customerLoyaltyPoints} points</span> 
                <span className="text-xs"> (${(customerLoyaltyPoints / 100).toFixed(2)} value)</span>
              </p>
              <div className="space-y-3 mb-4">
                <button
                  onClick={() => applyLoyaltyPoints(customerLoyaltyPoints)}
                  className="w-full py-2 px-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Use All ({customerLoyaltyPoints} pts = ${(Math.min(customerLoyaltyPoints, subtotal + tax) / 100).toFixed(2)})
                </button>
                <button
                  onClick={() => applyLoyaltyPoints(Math.min(500, customerLoyaltyPoints))}
                  disabled={customerLoyaltyPoints < 100}
                  className="w-full py-2 px-4 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors disabled:opacity-50"
                >
                  Use 500 pts ($5.00)
                </button>
                <button
                  onClick={() => applyLoyaltyPoints(Math.min(100, customerLoyaltyPoints))}
                  disabled={customerLoyaltyPoints < 100}
                  className="w-full py-2 px-4 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors disabled:opacity-50"
                >
                  Use 100 pts ($1.00)
                </button>
              </div>
              <button
                onClick={() => setShowLoyaltyRedeem(false)}
                className="w-full py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="p-3 sm:p-4 border-t space-y-2 flex-shrink-0">
          <button
            className="btn btn-success w-full py-2.5 sm:py-3 text-sm sm:text-base touch-manipulation"
            disabled={cart.lines.length === 0}
            onClick={openCustomerModal}
          >
            Pay ${(total / 100).toFixed(2)}
          </button>
          <button
            className="btn btn-secondary w-full py-2 sm:py-2.5 text-sm sm:text-base touch-manipulation"
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
            <p className="text-gray-500 text-sm mb-4">Enter customer info to earn & redeem loyalty points</p>
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
                placeholder="Phone Number (for loyalty lookup)"
                value={customerPhone}
                onChange={e => {
                  setCustomerPhone(e.target.value);
                  // Simulate loyalty points lookup by phone
                  if (e.target.value.length >= 10) {
                    // Demo: generate random points for returning customers
                    const demoPoints = Math.floor(Math.random() * 1500) + 100;
                    setCustomerLoyaltyPoints(demoPoints);
                    setCustomerId(1); // Simulate existing customer
                  } else {
                    setCustomerLoyaltyPoints(0);
                    setCustomerId(null);
                  }
                }}
              />
              <input
                type="email"
                className="input w-full"
                placeholder="Email (optional)"
                value={customerEmail}
                onChange={e => setCustomerEmail(e.target.value)}
              />
              {customerLoyaltyPoints > 0 && (
                <div className="bg-purple-50 rounded-lg p-3 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-purple-800">Returning Customer!</p>
                    <p className="text-xs text-purple-600">{customerLoyaltyPoints} loyalty points (${(customerLoyaltyPoints / 100).toFixed(2)} value)</p>
                  </div>
                </div>
              )}
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
                onClick={() => { setShowCustomerModal(false); setPayOpen(true); setCustomerLoyaltyPoints(0); }}
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
              <div className="text-4xl mb-2">{isOfflineSale ? '📱' : '✅'}</div>
              <h2 className={`text-xl font-semibold ${isOfflineSale ? 'text-orange-600' : 'text-green-600'}`}>
                {isOfflineSale ? 'Sale Saved Offline!' : 'Payment Successful!'}
              </h2>
              <p className="text-gray-500 mt-2">
                {isOfflineSale 
                  ? 'Will sync when back online' 
                  : `Sale #${lastSaleId} completed`}
              </p>
              {isOfflineSale && (
                <div className="mt-3 px-3 py-2 bg-orange-50 rounded-lg">
                  <p className="text-xs text-orange-700">
                    📡 This sale is stored locally and will automatically sync to the server when you&apos;re back online.
                  </p>
                </div>
              )}
            </div>
            <div className="mb-4 flex justify-center">
              <div ref={receiptRef}>
                <Receipt
                  saleId={lastSaleId || lastSale.id}
                  items={lastSale.items?.map((item: any) => ({
                    name: item.product_name || item.name,
                    price: Math.round(item.unit_price * 100),
                    quantity: item.quantity,
                  })) || []}
                  total={Math.round(lastSale.total * 100) || 0}
                  discount={Math.round((lastSale.discount || 0) * 100)}
                  couponCode={lastSale.coupon_code || appliedCoupon || undefined}
                  date={lastSale.created_at ? new Date(lastSale.created_at).toLocaleString() : new Date().toLocaleString()}
                  cashier={user?.full_name || user?.email}
                />
              </div>
            </div>
            <div className="space-y-3">
              <button
                onClick={printInAppReceipt}
                className="w-full py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-900 flex items-center justify-center gap-2"
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

      {/* Scanned Product Details Modal */}
      {showScannedProductModal && scannedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-2xl">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Product Scanned</h2>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="text-sm font-semibold text-gray-600">Product Name</label>
                <p className="text-lg font-medium text-gray-900">{scannedProduct.name}</p>
              </div>
              
              <div>
                <label className="text-sm font-semibold text-gray-600">SKU / Barcode</label>
                <p className="text-lg font-mono text-gray-900">{scannedProduct.sku || 'N/A'}</p>
              </div>
              
              <div>
                <label className="text-sm font-semibold text-gray-600">Price</label>
                <p className="text-2xl font-bold text-green-600">${(scannedProduct.price || 0).toFixed(2)}</p>
              </div>

              {scannedProduct.quantity !== undefined && (
                <div>
                  <label className="text-sm font-semibold text-gray-600">Stock Available</label>
                  <p className="text-lg text-gray-900">{scannedProduct.quantity} units</p>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  addToCart(scannedProduct);
                  setShowScannedProductModal(false);
                  setScannedProduct(null);
                }}
                className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold transition"
              >
                ✓ Add to Cart
              </button>
              <button
                onClick={() => {
                  setShowScannedProductModal(false);
                  setScannedProduct(null);
                }}
                className="flex-1 py-3 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 font-semibold transition"
              >
                ✕ Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
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
