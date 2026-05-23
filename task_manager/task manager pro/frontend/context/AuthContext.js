import { createContext, useContext, useEffect, useState } from 'react';
import { apiClient, setTokens, clearTokens, getAccessToken } from '../lib/api';

const AuthContext = createContext({
  user: null,
  isLoading: true,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const accessToken = getAccessToken();
      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      try {
        const me = await apiClient('/api/auth/me');
        setUser(me);
      } catch (error) {
        clearTokens();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    loadUser();
  }, []);

  const login = async ({ username, password }) => {
    const data = await apiClient('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    setTokens(data.access_token, data.refresh_token);
    const me = await apiClient('/api/auth/me');
    setUser(me);
    return me;
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const value = {
    user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
