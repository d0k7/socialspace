// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\settings\DangerZone.tsx

/**
 * DangerZone Component - Critical Account Actions
 * 
 * FAANG++++ Standards:
 * - Export all data (GDPR compliance)
 * - Delete account with multi-step confirmation
 * - Clear cache/data
 * - Revoke all sessions
 * - Security warnings
 * - Password confirmation
 * - Irreversible action protection
 * - Loading states
 * - Dark mode support
 * 
 * Features:
 * - Export data as JSON/ZIP
 * - Delete account with confirmation modal
 * - Password verification
 * - Warning messages
 * - Backup reminders
 * - GDPR-compliant data export
 */

import React, { useState } from 'react';
import {
  Download,
  Trash2,
  AlertTriangle,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Database,
  FileArchive,
  LogOut,
  RefreshCw,
} from 'lucide-react';
import api from '../../lib/api';

// ============================================================================
// INTERFACES
// ============================================================================

interface DangerZoneProps {
  onAccountDeleted?: () => void;
}

interface ExportData {
  format: 'json' | 'zip';
  includeMedia: boolean;
  includePosts: boolean;
  includeAnalytics: boolean;
  includeMessages: boolean;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const DangerZone: React.FC<DangerZoneProps> = ({ onAccountDeleted }) => {
  // ============================================================================
  // STATE
  // ============================================================================

  // Export data
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportData, setExportData] = useState<ExportData>({
    format: 'json',
    includeMedia: true,
    includePosts: true,
    includeAnalytics: true,
    includeMessages: true,
  });
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  // Delete account
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteStep, setDeleteStep] = useState<1 | 2 | 3>(1);
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeletePassword, setShowDeletePassword] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Clear cache
  const [isClearing, setIsClearing] = useState(false);

  // Revoke sessions
  const [isRevoking, setIsRevoking] = useState(false);

  // ============================================================================
  // EXPORT HANDLERS
  // ============================================================================

  const handleExport = async () => {
    setIsExporting(true);

    try {
      const response = await api.post('/user/export-data', exportData);
      const { downloadUrl } = response.data;

      // Trigger download
      window.open(downloadUrl, '_blank');

      setExportSuccess(true);
      setTimeout(() => {
        setExportSuccess(false);
        setShowExportModal(false);
      }, 2000);
    } catch (error: any) {
      console.error('Export failed:', error);
      alert('Failed to export data. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // ============================================================================
  // DELETE ACCOUNT HANDLERS
  // ============================================================================

  const handleDeleteAccount = async () => {
    if (deleteStep === 1) {
      // Move to password confirmation
      setDeleteStep(2);
      return;
    }

    if (deleteStep === 2) {
      // Verify password
      if (!deletePassword) {
        setDeleteError('Please enter your password');
        return;
      }

      // Move to final confirmation
      setDeleteStep(3);
      setDeleteError(null);
      return;
    }

    if (deleteStep === 3) {
      // Final confirmation
      if (deleteConfirmText !== 'DELETE') {
        setDeleteError('Please type DELETE to confirm');
        return;
      }

      setIsDeleting(true);
      setDeleteError(null);

      try {
        await api.post('/user/delete-account', {
          password: deletePassword,
        });

        // Account deleted successfully
        alert('Your account has been deleted. We\'re sorry to see you go!');
        
        // Clear local storage
        localStorage.clear();
        
        // Redirect to homepage or login
        if (onAccountDeleted) {
          onAccountDeleted();
        } else {
          window.location.href = '/';
        }
      } catch (error: any) {
        console.error('Delete account failed:', error);
        setDeleteError(
          error.response?.data?.detail ||
          error.response?.data?.message ||
          'Failed to delete account. Please check your password and try again.'
        );
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteModal(false);
    setDeleteStep(1);
    setDeletePassword('');
    setDeleteConfirmText('');
    setDeleteError(null);
  };

  // ============================================================================
  // CLEAR CACHE HANDLER
  // ============================================================================

  const handleClearCache = async () => {
    if (!confirm('This will clear all cached data. Continue?')) {
      return;
    }

    setIsClearing(true);

    try {
      // Clear localStorage (except auth tokens)
      const authToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      localStorage.clear();
      
      if (authToken) localStorage.setItem('access_token', authToken);
      if (refreshToken) localStorage.setItem('refresh_token', refreshToken);

      // Clear API cache
      await api.post('/user/clear-cache');

      alert('Cache cleared successfully!');
    } catch (error) {
      console.error('Clear cache failed:', error);
      alert('Failed to clear cache. Please try again.');
    } finally {
      setIsClearing(false);
    }
  };

  // ============================================================================
  // REVOKE SESSIONS HANDLER
  // ============================================================================

  const handleRevokeSessions = async () => {
    if (!confirm('This will log you out from all devices. Continue?')) {
      return;
    }

    setIsRevoking(true);

    try {
      await api.post('/user/revoke-sessions');

      alert('All sessions revoked. You will be logged out.');
      
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    } catch (error) {
      console.error('Revoke sessions failed:', error);
      alert('Failed to revoke sessions. Please try again.');
    } finally {
      setIsRevoking(false);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Warning Banner */}
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <ShieldAlert className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-1">
              Danger Zone
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300">
              These actions are irreversible. Please proceed with caution and ensure you have
              backups of any important data before continuing.
            </p>
          </div>
        </div>
      </div>

      {/* Export Data */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Download className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Export Your Data
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Download all your data including posts, analytics, and media files. GDPR compliant.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowExportModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            Export Data
          </button>
        </div>
      </div>

      {/* Clear Cache */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
              <Database className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Clear Cache
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Clear all cached data to free up space. This won't delete your posts or settings.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClearCache}
            disabled={isClearing}
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
          >
            {isClearing ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Clearing...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4" />
                <span>Clear Cache</span>
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Revoke All Sessions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <LogOut className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Revoke All Sessions
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Log out from all devices and browsers. You'll need to log in again on this device.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRevokeSessions}
            disabled={isRevoking}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
          >
            {isRevoking ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Revoking...</span>
              </div>
            ) : (
              'Revoke All'
            )}
          </button>
        </div>
      </div>

      {/* Delete Account */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border-2 border-red-500 dark:border-red-400 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <Trash2 className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h4 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-1">
                Delete Account
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <div className="flex items-start gap-2 text-xs text-red-600 dark:text-red-400">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>
                  This will delete all your posts, analytics, settings, and cancel your subscription.
                  Consider exporting your data first.
                </span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
          >
            Delete Account
          </button>
        </div>
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-lg w-full">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Export Your Data
              </h3>
            </div>

            <div className="p-6">
              {/* Format Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Export Format
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setExportData(prev => ({ ...prev, format: 'json' }))}
                    className={`
                      p-4 rounded-lg border-2 transition-all
                      ${exportData.format === 'json'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700'
                      }
                    `}
                  >
                    <FileArchive className="w-6 h-6 mx-auto mb-2 text-gray-600 dark:text-gray-400" />
                    <div className="font-medium text-gray-900 dark:text-gray-100">JSON</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Structured data</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setExportData(prev => ({ ...prev, format: 'zip' }))}
                    className={`
                      p-4 rounded-lg border-2 transition-all
                      ${exportData.format === 'zip'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700'
                      }
                    `}
                  >
                    <FileArchive className="w-6 h-6 mx-auto mb-2 text-gray-600 dark:text-gray-400" />
                    <div className="font-medium text-gray-900 dark:text-gray-100">ZIP</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">With media files</div>
                  </button>
                </div>
              </div>

              {/* Include Options */}
              <div className="space-y-3 mb-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={exportData.includePosts}
                    onChange={(e) => setExportData(prev => ({ ...prev, includePosts: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Include posts</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={exportData.includeAnalytics}
                    onChange={(e) => setExportData(prev => ({ ...prev, includeAnalytics: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Include analytics</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={exportData.includeMessages}
                    onChange={(e) => setExportData(prev => ({ ...prev, includeMessages: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Include messages</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={exportData.includeMedia}
                    onChange={(e) => setExportData(prev => ({ ...prev, includeMedia: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Include media files</span>
                </label>
              </div>

              {exportSuccess && (
                <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-300">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Export started! Download will begin shortly.</span>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowExportModal(false)}
                  disabled={isExporting}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleExport}
                  disabled={isExporting}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
                >
                  {isExporting ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Exporting...</span>
                    </div>
                  ) : (
                    'Export Data'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-lg w-full">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <h3 className="text-xl font-bold text-red-600 dark:text-red-400">
                  Delete Account
                </h3>
              </div>
            </div>

            <div className="p-6">
              {/* Step 1: Warning */}
              {deleteStep === 1 && (
                <div>
                  <p className="text-gray-700 dark:text-gray-300 mb-4">
                    Are you sure you want to delete your account? This action is permanent and cannot be undone.
                  </p>
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
                    <p className="text-sm text-red-700 dark:text-red-300 font-medium mb-2">
                      This will permanently delete:
                    </p>
                    <ul className="text-sm text-red-600 dark:text-red-400 space-y-1 list-disc list-inside">
                      <li>All your posts and content</li>
                      <li>All analytics and insights</li>
                      <li>All media files</li>
                      <li>All connected platforms</li>
                      <li>Your subscription (non-refundable)</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Step 2: Password Confirmation */}
              {deleteStep === 2 && (
                <div>
                  <p className="text-gray-700 dark:text-gray-300 mb-4">
                    Please enter your password to continue.
                  </p>
                  <div className="relative mb-4">
                    <input
                      type={showDeletePassword ? 'text' : 'password'}
                      value={deletePassword}
                      onChange={(e) => {
                        setDeletePassword(e.target.value);
                        setDeleteError(null);
                      }}
                      placeholder="Enter your password"
                      className="w-full px-4 py-2 pr-12 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowDeletePassword(!showDeletePassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                    >
                      {showDeletePassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
              )}

              {/* Step 3: Final Confirmation */}
              {deleteStep === 3 && (
                <div>
                  <p className="text-gray-700 dark:text-gray-300 mb-4">
                    This is your last chance. Type <strong className="text-red-600 dark:text-red-400">DELETE</strong> to confirm account deletion.
                  </p>
                  <input
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => {
                      setDeleteConfirmText(e.target.value);
                      setDeleteError(null);
                    }}
                    placeholder="Type DELETE"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500 mb-4"
                  />
                </div>
              )}

              {/* Error Message */}
              {deleteError && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-red-700 dark:text-red-300">
                    <AlertCircle className="w-4 h-4" />
                    <span>{deleteError}</span>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleCancelDelete}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDeleteAccount}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
                >
                  {isDeleting ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Deleting...</span>
                    </div>
                  ) : (
                    deleteStep === 3 ? 'Delete Forever' : 'Continue'
                  )}
                </button>
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

export default DangerZone;
