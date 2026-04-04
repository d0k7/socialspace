// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\pages\Settings\SettingsPage.tsx

/**
 * SettingsPage - Main Settings Page with Tabbed Navigation
 * 
 * FAANG++++ Standards:
 * - Tabbed navigation interface
 * - All settings components integrated
 * - URL-based tab routing
 * - Mobile responsive
 * - Breadcrumb navigation
 * - Auto-save indicators
 * - Loading states
 * - Dark mode support
 * 
 * Features:
 * - 5 settings tabs (Account, Notifications, AI, Billing, Danger Zone)
 * - Clean tabbed interface
 * - URL query params for deep linking
 * - Mobile sidebar/dropdown
 * - Keyboard navigation
 * - Accessible
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Settings,
  User,
  Bell,
  Sparkles,
  CreditCard,
  AlertTriangle,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react';

// Settings Components
import AccountSettings from '../../components/settings/AccountSettings';
import NotificationSettings from '../../components/settings/NotificationSettings';
import AIPreferences from '../../components/settings/AIPreferences';
import BillingSettings from '../../components/settings/BillingSettings';
import DangerZone from '../../components/settings/DangerZone';

// ============================================================================
// INTERFACES
// ============================================================================

interface SettingsPageProps {
  // Optional: pre-selected tab
  initialTab?: SettingsTab;
}

type SettingsTab = 'account' | 'notifications' | 'ai' | 'billing' | 'danger';

interface TabConfig {
  id: SettingsTab;
  label: string;
  icon: React.ReactNode;
  component: React.ReactNode;
  description: string;
}

// ============================================================================
// TAB CONFIGURATION
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'account',
    label: 'Account',
    icon: <User className="w-5 h-5" />,
    component: <AccountSettings />,
    description: 'Manage your profile and password',
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: <Bell className="w-5 h-5" />,
    component: <NotificationSettings />,
    description: 'Configure notification preferences',
  },
  {
    id: 'ai',
    label: 'AI Preferences',
    icon: <Sparkles className="w-5 h-5" />,
    component: <AIPreferences />,
    description: 'Customize AI tone and features',
  },
  {
    id: 'billing',
    label: 'Billing',
    icon: <CreditCard className="w-5 h-5" />,
    component: <BillingSettings />,
    description: 'Manage subscription and payments',
  },
  {
    id: 'danger',
    label: 'Danger Zone',
    icon: <AlertTriangle className="w-5 h-5" />,
    component: <DangerZone />,
    description: 'Delete account and export data',
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

export const SettingsPage: React.FC<SettingsPageProps> = ({ initialTab = 'account' }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // ============================================================================
  // STATE
  // ============================================================================

  const [activeTab, setActiveTab] = useState<SettingsTab>(initialTab);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // ============================================================================
  // SYNC WITH URL
  // ============================================================================

  useEffect(() => {
    // Get tab from URL query params
    const params = new URLSearchParams(location.search);
    const tabParam = params.get('tab') as SettingsTab;

    if (tabParam && TABS.find(t => t.id === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [location.search]);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleTabChange = (tab: SettingsTab) => {
    setActiveTab(tab);
    setIsMobileSidebarOpen(false);

    // Update URL
    const params = new URLSearchParams(location.search);
    params.set('tab', tab);
    navigate(`${location.pathname}?${params.toString()}`, { replace: true });
  };

  // ============================================================================
  // GET ACTIVE TAB CONFIG
  // ============================================================================

  const activeTabConfig = TABS.find(t => t.id === activeTab) || TABS[0];

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Title */}
            <div className="flex items-center gap-3">
              <Settings className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Settings
              </h1>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              type="button"
              onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
              className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              {isMobileSidebarOpen ? (
                <X className="w-6 h-6 text-gray-700 dark:text-gray-300" />
              ) : (
                <Menu className="w-6 h-6 text-gray-700 dark:text-gray-300" />
              )}
            </button>
          </div>

          {/* Breadcrumb - Desktop Only */}
          <div className="hidden lg:flex items-center gap-2 pb-4 text-sm text-gray-600 dark:text-gray-400">
            <span>Settings</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-gray-900 dark:text-gray-100 font-medium">
              {activeTabConfig.label}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar - Desktop */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <nav className="sticky top-8 space-y-1">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => handleTabChange(tab.id)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left
                    ${activeTab === tab.id
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }
                    ${tab.id === 'danger' && activeTab !== 'danger'
                      ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10'
                      : ''
                    }
                  `}
                >
                  <div className={`
                    ${activeTab === tab.id
                      ? 'text-blue-600 dark:text-blue-400'
                      : tab.id === 'danger'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-600 dark:text-gray-400'
                    }
                  `}>
                    {tab.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{tab.label}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                      {tab.description}
                    </div>
                  </div>
                </button>
              ))}
            </nav>
          </aside>

          {/* Mobile Sidebar Overlay */}
          {isMobileSidebarOpen && (
            <>
              <div
                className="lg:hidden fixed inset-0 bg-black/50 z-40"
                onClick={() => setIsMobileSidebarOpen(false)}
              />
              <div className="lg:hidden fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 z-50 overflow-y-auto">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Settings
                    </h2>
                    <button
                      type="button"
                      onClick={() => setIsMobileSidebarOpen(false)}
                      className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                    >
                      <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    </button>
                  </div>
                </div>
                <nav className="p-4 space-y-1">
                  {TABS.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => handleTabChange(tab.id)}
                      className={`
                        w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left
                        ${activeTab === tab.id
                          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }
                        ${tab.id === 'danger' && activeTab !== 'danger'
                          ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10'
                          : ''
                        }
                      `}
                    >
                      <div className={`
                        ${activeTab === tab.id
                          ? 'text-blue-600 dark:text-blue-400'
                          : tab.id === 'danger'
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-gray-600 dark:text-gray-400'
                        }
                      `}>
                        {tab.icon}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{tab.label}</div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                          {tab.description}
                        </div>
                      </div>
                    </button>
                  ))}
                </nav>
              </div>
            </>
          )}

          {/* Content Area */}
          <main className="flex-1 min-w-0">
            {/* Mobile Tab Title */}
            <div className="lg:hidden mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className={`
                  ${activeTab === 'danger'
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-blue-600 dark:text-blue-400'
                  }
                `}>
                  {activeTabConfig.icon}
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {activeTabConfig.label}
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {activeTabConfig.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Active Tab Content */}
            <div className="transition-opacity duration-200">
              {activeTabConfig.component}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default SettingsPage;
