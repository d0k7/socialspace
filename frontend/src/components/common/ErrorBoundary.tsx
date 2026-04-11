// File: C:\Users\dheer\Downloads\socialspace-workspace\socialspace\frontend\src\components\common\ErrorBoundary.tsx

/**
 * ErrorBoundary - Graceful Error Handling
 * 
 * Catches React errors and displays fallback UI instead of crashing
 */

import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(_error: Error): Partial<State> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 bg-red-100 dark:bg-red-900/30 rounded-full">
                <AlertTriangle className="w-12 h-12 text-red-600 dark:text-red-400" />
              </div>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Oops! Something went wrong
            </h2>

            <p className="text-gray-600 dark:text-gray-400 mb-6">
              We're sorry for the inconvenience. The page encountered an error and couldn't load properly.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-900 rounded-lg text-left overflow-auto max-h-40">
                <p className="text-xs font-mono text-red-600 dark:text-red-400 mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <button
                type="button"
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>

              <a
                href="/"
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300 font-medium"
              >
                <Home className="w-4 h-4" />
                <span>Go Home</span>
              </a>
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-500 mt-6">
              If the problem persists, please contact support.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
