import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.warn('Local storage access blocked by browser settings');
      return null;
    }
  });
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    try {
      const res = await authAPI.login({ username, password });
      const { access_token, user: userData } = res.data.data;
      try {
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user', JSON.stringify(userData));
      } catch (e) {
        console.warn('Could not save to local storage');
      }
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authAPI.logout();
    } catch {
      // Logout endpoint may fail if token is expired — that's fine
    } finally {
      try {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('hasPromptedHighRisk');
      } catch (e) {}
      setUser(null);
    }
  }, []);

  const isAuthenticated = !!user;
  const hasRole = useCallback((role) => user?.role === role, [user]);

  const value = {
    user,
    loading,
    isAuthenticated,
    hasRole,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
