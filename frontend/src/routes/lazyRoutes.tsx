// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\routes\lazyRoutes.tsx

/**
 * Lazy Loading Routes - Code Splitting for Better Performance
 * 
 * Split routes into separate bundles to reduce initial load time
 */

import { lazy, Suspense, ComponentType } from 'react';
import { DashboardSkeleton } from '../components/common/LoadingSkeleton';

// ============================================================================
// LAZY LOAD WRAPPER
// ============================================================================

interface LazyLoadProps {
  loadingComponent?: React.ReactNode;
}

export const lazyLoad = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  fallback?: React.ReactNode
) => {
  const LazyComponent = lazy(importFunc);

  return (props: React.ComponentProps<T>) => (
    <Suspense fallback={fallback || <PageLoadingFallback />}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

// ============================================================================
// DEFAULT LOADING FALLBACK
// ============================================================================

const PageLoadingFallback = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-gray-600 dark:text-gray-400">Loading...</p>
    </div>
  </div>
);

// ============================================================================
// LAZY LOADED PAGES
// ============================================================================

// Auth Pages
export const LoginPage = lazyLoad(
  () => import('../pages/Auth/LoginPage')
);

export const RegisterPage = lazyLoad(
  () => import('../pages/Auth/RegisterPage')
);

// Main Pages
export const DashboardPage = lazyLoad(
  () => import('../pages/Dashboard/DashboardPage'),
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
    <div className="max-w-7xl mx-auto">
      <DashboardSkeleton />
    </div>
  </div>
);

export const ComposerPage = lazyLoad(
  () => import('../pages/Composer/ComposerPage')
);

export const AnalyticsPage = lazyLoad(
  () => import('../pages/Analytics/AnalyticsPage'),
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
    <div className="max-w-7xl mx-auto">
      <DashboardSkeleton />
    </div>
  </div>
);

export const MessagesPage = lazyLoad(
  () => import('../pages/Messages/MessagesPage')
);

export const PlatformsPage = lazyLoad(
  () => import('../pages/Platforms/PlatformsPage')
);

export const SettingsPage = lazyLoad(
  () => import('../pages/Settings/SettingsPage')
);

// ============================================================================
// PRELOAD FUNCTIONS
// ============================================================================

// Preload critical routes for better UX
export const preloadDashboard = () => import('../pages/Dashboard/DashboardPage');
export const preloadComposer = () => import('../pages/Composer/ComposerPage');
export const preloadAnalytics = () => import('../pages/Analytics/AnalyticsPage');

// ============================================================================
// EXPORT
// ============================================================================

export default {
  LoginPage,
  RegisterPage,
  DashboardPage,
  ComposerPage,
  AnalyticsPage,
  MessagesPage,
  PlatformsPage,
  SettingsPage,
  preloadDashboard,
  preloadComposer,
  preloadAnalytics,
};
