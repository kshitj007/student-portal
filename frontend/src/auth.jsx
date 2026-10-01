import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiMe, getToken, setToken } from './api.js';

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) { setReady(true); return; }
    apiMe().then((d) => setUser(d.user)).catch(() => setToken(null)).finally(() => setReady(true));
  }, []);

  const login = (token, u) => { setToken(token); setUser(u); };
  const logout = () => { setToken(null); setUser(null); };

  if (!ready) return <div className="page"><p className="muted">Loading portal…</p></div>;
  return <Ctx.Provider value={{ user, login, logout }}>{children}</Ctx.Provider>;
}
