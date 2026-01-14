/**
 * Products Screen - Product catalog and management
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../services/api';
import { offlineService } from '../services/offline';
import { useSyncStore } from '../store/syncStore';

interface Category {
  id: number;
  name: string;
}

interface Product {
  id: number;
  name: string;
  sku?: string;
  barcode?: string;
  price: number;
  cost_price?: number;
  category_id?: number;
  quantity: number;
  min_quantity?: number;
  is_active?: boolean;
}

export const ProductsScreen: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const { isOnline } = useSyncStore();

  const {
    data: products = [],
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<Product[]>({
    queryKey: ['products', searchQuery, selectedCategoryId],
    queryFn: async () => {
      if (isOnline) {
        const data = await apiService.getProducts({
          search: searchQuery || undefined,
          category_id: selectedCategoryId || undefined,
          limit: 100,
        });
        await offlineService.cacheProducts(data as Product[]);
        return data as Product[];
      }
      if (searchQuery) {
        return offlineService.searchCachedProducts(searchQuery);
      }
      const cached = (await offlineService.getCachedProducts()) || [];
      // Filter cached products by category if selected
      if (selectedCategoryId) {
        return cached.filter((p: Product) => p.category_id === selectedCategoryId);
      }
      return cached;
    },
  });

  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: async () => {
      if (isOnline) {
        const data = await apiService.getCategories();
        // Ensure we have category objects with id and name
        if (Array.isArray(data)) {
          return data.map(cat => 
            typeof cat === 'object' && cat !== null 
              ? { id: (cat as Category).id, name: (cat as Category).name }
              : { id: 0, name: String(cat) }
          );
        }
        return [];
      }
      return [];
    },
  });

  const getStockStatus = useCallback((product: Product) => {
    const qty = product.quantity ?? 0;
    const minQty = product.min_quantity ?? 0;
    if (qty <= 0) {
      return { label: 'Out of Stock', color: '#ef4444', bg: '#fee2e2' };
    }
    if (qty <= minQty) {
      return { label: 'Low Stock', color: '#f59e0b', bg: '#fef3c7' };
    }
    return { label: 'In Stock', color: '#22c55e', bg: '#dcfce7' };
  }, []);

  const renderProduct = ({ item }: { item: Product }) => {
    const stockStatus = getStockStatus(item);
    
    return (
      <View style={styles.productCard}>
        <View style={styles.productImage}>
          <Ionicons name="cube-outline" size={28} color="#64748b" />
        </View>
        
        <View style={styles.productInfo}>
          <Text style={styles.productName} numberOfLines={1}>{item.name}</Text>
          <Text style={styles.productSku}>SKU: {item.sku}</Text>
          {item.barcode && (
            <Text style={styles.productBarcode}>
              <Ionicons name="barcode-outline" size={12} color="#64748b" /> {item.barcode}
            </Text>
          )}
        </View>

        <View style={styles.productMeta}>
          <Text style={styles.productPrice}>${item.price.toFixed(2)}</Text>
          <View style={[styles.stockBadge, { backgroundColor: stockStatus.bg }]}>
            <Text style={[styles.stockBadgeText, { color: stockStatus.color }]}>
              {item.quantity ?? 0} in stock
            </Text>
          </View>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Products</Text>
        {!isOnline && (
          <View style={styles.offlineBadge}>
            <Ionicons name="cloud-offline" size={14} color="#fbbf24" />
            <Text style={styles.offlineText}>Offline</Text>
          </View>
        )}
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#64748b" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, SKU, or barcode..."
          placeholderTextColor="#64748b"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color="#64748b" />
          </TouchableOpacity>
        )}
      </View>

      {/* Categories */}
      <FlatList
        horizontal
        data={[{ id: -1, name: 'All' }, ...categories]}
        keyExtractor={(item) => `cat-${item.name}-${item.id}`}
        showsHorizontalScrollIndicator={false}
        style={styles.categoriesContainer}
        contentContainerStyle={styles.categoriesContent}
        renderItem={({ item }) => {
          const isSelected = item.id === -1 ? selectedCategoryId === null : selectedCategoryId === item.id;
          return (
            <TouchableOpacity
              style={[
                styles.categoryChip,
                isSelected ? styles.categoryChipActive : null,
              ]}
              onPress={() => setSelectedCategoryId(item.id === -1 ? null : item.id)}
            >
              <Text
                style={[
                  styles.categoryChipText,
                  isSelected ? styles.categoryChipTextActive : null,
                ]}
              >
                {item.name}
              </Text>
            </TouchableOpacity>
          );
        }}
      />

      {/* Products List */}
      {isLoading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#0ea5e9" />
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderProduct}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#0ea5e9"
              colors={['#0ea5e9']}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="cube-outline" size={64} color="#334155" />
              <Text style={styles.emptyText}>No products found</Text>
              <Text style={styles.emptySubtext}>Try adjusting your search or filters</Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  offlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef3c7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  offlineText: {
    color: '#d97706',
    fontSize: 12,
    fontWeight: '500',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    color: '#0f172a',
    fontSize: 16,
  },
  categoriesContainer: {
    marginTop: 12,
    marginBottom: 8,
    flexGrow: 0,
    flexShrink: 0,
  },
  categoriesContent: {
    paddingHorizontal: 16,
    paddingRight: 32,
    paddingVertical: 4,
  },
  categoryChip: {
    backgroundColor: '#e2e8f0',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 10,
    borderWidth: 1,
    borderColor: '#94a3b8',
  },
  categoryChipActive: {
    backgroundColor: '#0ea5e9',
    borderColor: '#0ea5e9',
  },
  categoryChipText: {
    color: '#0f172a',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  categoryChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    color: '#0f172a',
    fontSize: 20,
    fontWeight: '700',
  },
  statLabel: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 2,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
  },
  productCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  productImage: {
    width: 48,
    height: 48,
    backgroundColor: '#f1f5f9',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    color: '#0f172a',
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  productSku: {
    color: '#64748b',
    fontSize: 12,
  },
  productBarcode: {
    color: '#64748b',
    fontSize: 11,
    marginTop: 2,
  },
  productMeta: {
    alignItems: 'flex-end',
  },
  productPrice: {
    color: '#0ea5e9',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  stockBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  stockBadgeText: {
    fontSize: 11,
    fontWeight: '500',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    paddingTop: 64,
  },
  emptyText: {
    color: '#64748b',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  emptySubtext: {
    color: '#94a3b8',
    fontSize: 14,
    marginTop: 4,
  },
});

export default ProductsScreen;
