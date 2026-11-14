import { useState } from "react";
import SourcesSettings from "./SourcesSettings.jsx";
import PreferencesSettings from "./PreferencesSettings.jsx";
import IntegrationsSettings from "./IntegrationsSettings.jsx";
import TelegramSettings from "./TelegramSettings.jsx";
import { api } from "../../services/api.js";

export default function SettingsPage({
  me,
  integrations,
  connect,
  act,
  reload,
  toast,
}) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [checkingAI, setCheckingAI] = useState(false),
    [aiCheck, setAICheck] = useState(null);
  async function checkAI() {
    setCheckingAI(true);
    setError("");
    try {
      const result = await api("/ai/check", { method: "POST" });
      setAICheck(result);
      toast(result.message);
    } catch (e) {
      setError(e.message);
      setAICheck(null);
    } finally {
      setCheckingAI(false);
    }
  }
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.target),
      payload = {};
    for (const key of [
      "notifications_enabled",
      "daily_report",
      "weekly_report",
      "monthly_report",
      "event_alerts",
    ])
      payload[key] = form.has(key);
    for (const key of ["quiet_start", "quiet_end", "max_per_hour"])
      payload[key] = Number(form.get(key));
    payload.timezone = form.get("timezone");
    try {
      await api("/preferences", { method: "PUT", body: payload });
      toast("Preferências salvas.");
      await reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const props = {
    me,
    integrations,
    connect,
    act,
    checkingAI,
    checkAI,
    aiCheck,
    error,
    save,
    busy,
  };
  return (
    <div className="settings-grid">
      <TelegramSettings {...props} />
      <IntegrationsSettings {...props} />
      <PreferencesSettings {...props} />
      <SourcesSettings {...props} />
    </div>
  );
}
