import { useCallback, useEffect, useState } from "react";
import api, { errOf } from "./api";

export function useFetch(url, params) {
  const [s, set] = useState({ data: null, error: null, loading: true });
  const key = url + JSON.stringify(params || {});
  const load = useCallback(async () => {
    set((p) => ({ ...p, loading: true }));
    try {
      const { data } = await api.get(url, { params });
      set({ data, error: null, loading: false });
    } catch (e) {
      set({ data: null, error: errOf(e), loading: false });
    }
  }, [key]);
  useEffect(() => {
    load();
  }, [load]);
  return { ...s, reload: load };
}
