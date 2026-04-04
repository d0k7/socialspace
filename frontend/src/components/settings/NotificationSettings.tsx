// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\settings\NotificationSettings.tsx

/**
 * NotificationSettings Component - Notification Preferences
 * 
 * FAANG++++ Standards:
 * - Email notification toggles
 * - Push notification settings
 * - Per-event notification preferences
 * - Quiet hours configuration
 * - Notification frequency
 * - Sound/vibration preferences
 * - Auto-save
 * - Loading states
 * - Dark mode support
 * 
 * Features:
 * - Email notifications on/off
 * - Push notifications on/off
 * - Event-specific toggles (new follower, mention, like, etc.)
 * - Quiet hours (do not disturb)
 * - Notification batching
 * - Sound settings
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Bell,
  Mail,
  Moon,
  Volume2,
  VolumeX,
  Clock,
  Check,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Smartphone,
  MessageSquare,
  Heart,
  Users,
  TrendingUp,
  Share2,
  AtSign,
  Zap,
} from 'lucide-react';
import api from '../../lib/api';

// ============================================================================
// INTERFACES
// ============================================================================

interface NotificationSettingsProps {
  onSave?: () => void;
}

interface NotificationPreferences {
  emailEnabled: boolean;
  pushEnabled: boolean;
  soundEnabled: boolean;
  
  // Event-specific
  newFollower: boolean;
  newMention: boolean;
  newComment: boolean;
  newLike: boolean;
  newShare: boolean;
  newMessage: boolean;
  postPublished: boolean;
  postScheduled: boolean;
  weeklyReport: boolean;
  monthlyReport: boolean;
  
  // Quiet hours
  quietHoursEnabled: boolean;
  quietHoursStart: string; // HH:MM format
  quietHoursEnd: string; // HH:MM format
  
  // Batching
  batchingEnabled: boolean;
  batchingInterval: 'hourly' | 'daily' | 'realtime';
}

interface NotificationToggleProps {
  icon: React.ReactNode;
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

// ============================================================================
// NOTIFICATION TOGGLE COMPONENT
// ============================================================================

const NotificationToggle: React.FC<NotificationToggleProps> = ({
  icon,
  label,
  description,
  checked,
  onChange,
  disabled = false,
}) => (
  <div className="flex items-center justify-between py-4 border-b border-gray-200 dark:border-gray-700 last:border-0">
    <div className="flex items-start gap-3 flex-1">
      <div className="mt-1 text-gray-600 dark:text-gray-400">
        {icon}
      </div>
      <div className="flex-1">
        <div className="font-medium text-gray-900 dark:text-gray-100">
          {label}
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
          {description}
        </div>
      </div>
    </div>
    
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      disabled={disabled}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors
        ${checked ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white transition-transform
          ${checked ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  </div>
);

// ============================================================================
// COMPONENT
// ============================================================================

export const NotificationSettings: React.FC<NotificationSettingsProps> = ({ onSave }) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    emailEnabled: true,
    pushEnabled: true,
    soundEnabled: true,
    
    newFollower: true,
    newMention: true,
    newComment: true,
    newLike: false,
    newShare: true,
    newMessage: true,
    postPublished: true,
    postScheduled: true,
    weeklyReport: true,
    monthlyReport: true,
    
    quietHoursEnabled: false,
    quietHoursStart: '22:00',
    quietHoursEnd: '08:00',
    
    batchingEnabled: false,
    batchingInterval: 'realtime',
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleToggle = useCallback((field: keyof NotificationPreferences, value: boolean) => {
    setPreferences(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
    setSaveError(null);
  }, []);

  const handleTimeChange = useCallback((field: 'quietHoursStart' | 'quietHoursEnd', value: string) => {
    setPreferences(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
    setSaveError(null);
  }, []);

  const handleBatchingChange = useCallback((value: 'hourly' | 'daily' | 'realtime') => {
    setPreferences(prev => ({ ...prev, batchingInterval: value }));
    setHasChanges(true);
    setSaveError(null);
  }, []);

  // ============================================================================
  // AUTO-SAVE
  // ============================================================================

  useEffect(() => {
    if (!hasChanges) return;

    const timer = setTimeout(() => {
      handleSave();
    }, 2000); // Auto-save after 2 seconds of no changes

    return () => clearTimeout(timer);
  }, [preferences, hasChanges]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);

    try {
      await api.put('/user/notification-preferences', preferences);

      setSaveSuccess(true);
      setHasChanges(false);

      if (onSave) onSave();

      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error: any) {
      console.error('Failed to save notification preferences:', error);
      setSaveError(
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Failed to save preferences'
      );
    } finally {
      setIsSaving(false);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Auto-save Indicator */}
      {(isSaving || saveSuccess) && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            {isSaving ? (
              <>
                <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Saving preferences...
                </span>
              </>
            ) : saveSuccess ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="text-sm text-green-700 dark:text-green-300">
                  Preferences saved automatically
                </span>
              </>
            ) : null}
          </div>
        </div>
      )}

      {/* Error Message */}
      {saveError && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{saveError}</span>
          </div>
        </div>
      )}

      {/* Notification Channels */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Notification Channels
        </h3>

        <div>
          <NotificationToggle
            icon={<Mail className="w-5 h-5" />}
            label="Email Notifications"
            description="Receive notifications via email"
            checked={preferences.emailEnabled}
            onChange={(checked) => handleToggle('emailEnabled', checked)}
          />

          <NotificationToggle
            icon={<Smartphone className="w-5 h-5" />}
            label="Push Notifications"
            description="Receive push notifications in browser and mobile"
            checked={preferences.pushEnabled}
            onChange={(checked) => handleToggle('pushEnabled', checked)}
          />

          <NotificationToggle
            icon={preferences.soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            label="Sound"
            description="Play sound for notifications"
            checked={preferences.soundEnabled}
            onChange={(checked) => handleToggle('soundEnabled', checked)}
          />
        </div>
      </div>

      {/* Event Notifications */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Activity Notifications
        </h3>

        <div>
          <NotificationToggle
            icon={<Users className="w-5 h-5" />}
            label="New Followers"
            description="When someone follows you"
            checked={preferences.newFollower}
            onChange={(checked) => handleToggle('newFollower', checked)}
          />

          <NotificationToggle
            icon={<AtSign className="w-5 h-5" />}
            label="Mentions"
            description="When someone mentions you in a post"
            checked={preferences.newMention}
            onChange={(checked) => handleToggle('newMention', checked)}
          />

          <NotificationToggle
            icon={<MessageSquare className="w-5 h-5" />}
            label="Comments"
            description="When someone comments on your post"
            checked={preferences.newComment}
            onChange={(checked) => handleToggle('newComment', checked)}
          />

          <NotificationToggle
            icon={<Heart className="w-5 h-5" />}
            label="Likes"
            description="When someone likes your post"
            checked={preferences.newLike}
            onChange={(checked) => handleToggle('newLike', checked)}
          />

          <NotificationToggle
            icon={<Share2 className="w-5 h-5" />}
            label="Shares"
            description="When someone shares your post"
            checked={preferences.newShare}
            onChange={(checked) => handleToggle('newShare', checked)}
          />

          <NotificationToggle
            icon={<Mail className="w-5 h-5" />}
            label="Direct Messages"
            description="When you receive a new message"
            checked={preferences.newMessage}
            onChange={(checked) => handleToggle('newMessage', checked)}
          />
        </div>
      </div>

      {/* Post Notifications */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Post Updates
        </h3>

        <div>
          <NotificationToggle
            icon={<Zap className="w-5 h-5" />}
            label="Post Published"
            description="When your scheduled post is published"
            checked={preferences.postPublished}
            onChange={(checked) => handleToggle('postPublished', checked)}
          />

          <NotificationToggle
            icon={<Clock className="w-5 h-5" />}
            label="Post Scheduled"
            description="Confirmation when a post is scheduled"
            checked={preferences.postScheduled}
            onChange={(checked) => handleToggle('postScheduled', checked)}
          />
        </div>
      </div>

      {/* Reports */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Reports
        </h3>

        <div>
          <NotificationToggle
            icon={<TrendingUp className="w-5 h-5" />}
            label="Weekly Report"
            description="Summary of your weekly performance"
            checked={preferences.weeklyReport}
            onChange={(checked) => handleToggle('weeklyReport', checked)}
          />

          <NotificationToggle
            icon={<TrendingUp className="w-5 h-5" />}
            label="Monthly Report"
            description="Summary of your monthly performance"
            checked={preferences.monthlyReport}
            onChange={(checked) => handleToggle('monthlyReport', checked)}
          />
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Quiet Hours
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Pause notifications during specific hours
            </p>
          </div>
          
          <button
            type="button"
            role="switch"
            aria-checked={preferences.quietHoursEnabled}
            onClick={() => handleToggle('quietHoursEnabled', !preferences.quietHoursEnabled)}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition-colors
              ${preferences.quietHoursEnabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                ${preferences.quietHoursEnabled ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>

        {preferences.quietHoursEnabled && (
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <div className="flex items-center gap-2">
                  <Moon className="w-4 h-4" />
                  <span>Start Time</span>
                </div>
              </label>
              <input
                type="time"
                value={preferences.quietHoursStart}
                onChange={(e) => handleTimeChange('quietHoursStart', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <div className="flex items-center gap-2">
                  <Moon className="w-4 h-4" />
                  <span>End Time</span>
                </div>
              </label>
              <input
                type="time"
                value={preferences.quietHoursEnd}
                onChange={(e) => handleTimeChange('quietHoursEnd', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Notification Batching */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Notification Batching
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Group notifications to reduce interruptions
            </p>
          </div>
          
          <button
            type="button"
            role="switch"
            aria-checked={preferences.batchingEnabled}
            onClick={() => handleToggle('batchingEnabled', !preferences.batchingEnabled)}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition-colors
              ${preferences.batchingEnabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                ${preferences.batchingEnabled ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>

        {preferences.batchingEnabled && (
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Notification Frequency
            </label>
            <div className="space-y-2">
              {[
                { value: 'realtime' as const, label: 'Real-time', description: 'Send immediately' },
                { value: 'hourly' as const, label: 'Hourly', description: 'Send every hour' },
                { value: 'daily' as const, label: 'Daily', description: 'Send once per day at 9 AM' },
              ].map((option) => (
                <label
                  key={option.value}
                  className={`
                    flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all
                    ${preferences.batchingInterval === option.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }
                  `}
                >
                  <input
                    type="radio"
                    name="batchingInterval"
                    value={option.value}
                    checked={preferences.batchingInterval === option.value}
                    onChange={() => handleBatchingChange(option.value)}
                    className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {option.label}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {option.description}
                    </div>
                  </div>
                  {preferences.batchingInterval === option.value && (
                    <Check className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  )}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Bell className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900 dark:text-blue-100">
            <p className="font-medium">💡 Pro Tip</p>
            <p className="text-blue-700 dark:text-blue-300 mt-1">
              Enable quiet hours and notification batching to reduce distractions while staying informed.
              Changes are saved automatically.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default NotificationSettings;