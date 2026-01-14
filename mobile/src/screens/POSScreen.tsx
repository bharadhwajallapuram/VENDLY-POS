/**
 * POS Screen - Enhanced point of sale interface with all features
 * Refactored to use shared UI library
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Dimensions,
  Image,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { useCartStore } from '../store/cartStore';
import { useSyncStore } from '../store/syncStore';
import { useOrdersStore, HeldOrder } from '../store/ordersStore';
import { useCashDrawerStore } from '../store/cashDrawerStore';
import { useAuthStore } from '../store/authStore';
import { apiService } from '../services/api';
import { offlineService } from '../services/offline';

// Import new components
import { BarcodeScanner } from '../components/BarcodeScanner';
import { DiscountModal, DiscountData } from '../components/DiscountModal';
import { CustomerSelectModal } from '../components/CustomerSelectModal';
import { PaymentModal, PaymentData } from '../components/PaymentModal';
import { ReceiptView } from '../components/ReceiptView';
import { HeldOrdersModal } from '../components/HeldOrdersModal';

// Shared UI components
import {
  Header,
  Input,
  Button,
  IconButton,
  Badge,
  Avatar,
  EmptyState,
  colors,
  spacing,
  fontSize,
  fontWeight,
  radius,
} from '../ui';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const isTablet = SCREEN_WIDTH >= 768;

interface Product {
  id: number;
  name: string;
  sku?: string;
  price: number;
  barcode?: string;
  category?: string;
  category_id?: number;
  quantity: number;
  min_quantity?: number;
  image_url?: string;
}

interface Category {
  id: number;
  name: string;
  description?: string;
}

interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  loyalty_points: number;
  total_purchases: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  created_at: string;
}

interface Receipt {
  saleId?: number;
  receiptNumber: string;
  date: Date;
  items: Array<{
    name: string;
    quantity: number;
    price: number;
    discount: number;
  }>;
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  paymentMethod: string;
  cashier: string;
  customerId?: number;
  customerName?: string;
  storeInfo: {
    name: string;
    address: string;
    phone: string;
    website: string;
  };
}

export const POSScreen: React.FC = () => {
  const { user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  
  // Modal states
  const [showScanner, setShowScanner] = useState(false);
  const [showDiscountModal, setShowDiscountModal] = useState(false);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [showHeldOrdersModal, setShowHeldOrdersModal] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [processingPayment, setProcessingPayment] = useState(false);

  // Selected customer
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  
  // Last receipt for display
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [lastReceipt, setLastReceipt] = useState<Receipt | null>(null);

  const { isOnline, addPendingAction } = useSyncStore();
  const { holdOrder, getHeldOrderCount } = useOrdersStore();
  const { currentSession, recordSale } = useCashDrawerStore();
  const {
    items: cartItems,
    subtotal,
    discount,
    discountAmount,
    taxAmount,
    total,
    itemCount,
    addItem,
    removeItem,
    updateQuantity,
    setDiscount: setCartDiscount,
    setCustomer,
    clearCart,
  } = useCartStore();

  const heldOrderCount = getHeldOrderCount();

  // Fetch products - only when a category is selected (segment-first approach like web)
  const { data: products = [], isLoading } = useQuery<Product[]>({
    queryKey: ['products', searchQuery, selectedCategory?.id],
    queryFn: async () => {
      // Only load products when a category is selected
      if (!selectedCategory) {
        return [];
      }
      if (isOnline) {
        const data = await apiService.getProducts({
          search: searchQuery || undefined,
          category_id: selectedCategory.id,
        });
        // Cache for offline use
        await offlineService.cacheProducts(data as Product[]);
        return data as Product[];
      }
      // Use cached data when offline
      if (searchQuery) {
        return offlineService.searchCachedProducts(searchQuery);
      }
      return (await offlineService.getCachedProducts()) || [];
    },
    enabled: !!selectedCategory, // Only fetch when a category is selected
  });

  // Helper function for category icons (matching web client)
  const getCategoryIcon = (categoryName: string): string => {
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
  };

  // Handle back to category/segment view
  const handleBackToCategories = () => {
    setSelectedCategory(null);
    setSearchQuery('');
  };

  // Fetch categories with full objects (id, name)
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categoriesWithIds'],
    queryFn: async () => {
      if (isOnline) {
        const data = await apiService.getCategoriesWithIds();
        return data as Category[];
      }
      return [];
    },
  });

  const handleAddToCart = useCallback((product: Product) => {
    if (product.quantity <= 0) {
      Alert.alert('Out of Stock', 'This product is currently out of stock');
      return;
    }
    addItem({
      id: Date.now(),
      product_id: product.id,
      name: product.name,
      sku: product.sku,
      price: product.price,
      barcode: product.barcode,
    });
  }, [addItem]);

  const handleBarcodeScan = useCallback((barcode: string, _type: string) => {
    const product = products.find(p => p.barcode === barcode);
    if (product) {
      handleAddToCart(product);
      setShowScanner(false);
    } else {
      Alert.alert('Not Found', `No product found with barcode: ${barcode}`);
    }
  }, [products, handleAddToCart]);

  const handleApplyDiscount = (discountData: DiscountData) => {
    if (discountData.type === 'percentage') {
      setCartDiscount(discountData.value);
    } else if (discountData.type === 'fixed') {
      const percentage = (discountData.value / subtotal) * 100;
      setCartDiscount(percentage);
    }
    Alert.alert('Discount Applied', discountData.description || `${discountData.value}% off`);
  };

  const handleSelectCustomer = (customer: Customer | null) => {
    setSelectedCustomer(customer);
    if (customer) {
      setCustomer(customer.id, customer.name);
    } else {
      setCustomer(null, null);
    }
  };

  const handleHoldOrder = () => {
    if (cartItems.length === 0) {
      Alert.alert('Empty Cart', 'Add items to cart before holding');
      return;
    }
    const orderName = `Order #${Date.now().toString().slice(-6)}`;
    holdOrder({
      name: orderName,
      items: cartItems,
      customerId: selectedCustomer?.id,
      customerName: selectedCustomer?.name,
      subtotal,
      discount: discountAmount,
      taxAmount,
      total,
      createdBy: user?.id?.toString() || 'unknown',
      createdByName: user?.full_name || 'Unknown',
    });
    clearCart();
    setSelectedCustomer(null);
    Alert.alert('Order Held', `"${orderName}" has been saved`);
  };

  const handleRecallOrder = (order: HeldOrder) => {
    clearCart();
    order.items.forEach(item => {
      addItem(item);
    });
    if (order.customerId && order.customerName) {
      setCustomer(order.customerId, order.customerName);
      setSelectedCustomer({
        id: order.customerId,
        name: order.customerName,
        email: '',
        phone: '',
        loyalty_points: 0,
        total_purchases: 0,
        tier: 'bronze',
        created_at: '',
      });
    }
    if (order.discount > 0) {
      const percentage = (order.discount / order.subtotal) * 100;
      setCartDiscount(percentage);
    }
    setShowHeldOrdersModal(false);
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      Alert.alert('Empty Cart', 'Please add items to cart before checkout');
      return;
    }
    setShowPaymentModal(true);
  };

  const processPayment = async (paymentData: PaymentData) => {
    setProcessingPayment(true);

    const saleData = {
      items: cartItems.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        price: item.price,
        discount: item.discount,
      })),
      payment_method: paymentData.method,
      subtotal,
      discount: discountAmount,
      tax: taxAmount,
      total: paymentData.amount,
      customer_id: selectedCustomer?.id,
      tip: paymentData.tipAmount,
    };

    try {
      let saleId: number | undefined;
      
      if (isOnline) {
        const result = await apiService.createSale(saleData);
        // Extract sale ID from the response
        if (result && typeof result === 'object' && 'id' in result) {
          saleId = (result as { id: number }).id;
        }
      } else {
        addPendingAction('sale', saleData);
      }

      if (currentSession) {
        if (paymentData.method === 'cash') {
          recordSale(paymentData.amount, 'cash');
        } else {
          recordSale(paymentData.amount, paymentData.method);
        }
      }

      const receiptNumber = `RCP-${Date.now()}`;
      setLastReceipt({
        saleId,
        receiptNumber,
        date: new Date(),
        items: cartItems.map(item => ({
          name: item.name,
          quantity: item.quantity,
          price: item.price,
          discount: item.discount,
        })),
        subtotal,
        discount: discountAmount,
        tax: taxAmount,
        total: paymentData.amount,
        paymentMethod: paymentData.method === 'cash' ? 'Cash' : 
                       paymentData.method === 'card' ? 'Card' :
                       paymentData.method === 'digital' ? 'Digital Wallet' : 'Other',
        cashier: user?.full_name || 'Cashier',
        customerId: selectedCustomer?.id,
        customerName: selectedCustomer?.name,
        storeInfo: {
          name: 'Vendly Store',
          address: '123 Main Street, New York, NY 10001',
          phone: '(555) 123-4567',
          website: 'www.vendly.com',
        },
      });

      clearCart();
      setSelectedCustomer(null);
      setCartDiscount(0);
      setShowPaymentModal(false);
      setShowReceiptModal(true);
    } catch (error: unknown) {
      Alert.alert('Error', error instanceof Error ? error.message : 'Payment failed');
    } finally {
      setProcessingPayment(false);
    }
  };

  // Component for product card with image handling
  const ProductCard = ({ item }: { item: Product }) => {
    const [imageError, setImageError] = useState(false);
    
    return (
      <TouchableOpacity
        style={[styles.productCard, item.quantity <= 0 && styles.productCardDisabled]}
        onPress={() => handleAddToCart(item)}
        activeOpacity={0.7}
      >
        {/* Product Image with fallback like web client */}
        <View style={styles.productImageContainer}>
          {item.image_url && !imageError ? (
            <Image
              source={{ uri: item.image_url }}
              style={styles.productImage}
              resizeMode="cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <View style={styles.productImageFallback}>
              <Text style={styles.productImageFallbackText}>
                {item.name.charAt(0).toUpperCase()}
              </Text>
            </View>
          )}
        </View>
        <Text style={styles.productName} numberOfLines={2}>{item.name}</Text>
        <Text style={styles.productSku} numberOfLines={1}>{item.sku || 'No SKU'}</Text>
        <Text style={styles.productPrice}>${item.price.toFixed(2)}</Text>
        <Text style={[styles.productStock, item.quantity <= 0 && styles.outOfStock]}>
          Stock: {item.quantity}
        </Text>
      </TouchableOpacity>
    );
  };

  const renderProduct = ({ item }: { item: Product }) => <ProductCard item={item} />;

  const renderCartItem = ({ item }: { item: typeof cartItems[0] }) => (
    <View style={styles.cartItem}>
      <View style={styles.cartItemInfo}>
        <Text style={styles.cartItemName} numberOfLines={1}>{item.name}</Text>
        <Text style={styles.cartItemPrice}>
          ${item.price.toFixed(2)} × {item.quantity}
        </Text>
      </View>
      <View style={styles.cartItemActions}>
        <View style={styles.cartItemQuantity}>
          <TouchableOpacity
            style={styles.quantityButton}
            onPress={() => updateQuantity(item.product_id, item.quantity - 1)}
          >
            <Ionicons name="remove" size={16} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.quantityText}>{item.quantity}</Text>
          <TouchableOpacity
            style={styles.quantityButton}
            onPress={() => updateQuantity(item.product_id, item.quantity + 1)}
          >
            <Ionicons name="add" size={16} color="#fff" />
          </TouchableOpacity>
        </View>
        <Text style={styles.cartItemTotal}>
          ${(item.price * item.quantity).toFixed(2)}
        </Text>
        <TouchableOpacity
          style={styles.removeButton}
          onPress={() => removeItem(item.product_id)}
        >
          <Ionicons name="close" size={18} color="#ef4444" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <Header
        title="POS"
        leftContent={
          !isOnline && (
            <Badge variant="warning">Offline</Badge>
          )
        }
        rightActions={[
          {
            icon: 'pause-circle-outline',
            onPress: () => setShowHeldOrdersModal(true),
            badge: heldOrderCount > 0 ? heldOrderCount : undefined,
          },
          {
            icon: 'scan-outline',
            onPress: () => setShowScanner(true),
          },
        ]}
      />

      {/* Main Content */}
      <View style={styles.content}>
        {/* Products Section */}
        <View style={styles.productsSection}>
          {/* Search */}
          <View style={styles.searchRow}>
            <View style={styles.searchInputWrapper}>
              <Input
                placeholder="Search products..."
                value={searchQuery}
                onChangeText={setSearchQuery}
                icon="search"
                clearable={searchQuery.length > 0}
                onClear={() => setSearchQuery('')}
              />
            </View>
            <IconButton
              icon="barcode-outline"
              onPress={() => setShowScanner(true)}
              variant="secondary"
              size="lg"
            />
          </View>

          {/* Show Categories Grid or Products based on selection */}
          {!selectedCategory ? (
            /* Category/Segment Selection View */
            <View style={styles.categoryGridContainer}>
              <Text style={styles.sectionTitle}>Select a Category</Text>
              <FlatList
                data={categories}
                keyExtractor={(item) => item.id.toString()}
                numColumns={isTablet ? 4 : 2}
                contentContainerStyle={styles.categoryGrid}
                showsVerticalScrollIndicator={false}
                key={isTablet ? 'cat-tablet' : 'cat-phone'}
                renderItem={({ item }) => (
                  <TouchableOpacity
                    style={styles.categoryCard}
                    onPress={() => setSelectedCategory(item)}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.categoryIcon}>{getCategoryIcon(item.name)}</Text>
                    <Text style={styles.categoryCardText} numberOfLines={2}>
                      {item.name}
                    </Text>
                  </TouchableOpacity>
                )}
                ListEmptyComponent={
                  <View style={styles.emptyCategories}>
                    <Ionicons name="folder-open-outline" size={48} color={colors.textMuted} />
                    <Text style={styles.emptyCategoriesText}>No categories available</Text>
                  </View>
                }
              />
            </View>
          ) : (
            /* Products View for Selected Category */
            <>
              {/* Back Button and Category Header */}
              <View style={styles.categoryHeader}>
                <TouchableOpacity
                  style={styles.backButton}
                  onPress={handleBackToCategories}
                >
                  <Ionicons name="arrow-back" size={20} color={colors.text} />
                  <Text style={styles.backButtonText}>Back</Text>
                </TouchableOpacity>
                <View style={styles.categoryTitleContainer}>
                  <Text style={styles.categoryHeaderIcon}>{getCategoryIcon(selectedCategory.name)}</Text>
                  <Text style={styles.categoryHeaderTitle}>{selectedCategory.name}</Text>
                </View>
              </View>

              {/* Product count */}
              <Text style={styles.productCount}>
                {products.length} product{products.length !== 1 ? 's' : ''}
              </Text>

              {/* Products Grid */}
              {isLoading ? (
                <ActivityIndicator size="large" color="#0ea5e9" style={styles.loader} />
              ) : (
                <FlatList
                  data={products}
                  keyExtractor={(item) => item.id.toString()}
                  numColumns={isTablet ? 4 : 3}
                  renderItem={renderProduct}
                  contentContainerStyle={styles.productsGrid}
                  showsVerticalScrollIndicator={false}
                  key={isTablet ? 'tablet' : 'phone'}
                  ListEmptyComponent={
                    <View style={styles.emptyProducts}>
                      <Ionicons name="cube-outline" size={48} color={colors.textMuted} />
                      <Text style={styles.emptyProductsText}>No products in this category</Text>
                    </View>
                  }
                />
              )}
            </>
          )}
        </View>

        {/* Cart Section */}
        <View style={styles.cartSection}>
          {/* Customer Selection */}
          <TouchableOpacity
            style={styles.customerButton}
            onPress={() => setShowCustomerModal(true)}
          >
            {selectedCustomer ? (
              <>
                <Avatar name={selectedCustomer.name} size="sm" />
                <View style={styles.customerInfo}>
                  <Text style={styles.customerName}>{selectedCustomer.name}</Text>
                  <Text style={styles.customerPoints}>
                    {selectedCustomer.loyalty_points} points
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
              </>
            ) : (
              <>
                <Ionicons name="person-add-outline" size={20} color={colors.primary} />
                <Text style={styles.addCustomerText}>Add Customer</Text>
              </>
            )}
          </TouchableOpacity>

          {/* Cart Header */}
          <View style={styles.cartHeader}>
            <Text style={styles.cartTitle}>Cart</Text>
            <View style={styles.cartHeaderActions}>
              {cartItems.length > 0 && (
                <>
                  <IconButton
                    icon="pause"
                    onPress={handleHoldOrder}
                    variant="secondary"
                    size="sm"
                  />
                  <IconButton
                    icon="trash-outline"
                    onPress={() => {
                      Alert.alert('Clear Cart', 'Remove all items?', [
                        { text: 'Cancel', style: 'cancel' },
                        { text: 'Clear', style: 'destructive', onPress: clearCart },
                      ]);
                    }}
                    variant="secondary"
                    size="sm"
                  />
                </>
              )}
            </View>
          </View>

          <FlatList
            data={cartItems}
            keyExtractor={(item) => item.id.toString()}
            renderItem={renderCartItem}
            style={styles.cartList}
            ListEmptyComponent={
              <EmptyState
                icon="cart-outline"
                title="Cart is empty"
                message="Add products to begin"
              />
            }
          />

          {/* Discount Button */}
          {cartItems.length > 0 && (
            <TouchableOpacity
              style={styles.discountButton}
              onPress={() => setShowDiscountModal(true)}
            >
              <Ionicons name="pricetag-outline" size={18} color="#0ea5e9" />
              <Text style={styles.discountButtonText}>
                {discount > 0 ? `${discount}% discount applied` : 'Add Discount'}
              </Text>
            </TouchableOpacity>
          )}

          {/* Cart Totals */}
          <View style={styles.cartTotals}>
            <View style={styles.totalRow}>
              <Text style={styles.totalLabel}>Subtotal ({itemCount})</Text>
              <Text style={styles.totalValue}>${subtotal.toFixed(2)}</Text>
            </View>
            {discountAmount > 0 && (
              <View style={styles.totalRow}>
                <Text style={styles.totalLabel}>Discount</Text>
                <Text style={styles.discountValue}>-${discountAmount.toFixed(2)}</Text>
              </View>
            )}
            <View style={styles.totalRow}>
              <Text style={styles.totalLabel}>Tax</Text>
              <Text style={styles.totalValue}>${taxAmount.toFixed(2)}</Text>
            </View>
            <View style={[styles.totalRow, styles.grandTotalRow]}>
              <Text style={styles.grandTotalLabel}>Total</Text>
              <Text style={styles.grandTotalValue}>${total.toFixed(2)}</Text>
            </View>
          </View>

          {/* Checkout Button */}
          <Button
            title={`Charge $${total.toFixed(2)}`}
            onPress={handleCheckout}
            variant="success"
            size="lg"
            icon="card-outline"
            disabled={cartItems.length === 0}
            fullWidth
          />
        </View>
      </View>

      {/* Modals */}
      <BarcodeScanner
        visible={showScanner}
        onClose={() => setShowScanner(false)}
        onScan={handleBarcodeScan}
      />

      <DiscountModal
        visible={showDiscountModal}
        onClose={() => setShowDiscountModal(false)}
        onApplyDiscount={handleApplyDiscount}
        currentSubtotal={subtotal}
      />

      <CustomerSelectModal
        visible={showCustomerModal}
        onClose={() => setShowCustomerModal(false)}
        onSelectCustomer={handleSelectCustomer}
        currentCustomer={selectedCustomer}
      />

      <PaymentModal
        visible={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        onProcessPayment={processPayment}
        total={total}
        subtotal={subtotal}
        tax={taxAmount}
        discount={discountAmount}
      />

      {lastReceipt && (
        <ReceiptView
          visible={showReceiptModal}
          onClose={() => setShowReceiptModal(false)}
          receipt={lastReceipt}
        />
      )}

      <HeldOrdersModal
        visible={showHeldOrdersModal}
        onClose={() => setShowHeldOrdersModal(false)}
        onRecallOrder={handleRecallOrder}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    flexDirection: 'row',
  },
  productsSection: {
    flex: isTablet ? 2 : 1.5,
    borderRightWidth: 1,
    borderRightColor: colors.border,
  },
  searchRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    padding: spacing.md,
  },
  searchInputWrapper: {
    flex: 1,
  },
  categoriesContainer: {
    maxHeight: 40,
  },
  categoriesContent: {
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  categoryChip: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.xl,
    marginRight: spacing.sm,
  },
  categoryChipActive: {
    backgroundColor: colors.primary,
  },
  categoryChipText: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
  },
  categoryChipTextActive: {
    color: colors.white,
  },
  // Category Grid View styles (segment-first approach)
  categoryGridContainer: {
    flex: 1,
    paddingHorizontal: spacing.sm,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.semibold,
    marginBottom: spacing.md,
    marginTop: spacing.sm,
    paddingHorizontal: spacing.xs,
  },
  categoryGrid: {
    paddingBottom: spacing.xl,
  },
  categoryCard: {
    flex: 1,
    backgroundColor: colors.surface,
    margin: spacing.xs,
    borderRadius: radius.lg,
    padding: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 120,
    maxWidth: isTablet ? '23%' : '47%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  categoryIcon: {
    fontSize: 40,
    marginBottom: spacing.sm,
  },
  categoryCardText: {
    color: colors.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
    textAlign: 'center',
  },
  emptyCategories: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xxl,
  },
  emptyCategoriesText: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    marginTop: spacing.md,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    marginBottom: spacing.sm,
    gap: spacing.md,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    gap: spacing.xs,
  },
  backButtonText: {
    color: colors.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
  },
  categoryTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  categoryHeaderIcon: {
    fontSize: 24,
  },
  categoryHeaderTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.bold,
  },
  productCount: {
    color: colors.textMuted,
    fontSize: fontSize.xs,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.xs,
  },
  emptyProducts: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xxl,
  },
  emptyProductsText: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    marginTop: spacing.md,
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
  },
  productsGrid: {
    padding: spacing.sm,
    paddingBottom: spacing.xxl,
  },
  productCard: {
    flex: 1,
    backgroundColor: colors.surface,
    margin: spacing.xs,
    borderRadius: radius.md,
    padding: spacing.sm,
    alignItems: 'center',
    maxWidth: isTablet ? '23%' : '31%',
  },
  productCardDisabled: {
    opacity: 0.5,
  },
  productImageContainer: {
    width: '100%',
    height: 60,
    borderRadius: radius.md,
    overflow: 'hidden',
    marginBottom: spacing.xs,
    backgroundColor: colors.surfaceHover,
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  productImageFallback: {
    width: '100%',
    height: '100%',
    backgroundColor: '#dbeafe',
    justifyContent: 'center',
    alignItems: 'center',
  },
  productImageFallbackText: {
    fontSize: 24,
    fontWeight: fontWeight.bold,
    color: colors.primary,
  },
  productName: {
    color: colors.text,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.medium,
    textAlign: 'center',
    marginBottom: 2,
    height: 32,
  },
  productSku: {
    color: colors.textMuted,
    fontSize: 10,
    marginBottom: 2,
  },
  productPrice: {
    color: colors.text,
    fontSize: fontSize.md,
    fontWeight: fontWeight.bold,
  },
  productStock: {
    color: colors.textMuted,
    fontSize: 10,
    marginTop: 2,
  },
  outOfStock: {
    color: colors.danger,
  },
  cartSection: {
    flex: 1,
    padding: spacing.md,
  },
  customerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    marginBottom: spacing.md,
  },
  customerInfo: {
    flex: 1,
  },
  customerName: {
    color: colors.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
  },
  customerPoints: {
    color: colors.warning,
    fontSize: fontSize.xs,
  },
  addCustomerText: {
    flex: 1,
    color: colors.primary,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
  },
  cartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  cartTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.semibold,
  },
  cartHeaderActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  cartList: {
    flex: 1,
  },
  cartItem: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginBottom: spacing.xs,
  },
  cartItemInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  cartItemName: {
    flex: 1,
    color: colors.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
  },
  cartItemPrice: {
    color: colors.textMuted,
    fontSize: fontSize.xs,
  },
  cartItemActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cartItemQuantity: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  quantityButton: {
    backgroundColor: colors.primary,
    width: 26,
    height: 26,
    borderRadius: radius.xs,
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityText: {
    color: colors.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
    minWidth: 20,
    textAlign: 'center',
  },
  cartItemTotal: {
    color: colors.success,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.semibold,
  },
  removeButton: {
    padding: spacing.xs,
  },
  discountButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    justifyContent: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  discountButtonText: {
    color: colors.primary,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
  },
  cartTotals: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  totalLabel: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
  },
  totalValue: {
    color: colors.text,
    fontSize: fontSize.sm,
  },
  discountValue: {
    color: colors.success,
    fontSize: fontSize.sm,
  },
  grandTotalRow: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.sm,
    marginTop: spacing.xs,
    marginBottom: 0,
  },
  grandTotalLabel: {
    color: colors.text,
    fontSize: fontSize.md,
    fontWeight: fontWeight.semibold,
  },
  grandTotalValue: {
    color: colors.success,
    fontSize: fontSize.xl,
    fontWeight: fontWeight.bold,
  },
});

export default POSScreen;
