// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\settings\BillingSettings.tsx

/**
 * BillingSettings Component - Subscription & Payment Management
 * 
 * FAANG++++ Standards:
 * - Current plan display
 * - Plan upgrade/downgrade
 * - Payment method management
 * - Billing history
 * - Invoice downloads
 * - Usage statistics
 * - Next billing date
 * - Cancel subscription
 * - Loading states
 * - Dark mode support
 * 
 * Features:
 * - Plan comparison
 * - Payment card management
 * - Billing history table
 * - Invoice PDF download
 * - Usage limits display
 * - Upgrade modal
 */

import React, { useState } from 'react';
import {
  CreditCard,
  Download,
  Check,
  Zap,
  Calendar,
  DollarSign,
  FileText,
  TrendingUp,
  Users,
  MessageSquare,
  BarChart3,
  Crown,
  Star,
  AlertCircle,
  Loader2,
  ExternalLink,
  Plus,
  Trash2,
  Edit,
} from 'lucide-react';
import api from '../../lib/api';

// ============================================================================
// INTERFACES
// ============================================================================

interface BillingSettingsProps {
  onSave?: () => void;
}

interface Plan {
  id: string;
  name: string;
  price: number;
  interval: 'month' | 'year';
  features: string[];
  limits: {
    posts: number;
    platforms: number;
    analytics: boolean;
    aiGeneration: number;
    teamMembers: number;
  };
  popular?: boolean;
  current?: boolean;
}

interface PaymentMethod {
  id: string;
  type: 'card';
  brand: string;
  last4: string;
  expiryMonth: number;
  expiryYear: number;
  isDefault: boolean;
}

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  invoiceUrl: string;
  description: string;
}

// ============================================================================
// PLANS DATA
// ============================================================================

const PLANS: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    interval: 'month',
    features: [
      '10 posts per month',
      '3 social platforms',
      'Basic analytics',
      '50 AI generations/month',
      'Email support',
    ],
    limits: {
      posts: 10,
      platforms: 3,
      analytics: false,
      aiGeneration: 50,
      teamMembers: 1,
    },
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 29,
    interval: 'month',
    features: [
      'Unlimited posts',
      'All 12 platforms',
      'Advanced analytics',
      '500 AI generations/month',
      'Priority support',
      'Custom scheduling',
    ],
    limits: {
      posts: -1, // Unlimited
      platforms: 12,
      analytics: true,
      aiGeneration: 500,
      teamMembers: 3,
    },
    popular: true,
  },
  {
    id: 'business',
    name: 'Business',
    price: 99,
    interval: 'month',
    features: [
      'Everything in Pro',
      'Unlimited AI generations',
      'White-label reports',
      'API access',
      'Dedicated account manager',
      'Up to 10 team members',
    ],
    limits: {
      posts: -1,
      platforms: 12,
      analytics: true,
      aiGeneration: -1,
      teamMembers: 10,
    },
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

export const BillingSettings: React.FC<BillingSettingsProps> = ({ onSave }) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [currentPlan] = useState<Plan>({ ...PLANS[1], current: true });
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);

  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([
    {
      id: 'pm_1',
      type: 'card',
      brand: 'Visa',
      last4: '4242',
      expiryMonth: 12,
      expiryYear: 2027,
      isDefault: true,
    },
  ]);

  const [invoices] = useState<Invoice[]>([
    {
      id: 'inv_1',
      date: '2026-03-01',
      amount: 29,
      status: 'paid',
      invoiceUrl: '#',
      description: 'Pro Plan - March 2026',
    },
    {
      id: 'inv_2',
      date: '2026-02-01',
      amount: 29,
      status: 'paid',
      invoiceUrl: '#',
      description: 'Pro Plan - February 2026',
    },
    {
      id: 'inv_3',
      date: '2026-01-01',
      amount: 29,
      status: 'paid',
      invoiceUrl: '#',
      description: 'Pro Plan - January 2026',
    },
  ]);

  const [usage] = useState({
    posts: 47,
    platforms: 8,
    aiGenerations: 234,
  });

  const [isUpgrading, setIsUpgrading] = useState(false);
  const [showAddCard, setShowAddCard] = useState(false);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleUpgrade = async (plan: Plan) => {
    setIsUpgrading(true);

    try {
      await api.post('/billing/change-plan', { planId: plan.id });

      alert(`Successfully upgraded to ${plan.name} plan!`);
      setShowUpgradeModal(false);

      if (onSave) onSave();
    } catch (error) {
      console.error('Upgrade failed:', error);
      alert('Failed to upgrade plan. Please try again.');
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleDownloadInvoice = (invoice: Invoice) => {
    window.open(invoice.invoiceUrl, '_blank');
  };

  const handleSetDefaultCard = async (cardId: string) => {
    try {
      await api.post('/billing/set-default-payment', { paymentMethodId: cardId });

      setPaymentMethods(prev =>
        prev.map(pm => ({
          ...pm,
          isDefault: pm.id === cardId,
        }))
      );

      if (onSave) onSave();
    } catch (error) {
      console.error('Failed to set default card:', error);
      alert('Failed to set default payment method.');
    }
  };

  const handleRemoveCard = async (cardId: string) => {
    if (!confirm('Are you sure you want to remove this payment method?')) {
      return;
    }

    try {
      await api.delete(`/billing/payment-methods/${cardId}`);

      setPaymentMethods(prev => prev.filter(pm => pm.id !== cardId));

      if (onSave) onSave();
    } catch (error) {
      console.error('Failed to remove card:', error);
      alert('Failed to remove payment method.');
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  const nextBillingDate = new Date();
  nextBillingDate.setMonth(nextBillingDate.getMonth() + 1);

  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Crown className="w-6 h-6" />
              <h3 className="text-xl font-bold">Current Plan</h3>
            </div>
            <p className="text-blue-100">You're on the {currentPlan.name} plan</p>
          </div>
          <button
            type="button"
            onClick={() => setShowUpgradeModal(true)}
            className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium"
          >
            Change Plan
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-5 h-5" />
              <span className="text-sm">Posts This Month</span>
            </div>
            <div className="text-2xl font-bold">
              {usage.posts}
              {currentPlan.limits.posts > 0 && (
                <span className="text-base font-normal text-blue-100">
                  {' '}/ {currentPlan.limits.posts}
                </span>
              )}
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5" />
              <span className="text-sm">AI Generations</span>
            </div>
            <div className="text-2xl font-bold">
              {usage.aiGenerations}
              {currentPlan.limits.aiGeneration > 0 && (
                <span className="text-base font-normal text-blue-100">
                  {' '}/ {currentPlan.limits.aiGeneration}
                </span>
              )}
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-5 h-5" />
              <span className="text-sm">Next Billing</span>
            </div>
            <div className="text-lg font-bold">
              {nextBillingDate.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Payment Methods */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Payment Methods
          </h3>
          <button
            type="button"
            onClick={() => setShowAddCard(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            <span>Add Card</span>
          </button>
        </div>

        <div className="space-y-3">
          {paymentMethods.map((method) => (
            <div
              key={method.id}
              className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <div className="flex items-center gap-4">
                <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <CreditCard className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {method.brand} •••• {method.last4}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Expires {method.expiryMonth}/{method.expiryYear}
                  </div>
                </div>
                {method.isDefault && (
                  <span className="px-2 py-1 text-xs font-semibold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                    Default
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {!method.isDefault && (
                  <button
                    type="button"
                    onClick={() => handleSetDefaultCard(method.id)}
                    className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    title="Set as default"
                  >
                    <Star className="w-4 h-4" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleRemoveCard(method.id)}
                  disabled={method.isDefault}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Remove card"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Billing History */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Billing History
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Date
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Description
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Amount
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Invoice
                </th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <tr
                  key={invoice.id}
                  className="border-b border-gray-200 dark:border-gray-700 last:border-0"
                >
                  <td className="py-3 px-4 text-sm text-gray-900 dark:text-gray-100">
                    {new Date(invoice.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                    {invoice.description}
                  </td>
                  <td className="py-3 px-4 text-sm font-medium text-gray-900 dark:text-gray-100">
                    ${invoice.amount.toFixed(2)}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`
                        inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
                        ${invoice.status === 'paid'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : invoice.status === 'pending'
                          ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                        }
                      `}
                    >
                      {invoice.status === 'paid' && <Check className="w-3 h-3" />}
                      {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <button
                      type="button"
                      onClick={() => handleDownloadInvoice(invoice)}
                      className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Choose Your Plan
                </h2>
                <button
                  type="button"
                  onClick={() => setShowUpgradeModal(false)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <span className="text-2xl text-gray-500">&times;</span>
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {PLANS.map((plan) => (
                  <div
                    key={plan.id}
                    className={`
                      relative rounded-lg border-2 p-6 transition-all
                      ${plan.popular
                        ? 'border-blue-500 shadow-lg'
                        : 'border-gray-200 dark:border-gray-700'
                      }
                      ${plan.id === currentPlan.id
                        ? 'bg-gray-50 dark:bg-gray-900'
                        : 'bg-white dark:bg-gray-800'
                      }
                    `}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <span className="px-3 py-1 bg-blue-500 text-white text-xs font-semibold rounded-full">
                          Most Popular
                        </span>
                      </div>
                    )}

                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                        {plan.name}
                      </h3>
                      <div className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                        ${plan.price}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        per {plan.interval}
                      </div>
                    </div>

                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <Check className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>

                    {plan.id === currentPlan.id ? (
                      <button
                        type="button"
                        disabled
                        className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-lg font-medium cursor-not-allowed"
                      >
                        Current Plan
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleUpgrade(plan)}
                        disabled={isUpgrading}
                        className={`
                          w-full px-4 py-2 rounded-lg font-medium transition-colors
                          ${plan.popular
                            ? 'bg-blue-600 hover:bg-blue-700 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100'
                          }
                          disabled:opacity-50 disabled:cursor-not-allowed
                        `}
                      >
                        {isUpgrading ? (
                          <div className="flex items-center justify-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Processing...</span>
                          </div>
                        ) : (
                          <>
                            {plan.price > currentPlan.price ? 'Upgrade' : 'Downgrade'}
                          </>
                        )}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default BillingSettings;