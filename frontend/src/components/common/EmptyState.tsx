// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\common\EmptyState.tsx

/**
 * EmptyState - Helpful Empty State Messages
 * 
 * Beautiful empty states with actions to guide users
 */

import React, { ReactNode } from 'react';
import {
  FileText,
  Inbox,
  Users,
  BarChart3,
  Calendar,
  MessageSquare,
  Search,
  AlertCircle,
  Plus,
} from 'lucide-react';

// ============================================================================
// INTERFACES
// ============================================================================

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };
  className?: string;
}

// ============================================================================
// BASE EMPTY STATE
// ============================================================================

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => (
  <div className={`flex flex-col items-center justify-center py-12 px-4 text-center ${className}`}>
    {icon && (
      <div className="mb-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-full">
        {icon}
      </div>
    )}

    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
      {title}
    </h3>

    <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mb-6">
      {description}
    </p>

    {action && (
      <button
        type="button"
        onClick={action.onClick}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
      >
        {action.icon}
        <span>{action.label}</span>
      </button>
    )}
  </div>
);

// ============================================================================
// PRESET EMPTY STATES
// ============================================================================

export const EmptyPosts: React.FC<{ onCreatePost?: () => void }> = ({ onCreatePost }) => (
  <EmptyState
    icon={<FileText className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="No posts yet"
    description="You haven't created any posts. Start creating content to engage with your audience across all platforms."
    action={onCreatePost ? {
      label: 'Create Your First Post',
      onClick: onCreatePost,
      icon: <Plus className="w-4 h-4" />,
    } : undefined}
  />
);

export const EmptyMessages: React.FC = () => (
  <EmptyState
    icon={<MessageSquare className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="No messages"
    description="You don't have any messages yet. Messages from your social media platforms will appear here."
  />
);

export const EmptyAnalytics: React.FC<{ onCreatePost?: () => void }> = ({ onCreatePost }) => (
  <EmptyState
    icon={<BarChart3 className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="No analytics data yet"
    description="Start posting content to see your analytics and insights. Track engagement, reach, and performance across all platforms."
    action={onCreatePost ? {
      label: 'Create Your First Post',
      onClick: onCreatePost,
      icon: <Plus className="w-4 h-4" />,
    } : undefined}
  />
);

export const EmptySchedule: React.FC<{ onSchedulePost?: () => void }> = ({ onSchedulePost }) => (
  <EmptyState
    icon={<Calendar className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="No scheduled posts"
    description="You don't have any posts scheduled. Plan your content calendar and schedule posts in advance."
    action={onSchedulePost ? {
      label: 'Schedule a Post',
      onClick: onSchedulePost,
      icon: <Calendar className="w-4 h-4" />,
    } : undefined}
  />
);

export const EmptyPlatforms: React.FC<{ onConnectPlatform?: () => void }> = ({ onConnectPlatform }) => (
  <EmptyState
    icon={<Users className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="No platforms connected"
    description="Connect your social media accounts to start posting and managing your content from one place."
    action={onConnectPlatform ? {
      label: 'Connect Platform',
      onClick: onConnectPlatform,
      icon: <Plus className="w-4 h-4" />,
    } : undefined}
  />
);

export const EmptySearch: React.FC<{ query?: string }> = ({ query }) => (
  <EmptyState
    icon={<Search className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="No results found"
    description={
      query
        ? `We couldn't find anything matching "${query}". Try adjusting your search terms.`
        : "We couldn't find any results. Try searching for something else."
    }
  />
);

export const EmptyInbox: React.FC = () => (
  <EmptyState
    icon={<Inbox className="w-12 h-12 text-gray-400 dark:text-gray-600" />}
    title="All caught up!"
    description="You don't have any unread messages. Check back later for new notifications and updates."
  />
);

export const ErrorState: React.FC<{ onRetry?: () => void; message?: string }> = ({
  onRetry,
  message = "We couldn't load this content. Please try again.",
}) => (
  <EmptyState
    icon={<AlertCircle className="w-12 h-12 text-red-400 dark:text-red-600" />}
    title="Something went wrong"
    description={message}
    action={onRetry ? {
      label: 'Try Again',
      onClick: onRetry,
    } : undefined}
  />
);

// ============================================================================
// EXPORT
// ============================================================================

export default EmptyState;