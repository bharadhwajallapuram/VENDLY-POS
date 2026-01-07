'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Check, X, Zap, Building2, Rocket, Crown } from 'lucide-react';
import { useAuth } from '@/store/auth';

interface Plan {
  id: number;
  name: string;
  tier: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  max_stores: number;
  max_users: number;
  max_products: number;
  max_transactions_monthly: number;
  features: {
    inventory: boolean;
    reports: boolean;
    advanced_reports: boolean;
    api_access: boolean;
    custom_branding: boolean;
    priority_support: boolean;
    ai_insights: boolean;
    multi_store: boolean;
    integrations: boolean;
  };
}

const tierIcons: Record<string, React.ReactNode> = {
  free: <Zap className="h-6 w-6" />,
  starter: <Rocket className="h-6 w-6" />,
  professional: <Building2 className="h-6 w-6" />,
  enterprise: <Crown className="h-6 w-6" />,
};

const tierColors: Record<string, string> = {
  free: 'bg-gray-100 text-gray-800 border-gray-200',
  starter: 'bg-blue-100 text-blue-800 border-blue-200',
  professional: 'bg-purple-100 text-purple-800 border-purple-200',
  enterprise: 'bg-amber-100 text-amber-800 border-amber-200',
};

const featureLabels: Record<string, string> = {
  inventory: 'Inventory Management',
  reports: 'Basic Reports',
  advanced_reports: 'Advanced Analytics',
  api_access: 'API Access',
  custom_branding: 'Custom Branding',
  priority_support: 'Priority Support',
  ai_insights: 'AI Insights',
  multi_store: 'Multi-Store Support',
  integrations: 'Third-Party Integrations',
};

export default function PricingPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');
  const [checkoutLoading, setCheckoutLoading] = useState<number | null>(null);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/billing/plans`);
      if (res.ok) {
        const data = await res.json();
        setPlans(data);
      }
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (plan: Plan) => {
    if (plan.tier === 'free') {
      // Free plan - just redirect to signup/dashboard
      if (token) {
        router.push('/pos');
      } else {
        router.push('/register');
      }
      return;
    }

    if (!token) {
      // Not logged in - redirect to register first
      router.push(`/register?plan=${plan.id}&interval=${billingInterval}`);
      return;
    }

    // Create checkout session
    setCheckoutLoading(plan.id);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/billing/subscription/checkout`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            plan_id: plan.id,
            billing_interval: billingInterval,
          }),
        }
      );

      if (res.ok) {
        const data = await res.json();
        // Redirect to Stripe Checkout
        window.location.href = data.url;
      } else {
        const error = await res.json();
        alert(error.detail || 'Failed to create checkout session');
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Failed to initiate checkout');
    } finally {
      setCheckoutLoading(null);
    }
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getYearlySavings = (plan: Plan) => {
    const monthlyTotal = plan.price_monthly * 12;
    const savings = monthlyTotal - plan.price_yearly;
    if (savings > 0) {
      return Math.round((savings / monthlyTotal) * 100);
    }
    return 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Simple, Transparent Pricing
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            Choose the plan that&apos;s right for your business
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex justify-center mb-10">
          <div className="bg-gray-100 p-1 rounded-lg inline-flex">
            <button
              onClick={() => setBillingInterval('monthly')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                billingInterval === 'monthly'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingInterval('yearly')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                billingInterval === 'yearly'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Yearly
              <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                Save up to 17%
              </span>
            </button>
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-4 lg:gap-8">
          {plans.map((plan) => {
            const price = billingInterval === 'monthly' ? plan.price_monthly : plan.price_yearly;
            const savings = getYearlySavings(plan);
            const isPopular = plan.tier === 'professional';

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-2xl shadow-lg overflow-hidden transition-transform hover:scale-105 ${
                  isPopular ? 'ring-2 ring-indigo-500' : 'border border-gray-200'
                }`}
              >
                {isPopular && (
                  <div className="absolute top-0 right-0 bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                    POPULAR
                  </div>
                )}

                <div className="p-6">
                  {/* Plan Header */}
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-4 ${tierColors[plan.tier]}`}>
                    {tierIcons[plan.tier]}
                    <span className="ml-2">{plan.name}</span>
                  </div>

                  <p className="text-gray-500 text-sm mb-4">{plan.description}</p>

                  {/* Price */}
                  <div className="mb-6">
                    <span className="text-4xl font-extrabold text-gray-900">
                      {price === 0 ? 'Free' : formatPrice(price, plan.currency)}
                    </span>
                    {price > 0 && (
                      <span className="text-gray-500 text-sm">
                        /{billingInterval === 'monthly' ? 'mo' : 'yr'}
                      </span>
                    )}
                    {billingInterval === 'yearly' && savings > 0 && (
                      <div className="text-green-600 text-sm mt-1">
                        Save {savings}% vs monthly
                      </div>
                    )}
                  </div>

                  {/* CTA Button */}
                  <button
                    onClick={() => handleSelectPlan(plan)}
                    disabled={checkoutLoading === plan.id}
                    className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                      isPopular
                        ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                        : plan.tier === 'free'
                        ? 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                    } disabled:opacity-50`}
                  >
                    {checkoutLoading === plan.id ? (
                      <span className="flex items-center justify-center">
                        <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></span>
                        Processing...
                      </span>
                    ) : plan.tier === 'free' ? (
                      'Get Started Free'
                    ) : (
                      'Start 14-Day Trial'
                    )}
                  </button>

                  {/* Limits */}
                  <div className="mt-6 pt-6 border-t border-gray-100">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Includes:</h4>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex items-center">
                        <Check className="h-4 w-4 text-green-500 mr-2" />
                        {plan.max_stores === 999 ? 'Unlimited' : plan.max_stores} store{plan.max_stores !== 1 ? 's' : ''}
                      </li>
                      <li className="flex items-center">
                        <Check className="h-4 w-4 text-green-500 mr-2" />
                        {plan.max_users === 999 ? 'Unlimited' : plan.max_users} user{plan.max_users !== 1 ? 's' : ''}
                      </li>
                      <li className="flex items-center">
                        <Check className="h-4 w-4 text-green-500 mr-2" />
                        {plan.max_products >= 999999 ? 'Unlimited' : plan.max_products.toLocaleString()} products
                      </li>
                      <li className="flex items-center">
                        <Check className="h-4 w-4 text-green-500 mr-2" />
                        {plan.max_transactions_monthly >= 999999
                          ? 'Unlimited'
                          : plan.max_transactions_monthly.toLocaleString()}{' '}
                        transactions/mo
                      </li>
                    </ul>
                  </div>

                  {/* Features */}
                  <div className="mt-6 pt-6 border-t border-gray-100">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Features:</h4>
                    <ul className="space-y-2 text-sm">
                      {Object.entries(plan.features).map(([key, enabled]) => (
                        <li
                          key={key}
                          className={`flex items-center ${enabled ? 'text-gray-700' : 'text-gray-400'}`}
                        >
                          {enabled ? (
                            <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          ) : (
                            <X className="h-4 w-4 text-gray-300 mr-2 flex-shrink-0" />
                          )}
                          {featureLabels[key] || key}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ or Trust Section */}
        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Trusted by businesses worldwide
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            All plans include SSL encryption, automatic backups, and 99.9% uptime SLA.
            Cancel anytime with no questions asked.
          </p>
          <div className="mt-8 flex justify-center space-x-8 text-gray-400">
            <div className="flex items-center">
              <Check className="h-5 w-5 text-green-500 mr-2" />
              <span>No credit card required for free plan</span>
            </div>
            <div className="flex items-center">
              <Check className="h-5 w-5 text-green-500 mr-2" />
              <span>14-day free trial on paid plans</span>
            </div>
            <div className="flex items-center">
              <Check className="h-5 w-5 text-green-500 mr-2" />
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
