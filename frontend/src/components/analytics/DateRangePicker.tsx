// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\analytics\DateRangePicker.tsx

/**
 * DateRangePicker Component - Date Range Selection
 * 
 * FAANG++++ Standards:
 * - Preset time periods (7d, 30d, 90d, 1y, all time)
 * - Custom date range selection
 * - Calendar interface
 * - Date validation
 * - Visual feedback
 * - Keyboard navigation
 * - Loading states
 * - Dark mode support
 * 
 * Features:
 * - Quick select presets
 * - Start/end date inputs
 * - Min/max date constraints
 * - Apply/Cancel actions
 * - Selected range display
 * - Relative time display (e.g., "Last 7 days")
 * - Accessible date inputs
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  ChevronDown,
  Check,
  X,
  Clock,
  AlertCircle,
} from 'lucide-react';
import {
  TimePeriod,
  DateRange,
  TIME_PERIOD_LABELS,
  getDateRangeForPeriod,
  formatDateForDisplay,
} from '../../types/analytics.types';

// ============================================================================
// INTERFACES
// ============================================================================

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  onPeriodChange?: (period: TimePeriod) => void;
  minDate?: Date;
  maxDate?: Date;
  disabled?: boolean;
}

// ============================================================================
// PRESET OPTIONS
// ============================================================================

const PRESET_OPTIONS: { value: TimePeriod; label: string; description: string }[] = [
  { value: '7d', label: 'Last 7 days', description: 'Past week' },
  { value: '30d', label: 'Last 30 days', description: 'Past month' },
  { value: '90d', label: 'Last 90 days', description: 'Past quarter' },
  { value: '1y', label: 'Last year', description: 'Past 12 months' },
  { value: 'all', label: 'All time', description: 'Since beginning' },
  { value: 'custom', label: 'Custom range', description: 'Choose dates' },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Format date for input[type="date"]
 */
const formatDateForInput = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Get relative time string
 */
const getRelativeTimeString = (startDate: Date, endDate: Date): string => {
  const now = new Date();
  const diffMs = endDate.getTime() - startDate.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  // Check if end date is today
  const isToday =
    endDate.getDate() === now.getDate() &&
    endDate.getMonth() === now.getMonth() &&
    endDate.getFullYear() === now.getFullYear();

  if (!isToday) {
    return `${formatDateForDisplay(startDate)} - ${formatDateForDisplay(endDate)}`;
  }

  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays <= 7) {
    return `Last ${diffDays} days`;
  } else if (diffDays <= 30) {
    return `Last ${Math.floor(diffDays / 7)} weeks`;
  } else if (diffDays <= 90) {
    return `Last ${Math.floor(diffDays / 30)} months`;
  } else if (diffDays <= 365) {
    return `Last ${Math.floor(diffDays / 30)} months`;
  } else {
    return `Last ${Math.floor(diffDays / 365)} year${Math.floor(diffDays / 365) > 1 ? 's' : ''}`;
  }
};

/**
 * Detect which preset matches the current range
 */
const detectPresetFromRange = (range: DateRange): TimePeriod | null => {
  const presets: TimePeriod[] = ['7d', '30d', '90d', '1y', 'all'];

  for (const preset of presets) {
    const presetRange = getDateRangeForPeriod(preset);
    
    // Check if dates match (within 1 day tolerance)
    const startDiff = Math.abs(range.startDate.getTime() - presetRange.startDate.getTime());
    const endDiff = Math.abs(range.endDate.getTime() - presetRange.endDate.getTime());
    
    const oneDayMs = 24 * 60 * 60 * 1000;
    
    if (startDiff < oneDayMs && endDiff < oneDayMs) {
      return preset;
    }
  }

  return null;
};

// ============================================================================
// COMPONENT
// ============================================================================

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  onPeriodChange,
  minDate,
  maxDate = new Date(),
  disabled = false,
}) => {
  // ============================================================================
  // STATE
  // ============================================================================

  const [isOpen, setIsOpen] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<TimePeriod>(
    detectPresetFromRange(value) || 'custom'
  );
  const [tempStartDate, setTempStartDate] = useState<string>(
    formatDateForInput(value.startDate)
  );
  const [tempEndDate, setTempEndDate] = useState<string>(
    formatDateForInput(value.endDate)
  );
  const [validationError, setValidationError] = useState<string>('');

  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================

  const relativeTimeString = getRelativeTimeString(value.startDate, value.endDate);

  const minDateString = minDate ? formatDateForInput(minDate) : undefined;
  const maxDateString = formatDateForInput(maxDate);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handlePresetSelect = useCallback(
    (preset: TimePeriod) => {
      setSelectedPreset(preset);
      setValidationError('');

      if (preset === 'custom') {
        // Don't auto-apply for custom, wait for user to set dates
        return;
      }

      // Get date range for preset
      const range = getDateRangeForPeriod(preset);
      setTempStartDate(formatDateForInput(range.startDate));
      setTempEndDate(formatDateForInput(range.endDate));

      // Auto-apply preset
      onChange(range);
      if (onPeriodChange) {
        onPeriodChange(preset);
      }
      setIsOpen(false);
    },
    [onChange, onPeriodChange]
  );

  const validateDates = useCallback(
    (startStr: string, endStr: string): string | null => {
      if (!startStr || !endStr) {
        return 'Please select both start and end dates';
      }

      const start = new Date(startStr);
      const end = new Date(endStr);

      // Check if valid dates
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return 'Invalid date format';
      }

      // Check if start is before end
      if (start > end) {
        return 'Start date must be before end date';
      }

      // Check min date
      if (minDate && start < minDate) {
        return `Start date cannot be before ${formatDateForDisplay(minDate)}`;
      }

      // Check max date
      if (end > maxDate) {
        return `End date cannot be after ${formatDateForDisplay(maxDate)}`;
      }

      // Check if range is too long (e.g., more than 2 years)
      const diffMs = end.getTime() - start.getTime();
      const diffDays = diffMs / (1000 * 60 * 60 * 24);
      if (diffDays > 730) {
        return 'Date range cannot exceed 2 years';
      }

      return null;
    },
    [minDate, maxDate]
  );

  const handleApply = useCallback(() => {
    const error = validateDates(tempStartDate, tempEndDate);
    
    if (error) {
      setValidationError(error);
      return;
    }

    const startDate = new Date(tempStartDate);
    const endDate = new Date(tempEndDate);

    onChange({ startDate, endDate });

    // Detect if this matches a preset
    const detectedPreset = detectPresetFromRange({ startDate, endDate });
    if (detectedPreset && onPeriodChange) {
      onPeriodChange(detectedPreset);
    }

    setIsOpen(false);
    setValidationError('');
  }, [tempStartDate, tempEndDate, onChange, onPeriodChange, validateDates]);

  const handleCancel = useCallback(() => {
    // Reset to current values
    setTempStartDate(formatDateForInput(value.startDate));
    setTempEndDate(formatDateForInput(value.endDate));
    setSelectedPreset(detectPresetFromRange(value) || 'custom');
    setValidationError('');
    setIsOpen(false);
  }, [value]);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  // Update temp values when value prop changes
  useEffect(() => {
    setTempStartDate(formatDateForInput(value.startDate));
    setTempEndDate(formatDateForInput(value.endDate));
    setSelectedPreset(detectPresetFromRange(value) || 'custom');
  }, [value]);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors
          ${isOpen
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          bg-white dark:bg-gray-800
        `}
        aria-label="Select date range"
        aria-expanded={isOpen}
      >
        <Calendar className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {relativeTimeString}
        </span>
        <ChevronDown className={`
          w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform
          ${isOpen ? 'transform rotate-180' : ''}
        `} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={handleCancel}
            aria-hidden="true"
          />

          {/* Menu */}
          <div className="absolute right-0 top-full mt-2 w-96 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-20">
            <div className="p-4">
              {/* Presets */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Quick Select
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {PRESET_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => handlePresetSelect(option.value)}
                      className={`
                        p-3 rounded-lg border text-left transition-all
                        ${selectedPreset === option.value
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
                          : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }
                      `}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`
                          text-sm font-medium
                          ${selectedPreset === option.value
                            ? 'text-blue-600 dark:text-blue-400'
                            : 'text-gray-900 dark:text-gray-100'
                          }
                        `}>
                          {option.label}
                        </span>
                        {selectedPreset === option.value && (
                          <Check className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        )}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {option.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Date Inputs */}
              {selectedPreset === 'custom' && (
                <div className="mb-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                    Custom Date Range
                  </h4>

                  <div className="space-y-3">
                    {/* Start Date */}
                    <div>
                      <label
                        htmlFor="start-date"
                        className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        Start Date
                      </label>
                      <input
                        id="start-date"
                        type="date"
                        value={tempStartDate}
                        onChange={(e) => {
                          setTempStartDate(e.target.value);
                          setValidationError('');
                        }}
                        min={minDateString}
                        max={maxDateString}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    {/* End Date */}
                    <div>
                      <label
                        htmlFor="end-date"
                        className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        End Date
                      </label>
                      <input
                        id="end-date"
                        type="date"
                        value={tempEndDate}
                        onChange={(e) => {
                          setTempEndDate(e.target.value);
                          setValidationError('');
                        }}
                        min={minDateString}
                        max={maxDateString}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  {/* Validation Error */}
                  {validationError && (
                    <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                        <span className="text-xs text-red-700 dark:text-red-300">
                          {validationError}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Preview */}
              {selectedPreset === 'custom' && tempStartDate && tempEndDate && !validationError && (
                <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-xs text-blue-900 dark:text-blue-100">
                      <p className="font-medium">Selected Range:</p>
                      <p className="text-blue-700 dark:text-blue-300 mt-0.5">
                        {formatDateForDisplay(new Date(tempStartDate))} -{' '}
                        {formatDateForDisplay(new Date(tempEndDate))}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  <div className="flex items-center justify-center gap-2">
                    <X className="w-4 h-4" />
                    <span>Cancel</span>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={handleApply}
                  disabled={selectedPreset === 'custom' && (!tempStartDate || !tempEndDate)}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors text-sm font-medium disabled:cursor-not-allowed"
                >
                  <div className="flex items-center justify-center gap-2">
                    <Check className="w-4 h-4" />
                    <span>Apply</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ============================================================================
// EXPORT
// ============================================================================

export default DateRangePicker;