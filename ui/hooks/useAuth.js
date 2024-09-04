// hooks/useAuth.js

import { useState, useEffect } from 'react';
import { getAuthToken, setAuthToken, removeAuthToken } from '../utils/auth';

export const useAuth = () => {
  const [token, setToken] = useState(null);

  useEffect(() => {
    const fetchToken = async () => {
      const storedToken = await getAuthToken();
      setToken(storedToken);
    };
    fetchToken();
  }, []);

  const signIn = async (newToken) => {
    await setAuthToken(newToken);
    setToken(newToken);
  };

  const signOut = async () => {
    await removeAuthToken();
    setToken(null);
  };

  return {
    token,
    signIn,
    signOut,
  };
};
