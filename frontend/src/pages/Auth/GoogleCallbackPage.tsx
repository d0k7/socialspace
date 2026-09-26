// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\pages\Auth\GoogleCallbackPage.tsx

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Loader2, AlertCircle } from 'lucide-react';

/**
 * GoogleCallbackPage
 *
 * WHY this page exists separately from LoginPage: the backend redirects
 * here with tokens in the URL hash fragment. This page's only job is to
 * read them, hand them to AuthContext exactly like a password login
 * would, and move on, no form, nothing to ask for.
 *
 * WHY window.location.hash, not useSearchParams: tokens are deliberately
 * sent as a # fragment, not a ? query string (see google_auth.py's
 * callback for why), and react-router's useSearchParams only parses the
 * query string, not the fragment.
 */
export const GoogleCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginWithTokens } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const processCallback = async () => {
      const hash = window.location.hash.replace(/^#/, '');
      const params = new URLSearchParams(hash);
      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');

      if (!accessToken || !refreshToken) {
        setError('Google sign-in did not return the expected tokens.');
        return;
      }

      try {
        await loginWithTokens(accessToken, refreshToken);
        navigate('/dashboard', { replace: true });
      } catch (err) {
        console.error('Failed to complete Google sign-in:', err);
        setError('Could not complete sign-in. Please try again.');
      }
    };

    processCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
          <p className="text-gray-900 dark:text-gray-100 font-medium mb-2">Sign-in failed</p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">{error}</p>
          <a href="/login" className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-sm">
            Back to login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Finishing sign-in...</p>
      </div>
    </div>
  );
};

export default GoogleCallbackPage;