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

interface Product {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  price: number;
  cost_price?: number;
  category?: string;
  stock_quantity: number;
  low_stock_threshold: number;
  is_active: boolean;
}

export const ProductsScreen: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const { isOnline } = useSyncStore();

  const {
    data: products = [],
    isLoading,
    refetch,
    isRefetching,
  } = useQuery<Product[]>({
    queryKey: ['products', searchQuery, selectedCategory],
    queryFn: async () => {
      if (isOnline) {
        const data = await apiService.getProducts({
          search: searchQuery || undefined,
          category: selectedCategory || undefined,
          limit: 100,
        });
        await offlineService.cacheProducts(data as Product[]);
        return data as Product[];
      }
      if (searchQuery) {
        return offlineService.searchCachedProducts(searchQuery);
      }
      return (await offlineService.getCachedProducts()) || [];
    },
  });

  const { data: categories = [] } = useQuery<string[]>({
    queryKey: ['categories'],
    queryFn: async () => {
      if (isOnline) {
        const data = await apiService.getCategories();
        await offlineService.cacheCategories(data as string[]);
        return data as string[];
      }
      return (await offlineService.getCachedCategories()) || [];
    },
  });

  const getStockStatus = useCallback((product: Product) => {
    if (product.stock_quantity <= 0) {
      return { label: 'Out of Stock', color: '#ef4444', bg: '#450a0a' };
    }
    if (product.stock_quantity <= product.low_stock_threshold) {
      return { label: 'Low Stock', color: '#f59e0b', bg: '#451a03' };
    }
    return { label: 'In Stock', color: '#22c55e', bg: '#052e16' };
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
              {item.stock_quantity} in stock
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
        data={['All', ...categories]}
        keyExtractor={(item) => item}
        showsHorizontalScrollIndicator={false}
        style={styles.categoriesContainer}
        contentContainerStyle={styles.categoriesContent}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.categoryChip,
              (item === 'All' ? !selectedCategory : selectedCategory === item) &&
                styles.categoryChipActive,
            ]}
            onPress={() => setSelectedCategory(item === 'All' ? null : item)}
          >
            <Text
              style={[
                styles.categoryChipText,
                (item === 'All' ? !selectedCategory : selectedCategory === item) &&
                  styles.categoryChipTextActive,
              ]}
            >
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Stats Row */}
      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{products.length}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#22c55e' }]}>
            {products.filter((p) => p.stock_quantity > p.low_stock_threshold).length}
          </Text>
          <Text style={styles.statLabel}>In Stock</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#f59e0b' }]}>
            {products.filter((p) => p.stock_quantity > 0 && p.stock_quantity <= p.low_stock_threshold).length}
          </Text>
          <Text style={styles.statLabel}>Low Stock</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#ef4444' }]}>
            {products.filter((p) => p.stock_quantity <= 0).length}
          </Text>
          <Text style={styles.statLabel}>Out</Text>
        </View>
      </View>

      {/* Products List */}
      {isLoading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
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
              tintColor="#3b82f6"
              colors={['#3b82f6']}
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
    backgroundColor: '#0f172a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  offlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#422006',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  offlineText: {
    color: '#fbbf24',
    fontSize: 12,
    fontWeight: '500',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    color: '#ffffff',
    fontSize: 16,
  },
  categoriesContainer: {
    maxHeight: 52,
    marginTop: 12,
  },
  categoriesContent: {
    paddingHorizontal: 16,
  },
  categoryChip: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  categoryChipActive: {
    backgroundColor: '#3b82f6',
  },
  categoryChipText: {
    color: '#94a3b8',
    fontSize: 14,
    fontWeight: '500',
  },
  categoryChipTextActive: {
    color: '#ffffff',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    padding: 12,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    color: '#ffffff',
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
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  productImage: {
    width: 48,
    height: 48,
    backgroundColor: '#334155',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    color: '#ffffff',
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
    color: '#3b82f6',
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
    color: '#475569',
    fontSize: 14,
    marginTop: 4,
  },
});

export default ProductsScreen;
