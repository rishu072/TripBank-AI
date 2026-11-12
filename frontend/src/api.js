import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1" });

api.interceptors.request.use((c) => {
  const t = localStorage.getItem("tb_token");
  if (t) c.headers.Authorization = `Bearer ${t}`;
  return c;
});

api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401 && !String(e.config?.url).startsWith("/auth/")) {
      localStorage.removeItem("tb_token");
      location.assign("/login");
    }
    return Promise.reject(e);
  }
);

export const errOf = (e) => ({
  code: e.response?.data?.error?.code || "NETWORK_ERROR",
  message: e.response?.data?.error?.message || "Network error. Check your connection and try again.",
});

export default api;
