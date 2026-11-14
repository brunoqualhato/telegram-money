import { useState, useEffect, useCallback } from "react";
import { api } from "../services/api.js";

export default function usePanelData({ page, setError, setSearch, setFilter }) {
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({ assets: [] });
  const [items, setItems] = useState([]);
  const [integrations, setIntegrations] = useState(null);
  const authenticated = Boolean(me);
  const reload = useCallback(async () => {
    const [owner, overview] = await Promise.all([api("/me"), api("/overview")]);
    setMe(owner);
    setData(overview);
  }, []);
  const loadPage = useCallback(
    async (signal) => {
      const paths = {
        alerts: "/rules",
        events: "/events",
        documents: "/documents",
        reports: "/reports",
        history: "/notifications",
        treasury: "/treasury",
      };
      if (paths[page]) setItems(await api(paths[page], { signal }));
      if (page === "settings")
        setIntegrations(await api("/integrations", { signal }));
    },
    [page],
  );
  useEffect(() => {
    reload()
      .catch((error) => {
        if (error.status !== 401) setError(error.message);
      })
      .finally(() => setLoading(false));
  }, [reload, setError]);
  useEffect(() => {
    if (!authenticated) return;
    const controller = new AbortController();
    setError("");
    setItems([]);
    setSearch("");
    setFilter("all");
    if (page === "settings") setIntegrations(null);
    loadPage(controller.signal).catch((error) => {
      if (error.name !== "AbortError") setError(error.message);
    });
    return () => controller.abort();
  }, [page, authenticated, loadPage, setError, setSearch, setFilter]);
  useEffect(() => {
    if (!authenticated) return;
    const controller = new AbortController();
    const id = setInterval(() => {
      reload()
        .then(() => loadPage(controller.signal))
        .catch((error) => {
          if (error.status === 401) setMe(null);
        });
    }, 30000);
    return () => {
      clearInterval(id);
      controller.abort();
    };
  }, [authenticated, reload, loadPage]);
  return { me, setMe, loading, data, items, integrations, reload, loadPage };
}
