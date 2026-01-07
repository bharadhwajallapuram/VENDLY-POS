/**
 * Dashboard Screen - Sales summary and analytics
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type TimeRange = 'today' | 'week' | 'month';

interface SalesSummary {
  totalSales: number;
  transactionCount: number;
  averageTicket: number;
  itemsSold: number;
  returns: number;
  netSales: number;
}

interface TopProduct {
  id: number;
  name: string;
  quantity: number;
  revenue: number;
}

interface HourlySale {
  hour: string;
  amount: number;
}

// Mock data
const MOCK_SUMMARY: Record<TimeRange, SalesSummary> = {
  today: {
    totalSales: 2847.50,
    transactionCount: 42,
    averageTicket: 67.80,
    itemsSold: 156,
    returns: 89.99,
    netSales: 2757.51,
  },
  week: {
    totalSales: 18543.25,
    transactionCount: 287,
    averageTicket: 64.60,
    itemsSold: 1024,
    returns: 425.00,
    netSales: 18118.25,
  },
  month: {
    totalSales: 72150.00,
    transactionCount: 1156,
    averageTicket: 62.41,
    itemsSold: 4250,
    returns: 1850.00,
    netSales: 70300.00,
  },
};

const TOP_PRODUCTS: TopProduct[] = [
  { id: 1, name: 'Wireless Mouse Pro', quantity: 45, revenue: 1349.55 },
  { id: 2, name: 'USB-C Hub 7-in-1', quantity: 38, revenue: 1710.00 },
  { id: 3, name: 'Mechanical Keyboard', quantity: 28, revenue: 2519.72 },
  { id: 4, name: 'Webcam HD 1080p', quantity: 25, revenue: 1249.75 },
  { id: 5, name: 'Laptop Stand', quantity: 22, revenue: 879.78 },
];

const HOURLY_SALES: HourlySale[] = [
  { hour: '9AM', amount: 150 },
  { hour: '10AM', amount: 280 },
  { hour: '11AM', amount: 420 },
  { hour: '12PM', amount: 580 },
  { hour: '1PM', amount: 450 },
  { hour: '2PM', amount: 320 },
  { hour: '3PM', amount: 390 },
  { hour: '4PM', amount: 520 },
  { hour: '5PM', amount: 680 },
  { hour: '6PM', amount: 450 },
];

export const DashboardScreen: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('today');
  const [refreshing, setRefreshing] = useState(false);

  const summary = MOCK_SUMMARY[timeRange];
  const maxHourlySale = Math.max(...HOURLY_SALES.map(s => s.amount));

  const onRefresh = async () => {
    setRefreshing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(1)}k`;
    }
    return `$${amount.toFixed(2)}`;
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <View style={styles.timeRangeSelector}>
          {(['today', 'week', 'month'] as TimeRange[]).map(range => (
            <TouchableOpacity
              key={range}
              style={[
                styles.timeRangeButton,
                timeRange === range && styles.timeRangeButtonActive,
              ]}
              onPress={() => setTimeRange(range)}
            >
              <Text style={[
                styles.timeRangeText,
                timeRange === range && styles.timeRangeTextActive,
              ]}>
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3b82f6" />
        }
      >
        {/* Main Stats */}
        <View style={styles.mainStatsRow}>
          <View style={[styles.mainStatCard, styles.primaryStatCard]}>
            <Text style={styles.mainStatLabel}>Net Sales</Text>
            <Text style={styles.mainStatValue}>${summary.netSales.toLocaleString('en-US', { minimumFractionDigits: 2 })}</Text>
            <View style={styles.statChange}>
              <Ionicons name="trending-up" size={14} color="#22c55e" />
              <Text style={styles.statChangeText}>+12.5% vs last {timeRange}</Text>
            </View>
          </View>
        </View>

        {/* Quick Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: '#1e3a5f' }]}>
              <Ionicons name="receipt-outline" size={20} color="#3b82f6" />
            </View>
            <Text style={styles.statValue}>{summary.transactionCount}</Text>
            <Text style={styles.statLabel}>Transactions</Text>
          </View>
          <View style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: '#422006' }]}>
              <Ionicons name="trending-up-outline" size={20} color="#f59e0b" />
            </View>
            <Text style={styles.statValue}>${summary.averageTicket.toFixed(2)}</Text>
            <Text style={styles.statLabel}>Avg. Ticket</Text>
          </View>
          <View style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: '#052e16' }]}>
              <Ionicons name="cube-outline" size={20} color="#22c55e" />
            </View>
            <Text style={styles.statValue}>{summary.itemsSold}</Text>
            <Text style={styles.statLabel}>Items Sold</Text>
          </View>
          <View style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: '#450a0a' }]}>
              <Ionicons name="arrow-undo-outline" size={20} color="#ef4444" />
            </View>
            <Text style={styles.statValue}>${summary.returns.toFixed(2)}</Text>
            <Text style={styles.statLabel}>Returns</Text>
          </View>
        </View>

        {/* Hourly Sales Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.sectionTitle}>Hourly Sales</Text>
          <View style={styles.chartContainer}>
            {HOURLY_SALES.map((sale, index) => (
              <View key={index} style={styles.chartBar}>
                <View 
                  style={[
                    styles.chartBarFill,
                    { height: `${(sale.amount / maxHourlySale) * 100}%` }
                  ]} 
                />
                <Text style={styles.chartBarLabel}>{sale.hour}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Top Products */}
        <View style={styles.topProductsCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Top Selling Products</Text>
            <TouchableOpacity>
              <Text style={styles.viewAllText}>View All</Text>
            </TouchableOpacity>
          </View>
          {TOP_PRODUCTS.map((product, index) => (
            <View key={product.id} style={styles.productRow}>
              <View style={styles.productRank}>
                <Text style={styles.productRankText}>{index + 1}</Text>
              </View>
              <View style={styles.productInfo}>
                <Text style={styles.productName}>{product.name}</Text>
                <Text style={styles.productQuantity}>{product.quantity} sold</Text>
              </View>
              <Text style={styles.productRevenue}>${product.revenue.toFixed(2)}</Text>
            </View>
          ))}
        </View>

        {/* Payment Methods Breakdown */}
        <View style={styles.paymentBreakdownCard}>
          <Text style={styles.sectionTitle}>Payment Methods</Text>
          <View style={styles.paymentMethods}>
            <View style={styles.paymentMethod}>
              <View style={[styles.paymentDot, { backgroundColor: '#3b82f6' }]} />
              <View style={styles.paymentInfo}>
                <Text style={styles.paymentType}>Card</Text>
                <Text style={styles.paymentAmount}>$1,847.50</Text>
              </View>
              <Text style={styles.paymentPercent}>65%</Text>
            </View>
            <View style={styles.paymentMethod}>
              <View style={[styles.paymentDot, { backgroundColor: '#22c55e' }]} />
              <View style={styles.paymentInfo}>
                <Text style={styles.paymentType}>Cash</Text>
                <Text style={styles.paymentAmount}>$710.00</Text>
              </View>
              <Text style={styles.paymentPercent}>25%</Text>
            </View>
            <View style={styles.paymentMethod}>
              <View style={[styles.paymentDot, { backgroundColor: '#a855f7' }]} />
              <View style={styles.paymentInfo}>
                <Text style={styles.paymentType}>Digital</Text>
                <Text style={styles.paymentAmount}>$200.00</Text>
              </View>
              <Text style={styles.paymentPercent}>7%</Text>
            </View>
            <View style={styles.paymentMethod}>
              <View style={[styles.paymentDot, { backgroundColor: '#f59e0b' }]} />
              <View style={styles.paymentInfo}>
                <Text style={styles.paymentType}>Gift Card</Text>
                <Text style={styles.paymentAmount}>$90.00</Text>
              </View>
              <Text style={styles.paymentPercent}>3%</Text>
            </View>
          </View>
          
          {/* Visual bar */}
          <View style={styles.paymentBar}>
            <View style={[styles.paymentBarSegment, { flex: 65, backgroundColor: '#3b82f6' }]} />
            <View style={[styles.paymentBarSegment, { flex: 25, backgroundColor: '#22c55e' }]} />
            <View style={[styles.paymentBarSegment, { flex: 7, backgroundColor: '#a855f7' }]} />
            <View style={[styles.paymentBarSegment, { flex: 3, backgroundColor: '#f59e0b' }]} />
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickAction}>
            <Ionicons name="download-outline" size={20} color="#3b82f6" />
            <Text style={styles.quickActionText}>Export Report</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickAction}>
            <Ionicons name="print-outline" size={20} color="#3b82f6" />
            <Text style={styles.quickActionText}>Print Summary</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 16,
    paddingHorizontal: 16,
    backgroundColor: '#1e293b',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#f1f5f9',
    marginBottom: 12,
  },
  timeRangeSelector: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 8,
    padding: 4,
  },
  timeRangeButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  timeRangeButtonActive: {
    backgroundColor: '#3b82f6',
  },
  timeRangeText: {
    fontSize: 14,
    color: '#64748b',
    fontWeight: '500',
  },
  timeRangeTextActive: {
    color: '#fff',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  mainStatsRow: {
    marginBottom: 16,
  },
  mainStatCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#334155',
  },
  primaryStatCard: {
    backgroundColor: '#052e16',
    borderColor: '#166534',
  },
  mainStatLabel: {
    fontSize: 14,
    color: '#86efac',
  },
  mainStatValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#f1f5f9',
    marginVertical: 4,
  },
  statChange: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statChangeText: {
    fontSize: 13,
    color: '#22c55e',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    width: (SCREEN_WIDTH - 44) / 2,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  statIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  statLabel: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  chartCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  chartContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 120,
    gap: 4,
  },
  chartBar: {
    flex: 1,
    alignItems: 'center',
    height: '100%',
    justifyContent: 'flex-end',
  },
  chartBarFill: {
    width: '100%',
    backgroundColor: '#3b82f6',
    borderRadius: 4,
    minHeight: 4,
  },
  chartBarLabel: {
    fontSize: 9,
    color: '#64748b',
    marginTop: 6,
  },
  topProductsCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  viewAllText: {
    fontSize: 14,
    color: '#3b82f6',
  },
  productRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  productRank: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  productRankText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748b',
  },
  productInfo: {
    flex: 1,
    marginLeft: 12,
  },
  productName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#f1f5f9',
  },
  productQuantity: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  productRevenue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#22c55e',
  },
  paymentBreakdownCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  paymentMethods: {
    gap: 12,
    marginBottom: 16,
  },
  paymentMethod: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  paymentDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  paymentInfo: {
    flex: 1,
    marginLeft: 12,
  },
  paymentType: {
    fontSize: 14,
    color: '#f1f5f9',
  },
  paymentAmount: {
    fontSize: 12,
    color: '#64748b',
  },
  paymentPercent: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
  },
  paymentBar: {
    flexDirection: 'row',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  paymentBarSegment: {
    height: '100%',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
  },
  quickAction: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1e293b',
    paddingVertical: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  quickActionText: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '500',
  },
});

export default DashboardScreen;
