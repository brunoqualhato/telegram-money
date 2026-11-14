import { useState } from "react";
import Field from "../../components/ui/Field.jsx";
import Button from "../../components/ui/Button.jsx";
import { api } from "../../services/api.js";

export default function SetupStepTelegram({ data, onChange }) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState("");

  async function testToken() {
    if (!data.telegram_bot_token) {
      setTestError("Informe o token do bot para testar.");
      return;
    }
    setTesting(true);
    setTestError("");
    setTestResult(null);
    try {
      const res = await api("/setup/test-telegram", {
        method: "POST",
        body: { token: data.telegram_bot_token },
      });
      setTestResult(res);
      if (res.username && !data.telegram_bot_username) {
        onChange("telegram_bot_username", res.username);
      }
    } catch (e) {
      setTestError(e.message || "Falha ao testar token do Telegram");
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="setup-step">
      <p className="form-note">
        Opcional. Crie seu bot no <strong>@BotFather</strong> no Telegram para
        receber notificações. Pode ser configurado agora ou mais tarde.
      </p>
      <Field label="Token do Bot do Telegram">
        <input
          type="text"
          placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
          value={data.telegram_bot_token}
          onChange={(e) => {
            onChange("telegram_bot_token", e.target.value);
            setTestResult(null);
          }}
        />
      </Field>
      <div style={{ marginTop: "-8px", marginBottom: "14px" }}>
        <Button
          secondary
          small
          type="button"
          disabled={testing || !data.telegram_bot_token}
          onClick={testToken}
        >
          {testing ? "Testando…" : "Testar Token no Telegram"}
        </Button>
      </div>
      {testResult && (
        <div className="notice" style={{ marginBottom: "14px" }}>
          ✓ Bot conectado: <strong>@{testResult.username}</strong> (
          {testResult.first_name})
        </div>
      )}
      {testError && (
        <div className="error-box" style={{ marginBottom: "14px" }}>
          {testError}
        </div>
      )}
      <Field label="Username do Bot (sem @)">
        <input
          type="text"
          placeholder="ex: MeuInvestimentoBot"
          value={data.telegram_bot_username}
          onChange={(e) => onChange("telegram_bot_username", e.target.value)}
        />
      </Field>
    </div>
  );
}
