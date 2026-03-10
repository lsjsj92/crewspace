import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '@/types';
import { login as apiLogin, getMe, logout as apiLogout } from '@/api/auth';
import { setTokens, clearTokens } from '@/api/client';
import { getAccessToken, getRefreshToken } from '@/utils/token';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const userData = await getMe();
      setUser(userData);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    const tokenResponse = await apiLogin({ email, password });
    setTokens(tokenResponse.access_token, tokenResponse.refresh_token);
    const userData = await getMe();
    setUser(userData);
  };

  const logout = async () => {
    const refreshTokenValue = getRefreshToken();
    if (refreshTokenValue) {
      try {
        await apiLogout(refreshTokenValue);
      } catch {
        // Ignore logout API errors
      }
    }
    clearTokens();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
