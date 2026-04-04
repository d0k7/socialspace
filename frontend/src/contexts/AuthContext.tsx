import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('demo_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    console.log('DEMO MODE: Logging in with', email);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const demoUser: User = {
      id: 'demo-123',
      email: email,
      name: email.split('@')[0],
    };
    
    localStorage.setItem('access_token', 'demo-token');
    localStorage.setItem('demo_user', JSON.stringify(demoUser));
    setUser(demoUser);
  };

  const register = async (name: string, email: string, password: string) => {
    console.log('DEMO MODE: Registering user', name, email);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const demoUser: User = {
      id: 'demo-123',
      email: email,
      name: name,
    };
    
    localStorage.setItem('access_token', 'demo-token');
    localStorage.setItem('demo_user', JSON.stringify(demoUser));
    setUser(demoUser);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('demo_user');
    setUser(null);
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};