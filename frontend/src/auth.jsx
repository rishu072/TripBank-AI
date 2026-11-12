import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "./api";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function applyTheme(t) {
  const dark = t === "dark" || (t !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem("tb_token"));

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/users/me");
      setUser(data);
      applyTheme(data.theme);
    } catch {
      localStorage.removeItem("tb_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (localStorage.getItem("tb_token")) load();
    else applyTheme("system");
  }, [load]);

  const sign = async (path, body) => {
    const { data } = await api.post(path, body);
    localStorage.setItem("tb_token", data.access_token);
    setUser(data.user);
    applyTheme(data.user.theme);
  };

  const value = {
    user,
    loading,
    setUser,
    login: (b) => sign("/auth/login", b),
    register: (b) => sign("/auth/register", b),
    logout: () => {
      localStorage.removeItem("tb_token");
      setUser(null);
    },
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
