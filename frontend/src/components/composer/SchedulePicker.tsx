// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\composer\SchedulePicker.tsx

/**
 * SchedulePicker Component - Date/Time Scheduling
 * 
 * FAANG++++ Standards:
 * - Date and time selection
 * - Timezone support
 * - "Post Now" vs "Schedule" toggle
 * - Validation (prevent past dates)
 * - Timezone-aware calculations
 * - User-friendly time display
 * - Accessibility compliant
 * 
 * Features:
 * - Toggle between immediate and scheduled posting
 * - Date picker with calendar
 * - Time picker with 15-minute intervals
 * - Timezone selector with major zones
 * - Validation messages
 * - Preview of scheduled time in user's timezone
 * - Quick select buttons (1 hour, 3 hours, tomorrow, etc.)
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Calendar,
  Clock,
  Globe,
  AlertCircle,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { TIMEZONES } from '../../types/composer.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface SchedulePickerProps {
  scheduleType: 'now' | 'scheduled';
  scheduledFor?: Date;
  timezone?: string;
  onScheduleTypeChange: (type: 'now' | 'scheduled') => void;
  onScheduledForChange: (date: Date | undefined) => void;
  onTimezoneChange: (timezone: string) => void;
  disabled?: boolean;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Format date for datetime-local input
 */
const formatDateTimeLocal = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

/**
 * Get minimum datetime (now + 5 minutes)
 */
const getMinDateTime = (): string => {
  const now = new Date();
  now.setMinutes(now.getMinutes() + 5);
  return formatDateTimeLocal(now);
};

/**
 * Round time to nearest 15 minutes
 */
const roundToNearest15Minutes = (date: Date): Date => {
  const rounded = new Date(date);
  const minutes = rounded.getMinutes();
  const roundedMinutes = Math.ceil(minutes / 15) * 15;
  rounded.setMinutes(roundedMinutes);
  rounded.setSeconds(0);
  rounded.setMilliseconds(0);
  return rounded;
};

/**
 * Format time for display
 */
const formatTimeDisplay = (date: Date, timezone: string): string => {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'full',
    timeStyle: 'short',
    timeZone: timezone,
  }).format(date);
};

/**
 * Get relative time string
 */
const getRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) {
    return `in ${diffMins} minute${diffMins !== 1 ? 's' : ''}`;
  } else if (diffHours < 24) {
    return `in ${diffHours} hour${diffHours !== 1 ? 's' : ''}`;
  } else if (diffDays < 7) {
    return `in ${diffDays} day${diffDays !== 1 ? 's' : ''}`;
  } else {
    return formatTimeDisplay(date, Intl.DateTimeFormat().resolvedOptions().timeZone);
  }
};

// ============================================================================
// QUICK SELECT OPTIONS
// ============================================================================

const getQuickSelectOptions = () => {
  const now = new Date();
  
  return [
    {
      label: '1 hour',
      getValue: () => {
        const date = new Date(now);
        date.setHours(date.getHours() + 1);
        return roundToNearest15Minutes(date);
      },
    },
    {
      label: '3 hours',
      getValue: () => {
        const date = new Date(now);
        date.setHours(date.getHours() + 3);
        return roundToNearest15Minutes(date);
      },
    },
    {
      label: 'Tomorrow 9 AM',
      getValue: () => {
        const date = new Date(now);
        date.setDate(date.getDate() + 1);
        date.setHours(9, 0, 0, 0);
        return date;
      },
    },
    {
      label: 'Next Monday 9 AM',
      getValue: () => {
        const date = new Date(now);
        const daysUntilMonday = (8 - date.getDay()) % 7 || 7;
        date.setDate(date.getDate() + daysUntilMonday);
        date.setHours(9, 0, 0, 0);
        return date;
      },
    },
  ];
};

// ============================================================================
// COMPONENT
// ============================================================================

export const SchedulePicker: React.FC<SchedulePickerProps> = ({
  scheduleType,
  scheduledFor,
  timezone = Intl.DateTimeFormat().resolvedOptions().timeZone,
  onScheduleTypeChange,
  onScheduledForChange,
  onTimezoneChange,
  disabled = false,
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [localDateTime, setLocalDateTime] = useState<string>(() => {
    if (scheduledFor) {
      return formatDateTimeLocal(scheduledFor);
    }
    const defaultDate = new Date();
    defaultDate.setHours(defaultDate.getHours() + 1);
    return formatDateTimeLocal(roundToNearest15Minutes(defaultDate));
  });

  const [validationError, setValidationError] = useState<string>('');

  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================

  const minDateTime = useMemo(() => getMinDateTime(), []);
  const quickSelectOptions = useMemo(() => getQuickSelectOptions(), []);

  const selectedDate = useMemo(() => {
    if (!scheduledFor) return null;
    return scheduledFor;
  }, [scheduledFor]);

  const relativeTime = useMemo(() => {
    if (!selectedDate) return '';
    return getRelativeTime(selectedDate);
  }, [selectedDate]);

  const formattedTime = useMemo(() => {
    if (!selectedDate) return '';
    return formatTimeDisplay(selectedDate, timezone);
  }, [selectedDate, timezone]);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleScheduleTypeChange = useCallback(
    (type: 'now' | 'scheduled') => {
      onScheduleTypeChange(type);
      setValidationError('');

      if (type === 'now') {
        onScheduledForChange(undefined);
      } else {
        // Set default scheduled time (1 hour from now)
        const defaultDate = new Date();
        defaultDate.setHours(defaultDate.getHours() + 1);
        const roundedDate = roundToNearest15Minutes(defaultDate);
        onScheduledForChange(roundedDate);
        setLocalDateTime(formatDateTimeLocal(roundedDate));
      }
    },
    [onScheduleTypeChange, onScheduledForChange]
  );

  const handleDateTimeChange = useCallback(
    (value: string) => {
      setLocalDateTime(value);

      if (!value) {
        setValidationError('Please select a date and time');
        return;
      }

      const selectedDate = new Date(value);
      const now = new Date();

      // Validate: must be in future (at least 5 minutes)
      if (selectedDate <= new Date(now.getTime() + 5 * 60000)) {
        setValidationError('Please select a time at least 5 minutes in the future');
        return;
      }

      // Validate: not more than 1 year in future
      const oneYearFromNow = new Date(now);
      oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1);
      if (selectedDate > oneYearFromNow) {
        setValidationError('Cannot schedule more than 1 year in advance');
        return;
      }

      setValidationError('');
      onScheduledForChange(selectedDate);
    },
    [onScheduledForChange]
  );

  const handleTimezoneChange = useCallback(
    (value: string) => {
      onTimezoneChange(value);
    },
    [onTimezoneChange]
  );

  const handleQuickSelect = useCallback(
    (option: { label: string; getValue: () => Date }) => {
      const date = option.getValue();
      setLocalDateTime(formatDateTimeLocal(date));
      onScheduledForChange(date);
      setValidationError('');
    },
    [onScheduledForChange]
  );

  // ============================================================================
  // EFFECTS
  // ============================================================================

  // Sync local state when scheduledFor prop changes
  useEffect(() => {
    if (scheduledFor && scheduleType === 'scheduled') {
      setLocalDateTime(formatDateTimeLocal(scheduledFor));
    }
  }, [scheduledFor, scheduleType]);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="w-full">
      {/* Schedule Type Toggle */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          When to publish?
        </h3>

        <div className="grid grid-cols-2 gap-3">
          {/* Post Now */}
          <button
            type="button"
            onClick={() => handleScheduleTypeChange('now')}
            disabled={disabled}
            className={`
              p-4 rounded-lg border-2 transition-all text-left
              ${scheduleType === 'now'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            aria-pressed={scheduleType === 'now'}
          >
            <div className="flex items-center gap-3">
              <div className={`
                p-2 rounded-full
                ${scheduleType === 'now' 
                  ? 'bg-blue-100 dark:bg-blue-800' 
                  : 'bg-gray-100 dark:bg-gray-700'
                }
              `}>
                <Zap className={`w-5 h-5 ${scheduleType === 'now' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}`} />
              </div>
              <div>
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  Post Now
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                  Publish immediately
                </div>
              </div>
            </div>
          </button>

          {/* Schedule */}
          <button
            type="button"
            onClick={() => handleScheduleTypeChange('scheduled')}
            disabled={disabled}
            className={`
              p-4 rounded-lg border-2 transition-all text-left
              ${scheduleType === 'scheduled'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            aria-pressed={scheduleType === 'scheduled'}
          >
            <div className="flex items-center gap-3">
              <div className={`
                p-2 rounded-full
                ${scheduleType === 'scheduled' 
                  ? 'bg-blue-100 dark:bg-blue-800' 
                  : 'bg-gray-100 dark:bg-gray-700'
                }
              `}>
                <Calendar className={`w-5 h-5 ${scheduleType === 'scheduled' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}`} />
              </div>
              <div>
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  Schedule
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                  Choose date & time
                </div>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Scheduled Options */}
      {scheduleType === 'scheduled' && (
        <div className="space-y-4">
          {/* Quick Select Buttons */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quick Select
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {quickSelectOptions.map((option, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleQuickSelect(option)}
                  disabled={disabled}
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date & Time Picker */}
          <div>
            <label
              htmlFor="datetime-picker"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Date & Time</span>
              </div>
            </label>
            <input
              id="datetime-picker"
              type="datetime-local"
              value={localDateTime}
              onChange={(e) => handleDateTimeChange(e.target.value)}
              min={minDateTime}
              disabled={disabled}
              className={`
                w-full px-4 py-3 rounded-lg border
                ${validationError 
                  ? 'border-red-500 dark:border-red-400' 
                  : 'border-gray-300 dark:border-gray-600'
                }
                bg-white dark:bg-gray-800
                text-gray-900 dark:text-gray-100
                focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              aria-invalid={!!validationError}
              aria-describedby={validationError ? 'datetime-error' : undefined}
            />
            {validationError && (
              <div
                id="datetime-error"
                className="mt-2 flex items-center gap-2 text-sm text-red-600 dark:text-red-400"
                role="alert"
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          {/* Timezone Selector */}
          <div>
            <label
              htmlFor="timezone-selector"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4" />
                <span>Timezone</span>
              </div>
            </label>
            <select
              id="timezone-selector"
              value={timezone}
              onChange={(e) => handleTimezoneChange(e.target.value)}
              disabled={disabled}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
          </div>

          {/* Scheduled Time Preview */}
          {selectedDate && !validationError && (
            <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-green-900 dark:text-green-100">
                    Scheduled for:
                  </div>
                  <div className="text-sm text-green-700 dark:text-green-300 mt-1">
                    {formattedTime}
                  </div>
                  <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                    {relativeTime}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Help Text */}
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <p>
              💡 <strong>Tip:</strong> Schedule posts during peak engagement times
              for better reach. Most platforms see highest activity between 9 AM - 12 PM
              and 6 PM - 9 PM in your audience's timezone.
            </p>
          </div>
        </div>
      )}

      {/* Post Now Info */}
      {scheduleType === 'now' && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <p className="font-medium">Your post will be published immediately</p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                The post will appear on selected platforms within a few seconds
              </p>
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

export default SchedulePicker;