import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '@/api/client';

// ============================================================================
// TYPES
// ============================================================================

interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

// ============================================================================
// STORAGE KEYS — single source of truth
// WHY: Prevents key drift across files (was the #1 auth bug before)
// ============================================================================

const KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'auth_user',
} as const;

// ============================================================================
// CONTEXT
// ============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// ============================================================================
// PROVIDER
// ============================================================================

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // --------------------------------------------------------------------------
  // RESTORE SESSION ON LOAD
  // WHY: On app load, check if a valid token exists and restore the user
  // session without forcing re-login. Calls /api/auth/me to verify the
  // token is still valid server-side (not expired, user still active).
  // --------------------------------------------------------------------------
  useEffect(() => {
    const restoreSession = async () => {
      const token = localStorage.getItem(KEYS.ACCESS_TOKEN);

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiClient.get('/api/auth/me');
        setUser(response.data);
      } catch {
        // Token invalid or expired — clear everything cleanly
        localStorage.removeItem(KEYS.ACCESS_TOKEN);
        localStorage.removeItem(KEYS.REFRESH_TOKEN);
        localStorage.removeItem(KEYS.USER);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  // --------------------------------------------------------------------------
  // LOGIN
  // --------------------------------------------------------------------------
  const login = async (email: string, password: string): Promise<void> => {
    const response = await apiClient.post('/api/auth/login', { email, password });
    const { access_token, refresh_token, user: userData } = response.data;

    localStorage.setItem(KEYS.ACCESS_TOKEN, access_token);
    localStorage.setItem(KEYS.REFRESH_TOKEN, refresh_token);
    localStorage.setItem(KEYS.USER, JSON.stringify(userData));

    setUser(userData);
  };

  // --------------------------------------------------------------------------
  // REGISTER
  // --------------------------------------------------------------------------
  const register = async (name: string, email: string, password: string): Promise<void> => {
    const response = await apiClient.post('/api/auth/register', { name, email, password });
    const { access_token, refresh_token, user: userData } = response.data;

    localStorage.setItem(KEYS.ACCESS_TOKEN, access_token);
    localStorage.setItem(KEYS.REFRESH_TOKEN, refresh_token);
    localStorage.setItem(KEYS.USER, JSON.stringify(userData));

    setUser(userData);
  };

  // --------------------------------------------------------------------------
  // LOGOUT
  // WHY async: Calls backend logout endpoint so server can log the event.
  // Clears local state regardless of whether the backend call succeeds —
  // the user must always be able to log out even if the server is down.
  // --------------------------------------------------------------------------
  const logout = async (): Promise<void> => {
    try {
      await apiClient.post('/api/auth/logout');
    } catch {
      // Intentionally swallowed — local logout must always succeed
    } finally {
      localStorage.removeItem(KEYS.ACCESS_TOKEN);
      localStorage.removeItem(KEYS.REFRESH_TOKEN);
      localStorage.removeItem(KEYS.USER);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};