'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

interface Integration {
  id: string;
  name: string;
  provider: string;
  category: string;
  description: string;
  icon: string;
  connected: boolean;
  connection_id?: number;
  last_sync?: string;
}

const AVAILABLE_INTEGRATIONS: Integration[] = [
  {
    id: 'quickbooks',
    name: 'QuickBooks Online',
    provider: 'quickbooks',
    category: 'Accounting',
    description: 'Sync sales, inventory, and customers with QuickBooks',
    icon: '📊',
    connected: false,
  },
  {
    id: 'xero',
    name: 'Xero',
    provider: 'xero',
    category: 'Accounting',
    description: 'Cloud accounting sync with Xero',
    icon: '💰',
    connected: false,
  },
  {
    id: 'shopify',
    name: 'Shopify',
    provider: 'shopify',
    category: 'E-commerce',
    description: 'Sync orders and inventory with your Shopify store',
    icon: '🛒',
    connected: false,
  },
  {
    id: 'woocommerce',
    name: 'WooCommerce',
    provider: 'woocommerce',
    category: 'E-commerce',
    description: 'Sync with your WordPress WooCommerce store',
    icon: '🛍️',
    connected: false,
  },
  {
    id: 'square',
    name: 'Square',
    provider: 'square',
    category: 'Payments',
    description: 'Sync inventory and catalog with Square',
    icon: '⬛',
    connected: false,
  },
  {
    id: 'doordash',
    name: 'DoorDash',
    provider: 'doordash',
    category: 'Delivery',
    description: 'Receive and manage DoorDash orders',
    icon: '🚗',
    connected: false,
  },
  {
    id: 'ubereats',
    name: 'UberEats',
    provider: 'ubereats',
    category: 'Delivery',
    description: 'Receive and manage UberEats orders',
    icon: '🍔',
    connected: false,
  },
];

function IntegrationsContent() {
  const searchParams = useSearchParams();
  const [integrations, setIntegrations] = useState<Integration[]>(AVAILABLE_INTEGRATIONS);
  const [loading, setLoading] = useState(true);
  const [connectingProvider, setConnectingProvider] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [shopDomain, setShopDomain] = useState('');
  const [showShopifyModal, setShowShopifyModal] = useState(false);

  useEffect(() => {
    // Check for OAuth callback status
    const connected = searchParams?.get('connected');
    const status = searchParams?.get('status');
    
    if (connected && status) {
      if (status === 'success') {
        setNotification({ type: 'success', message: `Successfully connected to ${connected}!` });
      } else {
        const message = searchParams?.get('message') || 'Connection failed';
        setNotification({ type: 'error', message: `Failed to connect to ${connected}: ${message}` });
      }
      
      // Clear URL params
      window.history.replaceState({}, '', '/settings/integrations');
    }

    fetchConnections();
  }, [searchParams]);

  const fetchConnections = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/oauth/connections', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const connections = await response.json();
        
        // Merge with available integrations
        setIntegrations(AVAILABLE_INTEGRATIONS.map(integration => {
          const connection = connections.find((c: { provider: string }) => c.provider === integration.provider);
          return {
            ...integration,
            connected: !!connection && connection.status === 'connected',
            connection_id: connection?.id,
            last_sync: connection?.last_sync,
          };
        }));
      }
    } catch (error) {
      console.error('Error fetching connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (integration: Integration) => {
    if (integration.provider === 'shopify') {
      setShowShopifyModal(true);
      return;
    }

    setConnectingProvider(integration.provider);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/oauth/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ provider: integration.provider }),
      });

      if (response.ok) {
        const data = await response.json();
        // Redirect to OAuth provider
        window.location.href = data.auth_url;
      } else {
        const error = await response.json();
        setNotification({ type: 'error', message: error.detail || 'Failed to initiate connection' });
      }
    } catch (error) {
      setNotification({ type: 'error', message: 'Network error' });
    } finally {
      setConnectingProvider(null);
    }
  };

  const handleConnectShopify = async () => {
    if (!shopDomain) {
      setNotification({ type: 'error', message: 'Please enter your Shopify store domain' });
      return;
    }

    setConnectingProvider('shopify');
    setShowShopifyModal(false);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/oauth/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ provider: 'shopify', shop_domain: shopDomain }),
      });

      if (response.ok) {
        const data = await response.json();
        window.location.href = data.auth_url;
      } else {
        const error = await response.json();
        setNotification({ type: 'error', message: error.detail || 'Failed to initiate connection' });
      }
    } catch (error) {
      setNotification({ type: 'error', message: 'Network error' });
    } finally {
      setConnectingProvider(null);
    }
  };

  const handleDisconnect = async (integration: Integration) => {
    if (!integration.connection_id) return;

    if (!confirm(`Are you sure you want to disconnect ${integration.name}?`)) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/oauth/connections/${integration.connection_id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setNotification({ type: 'success', message: `Disconnected from ${integration.name}` });
        fetchConnections();
      } else {
        setNotification({ type: 'error', message: 'Failed to disconnect' });
      }
    } catch (error) {
      setNotification({ type: 'error', message: 'Network error' });
    }
  };

  const handleSync = async (integration: Integration) => {
    if (!integration.connection_id) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/oauth/connections/${integration.connection_id}/sync`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setNotification({ type: 'success', message: `Sync initiated for ${integration.name}` });
      } else {
        setNotification({ type: 'error', message: 'Failed to start sync' });
      }
    } catch (error) {
      setNotification({ type: 'error', message: 'Network error' });
    }
  };

  const categories = [...new Set(integrations.map(i => i.category))];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-sm text-gray-500">Connect Vendly with your favorite tools</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Notification */}
        {notification && (
          <div className={`mb-6 p-4 rounded-lg ${
            notification.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            <div className="flex justify-between items-center">
              <span>{notification.message}</span>
              <button onClick={() => setNotification(null)} className="text-lg">×</button>
            </div>
          </div>
        )}

        {/* Connected Integrations */}
        {integrations.some(i => i.connected) && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Connected</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {integrations.filter(i => i.connected).map((integration) => (
                <div key={integration.id} className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center">
                      <span className="text-3xl mr-3">{integration.icon}</span>
                      <div>
                        <h3 className="font-semibold text-gray-900">{integration.name}</h3>
                        <p className="text-xs text-green-600">✓ Connected</p>
                      </div>
                    </div>
                  </div>
                  
                  {integration.last_sync && (
                    <p className="text-xs text-gray-500 mt-3">
                      Last synced: {new Date(integration.last_sync).toLocaleString()}
                    </p>
                  )}

                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={() => handleSync(integration)}
                      className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Sync Now
                    </button>
                    <button
                      onClick={() => handleDisconnect(integration)}
                      className="px-3 py-2 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Available Integrations by Category */}
        {categories.map((category) => {
          const categoryIntegrations = integrations.filter(i => i.category === category && !i.connected);
          if (categoryIntegrations.length === 0) return null;

          return (
            <div key={category} className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{category}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categoryIntegrations.map((integration) => (
                  <div key={integration.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-start">
                      <span className="text-3xl mr-3">{integration.icon}</span>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{integration.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">{integration.description}</p>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleConnect(integration)}
                      disabled={connectingProvider === integration.provider}
                      className="w-full mt-4 px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-800 disabled:opacity-50"
                    >
                      {connectingProvider === integration.provider ? 'Connecting...' : 'Connect'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Shopify Domain Modal */}
      {showShopifyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Connect Shopify Store</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Shopify Store Domain
              </label>
              <div className="flex items-center">
                <input
                  type="text"
                  value={shopDomain}
                  onChange={(e) => setShopDomain(e.target.value.replace('.myshopify.com', ''))}
                  placeholder="your-store"
                  className="flex-1 rounded-l-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <span className="px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md text-gray-500">
                  .myshopify.com
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowShopifyModal(false)}
                className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConnectShopify}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Connect Shopify
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    }>
      <IntegrationsContent />
    </Suspense>
  );
}
