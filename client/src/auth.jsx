import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, session } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(session.user);

  // Re-validate a stored session once on load (token may have expired).
  useEffect(() => {
    if (!session.token()) return;
    api('/api/auth/me')
      .then((d) => {
        session.save(session.token(), d.user);
        setUser(d.user);
      })
      .catch((err) => {
        if (err.status === 401) {
          session.clear();
          setUser(null);
        }
      });
  }, []);

  useEffect(() => {
    const onUnauthorized = () => {
      session.clear();
      setUser(null);
    };
    window.addEventListener('aspectlens:unauthorized', onUnauthorized);
    return () => window.removeEventListener('aspectlens:unauthorized', onUnauthorized);
  }, []);

  const authenticate = useCallback(async (path, body) => {
    const data = await api(path, { method: 'POST', body });
    session.save(data.token, data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const value = useMemo(
    () => ({
      user,
      login: (email, password) => authenticate('/api/auth/login', { email, password }),
      register: (fields) => authenticate('/api/auth/register', fields),
      logout: () => {
        session.clear();
        setUser(null);
      },
    }),
    [user, authenticate],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
