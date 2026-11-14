import { useState } from "react";
import Field from "../../components/ui/Field.jsx";
import Button from "../../components/ui/Button.jsx";
import ModelSelector from "../settings/ModelSelector.jsx";
import { api } from "../../services/api.js";

function AITestFeedback({ testResult, testError }) {
  if (testResult) {
    const names = testResult.models?.join(", ") || "nenhum";
    return (
      <div className="notice" style={{ marginBottom: "14px" }}>
        ✓ Servidor de IA acessível. Modelos disponíveis:{" "}
        <strong>{names}</strong>
      </div>
    );
  }
  if (testError) {
    return (
      <div className="error-box" style={{ marginBottom: "14px" }}>
        {testError}
      </div>
    );
  }
  return null;
}

function SetupLMFields({ data, onChange, detectedModels }) {
  return (
    <>
      <Field label="URL do LM Studio">
        <input
          type="text"
          value={data.lm_studio_base_url}
          onChange={(e) => onChange("lm_studio_base_url", e.target.value)}
        />
      </Field>
      <Field label="Chave de API (opcional)">
        <input
          type="password"
          placeholder="opcional se autenticação ativada"
          value={data.lm_studio_api_key}
          onChange={(e) => onChange("lm_studio_api_key", e.target.value)}
        />
      </Field>
      <ModelSelector
        provider="lmstudio"
        value={data.lm_studio_model}
        onChange={(val) => onChange("lm_studio_model", val)}
        detectedModels={detectedModels}
      />
    </>
  );
}

function SetupOllamaFields({ data, onChange, detectedModels }) {
  return (
    <>
      <Field label="URL do Ollama">
        <input
          type="text"
          value={data.ollama_url}
          onChange={(e) => onChange("ollama_url", e.target.value)}
        />
      </Field>
      <ModelSelector
        provider="ollama"
        value={data.ollama_model}
        onChange={(val) => onChange("ollama_model", val)}
        detectedModels={detectedModels}
      />
    </>
  );
}

export default function SetupStepAI({ data, onChange }) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState("");

  const isLM = data.ai_provider === "lmstudio";
  const url = isLM ? data.lm_studio_base_url : data.ollama_url;

  async function testAI() {
    setTesting(true);
    setTestError("");
    setTestResult(null);
    try {
      const apiKey = isLM ? data.lm_studio_api_key : "";
      const res = await api("/setup/test-ai", {
        method: "POST",
        body: { provider: data.ai_provider, url, api_key: apiKey },
      });
      setTestResult(res);
      const first = res.models?.[0];
      if (first) {
        const cur = isLM ? data.lm_studio_model : data.ollama_model;
        if (!cur || !res.models.includes(cur)) {
          onChange(isLM ? "lm_studio_model" : "ollama_model", first);
        }
      }
    } catch (e) {
      setTestError(e.message || "Falha ao conectar no gateway de IA");
    } finally {
      setTesting(false);
    }
  }

  const detected = testResult?.models || [];

  return (
    <div className="setup-step">
      <p className="form-note">
        Opcional. IA local para resumos de fatos relevantes sem envio de dados à
        nuvem.
      </p>
      <Field label="Provedor de IA">
        <select
          value={data.ai_provider}
          onChange={(e) => {
            onChange("ai_provider", e.target.value);
            setTestResult(null);
          }}
        >
          <option value="lmstudio">LM Studio (Local / Docker)</option>
          <option value="ollama">Ollama (Local / Docker)</option>
        </select>
      </Field>
      {isLM ? (
        <SetupLMFields
          data={data}
          onChange={onChange}
          detectedModels={detected}
        />
      ) : (
        <SetupOllamaFields
          data={data}
          onChange={onChange}
          detectedModels={detected}
        />
      )}
      <div style={{ marginTop: "-8px", marginBottom: "14px" }}>
        <Button
          secondary
          small
          type="button"
          disabled={testing || !url}
          onClick={testAI}
        >
          {testing ? "Testando…" : "Testar Conexão com IA"}
        </Button>
      </div>
      <AITestFeedback testResult={testResult} testError={testError} />
    </div>
  );
}
