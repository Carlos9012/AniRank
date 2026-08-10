// context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from "react";
import * as authApi from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      authApi.getMe()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem("token");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(credentials) {
    const data = await authApi.login(credentials);
    localStorage.setItem("token", data.access_token);
    const userData = await authApi.getMe();
    setUser(userData);
    return userData;
  }

  async function register(credentials) {
    await authApi.register(credentials);
    return login(credentials);
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}