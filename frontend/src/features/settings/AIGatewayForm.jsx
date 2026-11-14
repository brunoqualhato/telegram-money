import { useState } from "react";
import LMStudioFields from "./LMStudioFields.jsx";
import OllamaFields from "./OllamaFields.jsx";
import Field from "../../components/ui/Field.jsx";
import Button from "../../components/ui/Button.jsx";
import { api } from "../../services/api.js";

function getInitialConfig(integrations = {}) {
  return {
    provider: integrations.ai_provider || "lmstudio",
    lmBaseUrl:
      integrations.lm_studio_base_url || "http://host.docker.internal:1235/v1",
    lmModel: integrations.lm_studio_model || "",
    ollamaUrl: integrations.ollama_url || "http://host.docker.internal:11434",
    ollamaModel: integrations.ollama_model || "",
    aiTimeout: integrations.ai_timeout_seconds || 180,
  };
}

function pickModel(models, currentModel) {
  if (!models || models.length === 0) return currentModel;
  if (!currentModel || !models.includes(currentModel)) return models[0];
  return currentModel;
}

function GatewayNotice({ testResult, error }) {
  if (error) {
    return (
      <div className="error-box" style={{ marginBottom: "12px" }}>
        {error}
      </div>
    );
  }
  if (testResult) {
    const list = testResult.models?.join(", ") || "nenhum";
    return (
      <div className="notice" style={{ marginBottom: "12px" }}>
        ✓ IA acessível. Modelos: <strong>{list}</strong>
      </div>
    );
  }
  return null;
}

function buildAIPayload(state) {
  return {
    ai_provider: state.provider,
    lm_studio_base_url: state.lmBaseUrl,
    lm_studio_model: state.lmModel,
    lm_studio_api_key: state.lmApiKey,
    ai_timeout_seconds: Number(state.aiTimeout),
    ollama_url: state.ollamaUrl,
    ollama_model: state.ollamaModel,
  };
}

export default function AIGatewayForm({ integrations, reload, toast }) {
  const init = getInitialConfig(integrations);
  const [provider, setProvider] = useState(init.provider);
  const [lmBaseUrl, setLmBaseUrl] = useState(init.lmBaseUrl);
  const [lmModel, setLmModel] = useState(init.lmModel);
  const [lmApiKey, setLmApiKey] = useState("");
  const [ollamaUrl, setOllamaUrl] = useState(init.ollamaUrl);
  const [ollamaModel, setOllamaModel] = useState(init.ollamaModel);
  const [aiTimeout, setAiTimeout] = useState(init.aiTimeout);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isLM = provider === "lmstudio";
  const url = isLM ? lmBaseUrl : ollamaUrl;

  async function testGateway() {
    setTesting(true);
    setError("");
    setTestResult(null);
    try {
      const key = isLM ? lmApiKey : "";
      const res = await api("/integrations/test-ai", {
        method: "POST",
        body: { provider, url, api_key: key },
      });
      setTestResult(res);
      if (isLM) setLmModel((prev) => pickModel(res.models, prev));
      else setOllamaModel((prev) => pickModel(res.models, prev));
    } catch (e) {
      setError(e.message || "Erro ao conectar com servidor de IA");
    } finally {
      setTesting(false);
    }
  }

  async function saveGateway(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = buildAIPayload({
        provider,
        lmBaseUrl,
        lmModel,
        lmApiKey,
        aiTimeout,
        ollamaUrl,
        ollamaModel,
      });
      await api("/integrations/settings", { method: "PUT", body: payload });
      toast("Configurações do gateway de IA salvas.");
      setLmApiKey("");
      await reload();
    } catch (e) {
      setError(e.message || "Erro ao salvar gateway de IA");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={saveGateway} style={{ marginTop: "16px" }}>
      <hr style={{ margin: "16px 0", borderColor: "var(--border-subtle)" }} />
      <h4 style={{ margin: "0 0 8px", fontSize: "14px", fontWeight: "600" }}>
        Configurar Servidor de IA
      </h4>
      <Field label="Provedor de IA">
        <select value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="lmstudio">LM Studio (Local / Docker)</option>
          <option value="ollama">Ollama (Local / Docker)</option>
        </select>
      </Field>
      {isLM ? (
        <LMStudioFields
          baseUrl={lmBaseUrl}
          setBaseUrl={setLmBaseUrl}
          apiKey={lmApiKey}
          setApiKey={setLmApiKey}
          model={lmModel}
          setModel={setLmModel}
          hasApiKey={integrations.lm_studio_has_api_key}
          detectedModels={testResult?.models || []}
        />
      ) : (
        <OllamaFields
          url={ollamaUrl}
          setUrl={setOllamaUrl}
          model={ollamaModel}
          setModel={setOllamaModel}
          detectedModels={testResult?.models || []}
        />
      )}
      <Field label="Timeout da IA (segundos)">
        <input
          type="number"
          min={5}
          max={600}
          value={aiTimeout}
          onChange={(e) => setAiTimeout(e.target.value)}
        />
      </Field>
      <div style={{ marginTop: "-8px", marginBottom: "12px" }}>
        <Button
          secondary
          small
          type="button"
          disabled={testing || !url}
          onClick={testGateway}
        >
          {testing ? "Testando…" : "Testar Conexão com IA"}
        </Button>
      </div>
      <GatewayNotice testResult={testResult} error={error} />
      <Button small disabled={saving}>
        {saving ? "Salvando…" : "Salvar Configuração de IA"}
      </Button>
    </form>
  );
}
