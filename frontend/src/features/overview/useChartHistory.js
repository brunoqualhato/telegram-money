import { useEffect, useState } from "react";
import { api } from "../../services/api.js";

export default function useChartHistory(path, revision) {
  const [state, setState] = useState({ rows: [], loading: true, error: "" });
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    setState({ path, rows: [], loading: true, error: "" });
    api(path, { signal: controller.signal })
      .then((rows) => {
        if (!controller.signal.aborted)
          setState({ path, rows, loading: false, error: "" });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({ path, rows: [], loading: false, error: error.message });
      });
    return () => controller.abort();
  }, [path, revision]);
  return state.path === path
    ? state
    : { rows: [], loading: Boolean(path), error: "" };
}
