// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\common\LoadingSkeleton.tsx

/**
 * LoadingSkeleton - Reusable Loading States
 * 
 * Beautiful skeleton loaders for better perceived performance
 */

import React from 'react';

// ============================================================================
// BASE SKELETON
// ============================================================================

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
  animation = 'pulse',
}) => {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';
  
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer',
    none: '',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${animationClasses[animation]}
        ${className}
      `}
      style={style}
    />
  );
};

// ============================================================================
// CARD SKELETON
// ============================================================================

export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
    <div className="flex items-center gap-4 mb-4">
      <Skeleton variant="circular" width={48} height={48} />
      <div className="flex-1">
        <Skeleton width="60%" className="mb-2" />
        <Skeleton width="40%" />
      </div>
    </div>
    <Skeleton width="100%" className="mb-2" />
    <Skeleton width="90%" className="mb-2" />
    <Skeleton width="70%" />
  </div>
);

// ============================================================================
// POST SKELETON
// ============================================================================

export const PostSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
    {/* Header */}
    <div className="flex items-center gap-3 mb-4">
      <Skeleton variant="circular" width={40} height={40} />
      <div className="flex-1">
        <Skeleton width="30%" className="mb-2" />
        <Skeleton width="20%" />
      </div>
    </div>

    {/* Content */}
    <div className="mb-4">
      <Skeleton width="100%" className="mb-2" />
      <Skeleton width="95%" className="mb-2" />
      <Skeleton width="80%" />
    </div>

    {/* Image placeholder */}
    <Skeleton variant="rectangular" height={200} className="mb-4" />

    {/* Footer */}
    <div className="flex items-center gap-6">
      <Skeleton width={60} />
      <Skeleton width={60} />
      <Skeleton width={60} />
    </div>
  </div>
);

// ============================================================================
// TABLE SKELETON
// ============================================================================

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
    {/* Header */}
    <div className="border-b border-gray-200 dark:border-gray-700 p-4">
      <div className="grid grid-cols-4 gap-4">
        <Skeleton width="80%" />
        <Skeleton width="60%" />
        <Skeleton width="70%" />
        <Skeleton width="50%" />
      </div>
    </div>

    {/* Rows */}
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="border-b border-gray-200 dark:border-gray-700 last:border-0 p-4">
        <div className="grid grid-cols-4 gap-4">
          <Skeleton width="90%" />
          <Skeleton width="70%" />
          <Skeleton width="60%" />
          <Skeleton width="40%" />
        </div>
      </div>
    ))}
  </div>
);

// ============================================================================
// STAT CARD SKELETON
// ============================================================================

export const StatCardSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
    <div className="flex items-center justify-between mb-4">
      <Skeleton variant="circular" width={48} height={48} />
      <Skeleton width={60} />
    </div>
    <Skeleton width="50%" height={32} className="mb-2" />
    <Skeleton width="40%" />
  </div>
);

// ============================================================================
// DASHBOARD SKELETON
// ============================================================================

export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* Stats Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCardSkeleton />
      <StatCardSkeleton />
      <StatCardSkeleton />
      <StatCardSkeleton />
    </div>

    {/* Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <Skeleton width="40%" className="mb-4" />
        <Skeleton variant="rectangular" height={300} />
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <Skeleton width="40%" className="mb-4" />
        <Skeleton variant="rectangular" height={300} />
      </div>
    </div>

    {/* Table */}
    <TableSkeleton rows={3} />
  </div>
);

// ============================================================================
// LIST SKELETON
// ============================================================================

export const ListSkeleton: React.FC<{ items?: number }> = ({ items = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1">
          <Skeleton width="60%" className="mb-2" />
          <Skeleton width="40%" />
        </div>
        <Skeleton width={80} height={32} variant="rectangular" />
      </div>
    ))}
  </div>
);

// ============================================================================
// FORM SKELETON
// ============================================================================

export const FormSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6">
    {/* Field 1 */}
    <div>
      <Skeleton width="30%" className="mb-2" />
      <Skeleton variant="rectangular" height={40} />
    </div>

    {/* Field 2 */}
    <div>
      <Skeleton width="25%" className="mb-2" />
      <Skeleton variant="rectangular" height={40} />
    </div>

    {/* Field 3 */}
    <div>
      <Skeleton width="35%" className="mb-2" />
      <Skeleton variant="rectangular" height={100} />
    </div>

    {/* Buttons */}
    <div className="flex gap-3">
      <Skeleton width={100} height={40} variant="rectangular" />
      <Skeleton width={80} height={40} variant="rectangular" />
    </div>
  </div>
);

// ============================================================================
// PROFILE SKELETON
// ============================================================================

export const ProfileSkeleton: React.FC = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
    {/* Avatar & Name */}
    <div className="flex items-center gap-4 mb-6">
      <Skeleton variant="circular" width={80} height={80} />
      <div className="flex-1">
        <Skeleton width="40%" height={24} className="mb-2" />
        <Skeleton width="30%" />
      </div>
    </div>

    {/* Stats */}
    <div className="grid grid-cols-3 gap-4 mb-6">
      <div className="text-center">
        <Skeleton width="60%" height={24} className="mb-1 mx-auto" />
        <Skeleton width="40%" className="mx-auto" />
      </div>
      <div className="text-center">
        <Skeleton width="60%" height={24} className="mb-1 mx-auto" />
        <Skeleton width="40%" className="mx-auto" />
      </div>
      <div className="text-center">
        <Skeleton width="60%" height={24} className="mb-1 mx-auto" />
        <Skeleton width="40%" className="mx-auto" />
      </div>
    </div>

    {/* Bio */}
    <Skeleton width="100%" className="mb-2" />
    <Skeleton width="90%" className="mb-2" />
    <Skeleton width="60%" />
  </div>
);

// ============================================================================
// EXPORT
// ============================================================================

export default Skeleton;