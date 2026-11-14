import { useState } from "react";
import Field from "../../components/ui/Field.jsx";
import Button from "../../components/ui/Button.jsx";
import { api } from "../../services/api.js";

export default function TelegramBotForm({ integrations, reload, toast }) {
  const [token, setToken] = useState("");
  const [username, setUsername] = useState(
    integrations.telegram_bot_username || "",
  );
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function testToken() {
    if (!token) {
      setError("Digite o token para testar.");
      return;
    }
    setTesting(true);
    setError("");
    setTestResult(null);
    try {
      const res = await api("/integrations/test-telegram", {
        method: "POST",
        body: { token },
      });
      setTestResult(res);
      if (res.username && !username) setUsername(res.username);
    } catch (e) {
      setError(e.message || "Erro ao validar token");
    } finally {
      setTesting(false);
    }
  }

  async function saveBot(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        telegram_bot_token: token,
        telegram_bot_username: username,
      };
      await api("/integrations/settings", { method: "PUT", body: payload });
      toast("Configurações do bot do Telegram salvas.");
      setToken("");
      await reload();
    } catch (e) {
      setError(e.message || "Erro ao salvar bot");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={saveBot} style={{ marginTop: "16px" }}>
      <hr style={{ margin: "16px 0", borderColor: "var(--border-subtle)" }} />
      <h4 style={{ margin: "0 0 8px", fontSize: "14px", fontWeight: "600" }}>
        Configurações do Bot
      </h4>
      <Field label="Token do Bot">
        <input
          type="text"
          placeholder={
            integrations.telegram_has_token
              ? "Token configurado (deixe vazio para manter)"
              : "123456:ABCdefGhIJKlmNoPQRsTUVwxyZ"
          }
          value={token}
          onChange={(e) => {
            setToken(e.target.value);
            setTestResult(null);
          }}
        />
      </Field>
      <div style={{ marginTop: "-8px", marginBottom: "12px" }}>
        <Button
          secondary
          small
          type="button"
          disabled={testing || !token}
          onClick={testToken}
        >
          {testing ? "Testando…" : "Testar Token"}
        </Button>
      </div>
      {testResult && (
        <div className="notice" style={{ marginBottom: "12px" }}>
          ✓ Bot conectado: <strong>@{testResult.username}</strong> (
          {testResult.first_name})
        </div>
      )}
      <Field label="Username do Bot (sem @)">
        <input
          type="text"
          placeholder="ex: MeuInvestimentoBot"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </Field>
      {error && (
        <div className="error-box" style={{ marginBottom: "12px" }}>
          {error}
        </div>
      )}
      <Button small disabled={saving}>
        {saving ? "Salvando…" : "Salvar Configuração do Bot"}
      </Button>
    </form>
  );
}
