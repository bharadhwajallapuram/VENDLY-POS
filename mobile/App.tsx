/**
 * Vendly POS Mobile App - Full Navigation
 */

import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';

import {
  LoginScreen,
  POSScreen,
  ProductsScreen,
  InventoryScreen,
  SettingsScreen,
  ReturnsScreen,
  RegisterScreen,
  DashboardScreen,
  ReportsScreen,
  PaymentsScreen,
  EODReportsScreen,
} from './src/screens';
import { useAuthStore } from './src/store/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Light theme matching web client
const LightTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#0ea5e9',      // sky-500
    background: '#f8fafc',   // slate-50
    card: '#ffffff',         // white
    text: '#0f172a',         // slate-900
    border: '#e2e8f0',       // slate-200
    notification: '#ef4444',
  },
};

function MainTabs() {
  return (
    <Tab.Navigator
      id="MainTabs"
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopColor: '#e2e8f0',
          height: 65,
          paddingBottom: 10,
          paddingTop: 5,
        },
        tabBarActiveTintColor: '#0ea5e9',
        tabBarInactiveTintColor: '#94a3b8',
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'help';
          
          switch (route.name) {
            case 'POS':
              iconName = focused ? 'cart' : 'cart-outline';
              break;
            case 'Products':
              iconName = focused ? 'cube' : 'cube-outline';
              break;
            case 'Inventory':
              iconName = focused ? 'layers' : 'layers-outline';
              break;
            case 'Dashboard':
              iconName = focused ? 'stats-chart' : 'stats-chart-outline';
              break;
            case 'More':
              iconName = focused ? 'menu' : 'menu-outline';
              break;
          }
          
          return <Ionicons name={iconName} size={24} color={color} />;
        },
      })}
    >
      <Tab.Screen name="POS" component={POSScreen} />
      <Tab.Screen name="Products" component={ProductsScreen} />
      <Tab.Screen name="Inventory" component={InventoryScreen} />
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="More" component={MoreStack} />
    </Tab.Navigator>
  );
}

function MoreStack() {
  return (
    <Stack.Navigator
      id="MoreStack"
      screenOptions={{
        headerStyle: { backgroundColor: '#ffffff' },
        headerTintColor: '#0f172a',
        headerTitleStyle: { fontWeight: '600' },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="Settings" component={SettingsScreen} />
      <Stack.Screen name="Returns" component={ReturnsScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="Reports" component={ReportsScreen} options={{ title: 'Sales Reports' }} />
      <Stack.Screen name="Payments" component={PaymentsScreen} options={{ title: 'Payments' }} />
      <Stack.Screen name="EODReports" component={EODReportsScreen} options={{ title: 'End of Day' }} />
    </Stack.Navigator>
  );
}

function RootNavigator() {
  const { isAuthenticated, loadStoredAuth } = useAuthStore();

  useEffect(() => {
    loadStoredAuth();
  }, [loadStoredAuth]);

  return (
    <Stack.Navigator id="RootStack" screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name="Login" component={LoginScreen} />
      ) : (
        <Stack.Screen name="Main" component={MainTabs} />
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer theme={LightTheme}>
        <StatusBar style="dark" />
        <RootNavigator />
      </NavigationContainer>
    </QueryClientProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
});
