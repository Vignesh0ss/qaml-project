import React, { createContext, useContext, useState, useEffect } from "react";
import { login as apiLogin, register as apiRegister, LoginPayload, RegisterPayload } from "../services/api";

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("qaml_token");
    const savedUser = localStorage.getItem("qaml_user");
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (payload: LoginPayload) => {
    const data = await apiLogin(payload);
    const userData = { username: data.username || payload.username || payload.email || "User" };
    setToken(data.access_token);
    setUser(userData);
    localStorage.setItem("qaml_token", data.access_token);
    localStorage.setItem("qaml_user", JSON.stringify(userData));
  };

  const register = async (payload: RegisterPayload) => {
    const data = await apiRegister(payload);
    const userData = { username: payload.username };
    setToken(data.access_token);
    setUser(userData);
    localStorage.setItem("qaml_token", data.access_token);
    localStorage.setItem("qaml_user", JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("qaml_token");
    localStorage.removeItem("qaml_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
