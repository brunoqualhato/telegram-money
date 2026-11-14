import { useState, useEffect, useRef } from "react";
import usePanelData from "./usePanelData.js";
import getPageInfo from "./getPageInfo.js";
import { api } from "../services/api.js";

export default function useApp() {
  const [page, setPage] = useState("overview");
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [refreshing, setRefreshing] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [confirm, setConfirm] = useState(null);
  const toastTimer = useRef();
  useEffect(() => () => clearTimeout(toastTimer.current), []);
  const panel = usePanelData({ page, setError, setSearch, setFilter });
  const { reload, loadPage, data } = panel;
  function notify(text) {
    setToast(text);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 6000);
  }
  function navigate(next) {
    setPage(next);
    setMobile(false);
  }
  async function done(text) {
    notify(text);
    await reload();
    await loadPage();
  }
  async function act(path, method = "POST", body) {
    try {
      const result = await api(path, { method, body });
      await done(result.message || "Alteração salva.");
      return result;
    } catch (e) {
      setError(e.message);
      return null;
    }
  }
  async function connect() {
    const result = await act("/telegram/link");
    if (result?.url) setModal({ type: "telegram", url: result.url });
  }
  async function report() {
    const result = await act("/reports");
    if (result) navigate("reports");
  }
  async function refresh() {
    setRefreshing(true);
    await act("/market/refresh");
    setRefreshing(false);
  }
  function removeAsset(asset) {
    setConfirm({
      title: `Remover ${asset.ticker}?`,
      text: "O ativo, suas cotações e regras serão removidos. O histórico de notificações e os documentos serão preservados.",
      action: () => act(`/assets/${asset.id}`, "DELETE"),
    });
  }
  function retry(item) {
    setConfirm({
      title: "Reenviar notificação?",
      text:
        item.status === "uncertain"
          ? "A entrega anterior é incerta. Confira o Telegram antes de continuar: o reenvio pode duplicar uma mensagem já recebida."
          : "A mensagem voltará à fila de envio e seguirá suas preferências atuais.",
      action: () => act(`/notifications/${item.id}/retry`),
    });
  }
  return {
    ...panel,
    page,
    modal,
    setModal,
    toast,
    setToast,
    error,
    setError,
    search,
    setSearch,
    filter,
    setFilter,
    refreshing,
    mobile,
    setMobile,
    confirm,
    setConfirm,
    notify,
    navigate,
    done,
    act,
    connect,
    report,
    refresh,
    removeAsset,
    retry,
    ...getPageInfo({ page, data, search, filter }),
  };
}
