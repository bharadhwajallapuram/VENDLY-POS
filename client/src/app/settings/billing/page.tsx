'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  CreditCard,
  Building2,
  Users,
  ShoppingCart,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  Download,
  TrendingUp,
  LucideIcon,
} from 'lucide-react';
import { useAuth } from '@/store/auth';

interface Subscription {
  id: number;
  tenant_id: number;
  plan_id: number;
  plan_name: string;
  status: string;
  billing_interval: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  transactions_used: number;
  transactions_limit: number;
}

interface Tenant {
  id: number;
  name: string;
  slug: string;
  email: string;
  business_name: string | null;
  subscription: {
    plan_name: string;
    plan_tier: string;
    status: string;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
  } | null;
  limits: {
    max_stores: number;
    max_users: number;
    max_products: number;
    max_transactions_monthly: number;
    transactions_used?: number;
    features: Record<string, boolean>;
  };
  stores: Array<{ id: number; name: string; code: string; city: string }>;
}

interface Invoice {
  id: number;
  invoice_number: string;
  status: string;
  total: number;
  currency: string;
  invoice_date: string;
  paid_at: string | null;
  invoice_pdf_url: string | null;
}

interface UsageLimit {
  allowed: boolean;
  used: number;
  max: number;
  remaining: number;
}

function BillingPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { token } = useAuth();

  const [tenant, setTenant] = useState<Tenant | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [usage, setUsage] = useState<{
    transactions: UsageLimit;
    stores: UsageLimit;
    users: UsageLimit;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (searchParams?.get('success') === 'true') {
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 5000);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, router]);

  const fetchData = async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const headers = {
      Authorization: `Bearer ${token}`,
    };

    try {
      const [tenantRes, subRes, invoicesRes, txUsage, storeUsage, userUsage] = await Promise.all([
        fetch(`${apiUrl}/api/v1/billing/tenants/me`, { headers }),
        fetch(`${apiUrl}/api/v1/billing/subscription`, { headers }),
        fetch(`${apiUrl}/api/v1/billing/invoices`, { headers }),
        fetch(`${apiUrl}/api/v1/billing/usage/transactions`, { headers }),
        fetch(`${apiUrl}/api/v1/billing/usage/stores`, { headers }),
        fetch(`${apiUrl}/api/v1/billing/usage/users`, { headers }),
      ]);

      if (tenantRes.ok) {
        setTenant(await tenantRes.json());
      }
      if (subRes.ok) {
        setSubscription(await subRes.json());
      }
      if (invoicesRes.ok) {
        setInvoices(await invoicesRes.json());
      }

      if (txUsage.ok && storeUsage.ok && userUsage.ok) {
        setUsage({
          transactions: await txUsage.json(),
          stores: await storeUsage.json(),
          users: await userUsage.json(),
        });
      }
    } catch (error) {
      console.error('Failed to fetch billing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const openBillingPortal = async () => {
    setPortalLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/billing/subscription/portal`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        const data = await res.json();
        window.location.href = data.url;
      } else {
        alert('Failed to open billing portal');
      }
    } catch (error) {
      console.error('Portal error:', error);
    } finally {
      setPortalLoading(false);
    }
  };

  const cancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will still have access until the end of your billing period.')) {
      return;
    }

    setCancelLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/billing/subscription/cancel?at_period_end=true`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res.ok) {
        alert('Subscription will be canceled at the end of your billing period.');
        fetchData();
      } else {
        const error = await res.json();
        alert(error.detail || 'Failed to cancel subscription');
      }
    } catch (error) {
      console.error('Cancel error:', error);
    } finally {
      setCancelLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'trialing':
        return 'bg-green-100 text-green-800';
      case 'past_due':
        return 'bg-red-100 text-red-800';
      case 'canceled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const UsageBar = ({ label, icon: Icon, usage: u }: { label: string; icon: LucideIcon; usage: UsageLimit }) => {
    const percentage = Math.min(100, (u.used / u.max) * 100);
    const isNearLimit = percentage >= 80;
    const isAtLimit = percentage >= 100;

    return (
      <div className="bg-white rounded-lg p-4 border">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center">
            <Icon className="h-5 w-5 text-gray-500 mr-2" />
            <span className="font-medium text-gray-700">{label}</span>
          </div>
          <span className={`text-sm ${isAtLimit ? 'text-red-600 font-bold' : 'text-gray-500'}`}>
            {u.used.toLocaleString()} / {u.max >= 999999 ? '∞' : u.max.toLocaleString()}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(100, percentage)}%` }}
          />
        </div>
        {isNearLimit && !isAtLimit && (
          <p className="text-xs text-yellow-600 mt-1">Approaching limit</p>
        )}
        {isAtLimit && (
          <p className="text-xs text-red-600 mt-1">Limit reached - upgrade to continue</p>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      {/* Success Message */}
      {showSuccess && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
          <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
          <span className="text-green-800">
            Your subscription has been activated successfully!
          </span>
        </div>
      )}

      <h1 className="text-3xl font-bold text-gray-900 mb-8">Billing & Subscription</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Current Plan */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Plan</h2>

            {tenant?.subscription ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="text-2xl font-bold text-gray-900">
                      {tenant.subscription.plan_name}
                    </span>
                    <span
                      className={`ml-3 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                        tenant.subscription.status
                      )}`}
                    >
                      {tenant.subscription.status}
                    </span>
                  </div>
                  <button
                    onClick={() => router.push('/pricing')}
                    className="text-indigo-600 hover:text-indigo-700 font-medium flex items-center"
                  >
                    <TrendingUp className="h-4 w-4 mr-1" />
                    Upgrade
                  </button>
                </div>

                {tenant.subscription.current_period_end && (
                  <p className="text-gray-600 mb-4">
                    {tenant.subscription.cancel_at_period_end ? (
                      <span className="text-red-600">
                        <AlertTriangle className="inline h-4 w-4 mr-1" />
                        Cancels on {formatDate(tenant.subscription.current_period_end)}
                      </span>
                    ) : (
                      <>Next billing date: {formatDate(tenant.subscription.current_period_end)}</>
                    )}
                  </p>
                )}

                <div className="flex space-x-4">
                  <button
                    onClick={openBillingPortal}
                    disabled={portalLoading}
                    className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <CreditCard className="h-4 w-4 mr-2" />
                    {portalLoading ? 'Loading...' : 'Manage Payment Method'}
                    <ExternalLink className="h-4 w-4 ml-2" />
                  </button>

                  {tenant.subscription.plan_tier !== 'free' &&
                    !tenant.subscription.cancel_at_period_end && (
                      <button
                        onClick={cancelSubscription}
                        disabled={cancelLoading}
                        className="px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        {cancelLoading ? 'Canceling...' : 'Cancel Subscription'}
                      </button>
                    )}
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">No active subscription</p>
                <button
                  onClick={() => router.push('/pricing')}
                  className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
                >
                  View Plans
                </button>
              </div>
            )}
          </div>

          {/* Usage */}
          {usage && (
            <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Usage This Month</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <UsageBar label="Transactions" icon={ShoppingCart} usage={usage.transactions} />
                <UsageBar label="Stores" icon={Building2} usage={usage.stores} />
                <UsageBar label="Team Members" icon={Users} usage={usage.users} />
              </div>
            </div>
          )}

          {/* Invoices */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Invoice History</h2>

            {invoices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3">Invoice</th>
                      <th className="pb-3">Date</th>
                      <th className="pb-3">Amount</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.map((invoice) => (
                      <tr key={invoice.id} className="border-b last:border-0">
                        <td className="py-3 font-medium">{invoice.invoice_number}</td>
                        <td className="py-3 text-gray-600">{formatDate(invoice.invoice_date)}</td>
                        <td className="py-3">
                          ${invoice.total.toFixed(2)} {invoice.currency}
                        </td>
                        <td className="py-3">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              invoice.status === 'paid'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {invoice.status}
                          </span>
                        </td>
                        <td className="py-3">
                          {invoice.invoice_pdf_url && (
                            <a
                              href={invoice.invoice_pdf_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-indigo-600 hover:text-indigo-700"
                            >
                              <Download className="h-4 w-4" />
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No invoices yet</p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Organization Info */}
          {tenant && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-gray-500">Name</label>
                  <p className="font-medium">{tenant.name}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Email</label>
                  <p className="font-medium">{tenant.email}</p>
                </div>
                {tenant.business_name && (
                  <div>
                    <label className="text-sm text-gray-500">Business Name</label>
                    <p className="font-medium">{tenant.business_name}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Stores */}
          {tenant && tenant.stores.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Stores</h2>
                <span className="text-sm text-gray-500">
                  {tenant.stores.length} / {tenant.limits.max_stores === 999 ? '∞' : tenant.limits.max_stores}
                </span>
              </div>
              <ul className="space-y-2">
                {tenant.stores.map((store) => (
                  <li key={store.id} className="flex items-center text-sm">
                    <Building2 className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="font-medium">{store.name}</span>
                    <span className="text-gray-400 ml-2">({store.code})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Plan Features */}
          {tenant?.limits.features && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Plan Features</h2>
              <ul className="space-y-2">
                {Object.entries(tenant.limits.features).map(([key, enabled]) => (
                  <li
                    key={key}
                    className={`flex items-center text-sm ${
                      enabled ? 'text-gray-700' : 'text-gray-400'
                    }`}
                  >
                    {enabled ? (
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    ) : (
                      <span className="h-4 w-4 border border-gray-300 rounded-full mr-2" />
                    )}
                    {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    }>
      <BillingPageContent />
    </Suspense>
  );
}
