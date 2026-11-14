import { useState } from "react";
import Field from "../../components/ui/Field.jsx";
import Button from "../../components/ui/Button.jsx";
import { api } from "../../services/api.js";

export default function MarketSourcesForm({ integrations, reload, toast }) {
  const [brapiToken, setBrapiToken] = useState("");
  const [pollSeconds, setPollSeconds] = useState(
    integrations.poll_seconds || 120,
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function saveSources(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        poll_seconds: Number(pollSeconds),
        brapi_token: brapiToken,
      };
      await api("/integrations/settings", { method: "PUT", body: payload });
      toast("Configurações de fontes de mercado salvas.");
      setBrapiToken("");
      await reload();
    } catch (e) {
      setError(e.message || "Erro ao salvar fontes de mercado");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={saveSources} style={{ marginTop: "16px" }}>
      <hr style={{ margin: "16px 0", borderColor: "var(--border-subtle)" }} />
      <h4 style={{ margin: "0 0 8px", fontSize: "14px", fontWeight: "600" }}>
        Configurar Fontes de Mercado
      </h4>
      <Field label="Token brapi.dev (opcional)">
        <input
          type="text"
          placeholder={
            integrations.brapi_has_token
              ? "Token configurado (deixe vazio para manter)"
              : "Em branco para conector aberto B3 gratuito"
          }
          value={brapiToken}
          onChange={(e) => setBrapiToken(e.target.value)}
        />
      </Field>
      <Field label="Intervalo de Coleta de Cotações (segundos)">
        <input
          type="number"
          min={30}
          max={3600}
          value={pollSeconds}
          onChange={(e) => setPollSeconds(e.target.value)}
        />
      </Field>
      {error && (
        <div className="error-box" style={{ marginBottom: "12px" }}>
          {error}
        </div>
      )}
      <Button small disabled={saving}>
        {saving ? "Salvando…" : "Salvar Fontes de Mercado"}
      </Button>
    </form>
  );
}
