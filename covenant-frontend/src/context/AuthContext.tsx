import React, { createContext, useContext, useEffect, useState } from "react";
import * as api from "../lib/api";
import type { User } from "../lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("covenant_user");
    if (stored) setUser(JSON.parse(stored));
    setLoading(false);
  }, []);

  const persist = (token: string, u: User) => {
    localStorage.setItem("covenant_token", token);
    localStorage.setItem("covenant_user", JSON.stringify(u));
    setUser(u);
  };

  const login = async (email: string, password: string) => {
    const { access_token, user } = await api.login(email, password);
    persist(access_token, user);
  };

  const register = async (email: string, password: string, fullName: string) => {
    const { access_token, user } = await api.register(email, password, fullName);
    persist(access_token, user);
  };

  const logout = () => {
    localStorage.removeItem("covenant_token");
    localStorage.removeItem("covenant_user");
    setUser(null);
  };

  // Called after a profile update so the sidebar/UI reflect the new
  // details immediately without requiring a re-login.
  const updateUser = (updated: User) => {
    localStorage.setItem("covenant_user", JSON.stringify(updated));
    setUser(updated);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
