/**
 * Main Entry Point
 * 
 * Application bootstrap with:
 * - React Query Provider
 * - Router Provider
 * - Toast Provider
 * - Global Styles
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'
import { queryClient } from '@/lib/query-client'
import App from './App'
import './index.css'

/**
 * Toast Configuration
 */
const toastOptions = {
  duration: 4000,
  position: 'top-right' as const,
  style: {
    background: '#333',
    color: '#fff',
  },
  success: {
    duration: 3000,
    iconTheme: {
      primary: '#10b981',
      secondary: '#fff',
    },
  },
  error: {
    duration: 4000,
    iconTheme: {
      primary: '#ef4444',
      secondary: '#fff',
    },
  },
}

/**
 * Render Application
 */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster toastOptions={toastOptions} />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  </React.StrictMode>
)