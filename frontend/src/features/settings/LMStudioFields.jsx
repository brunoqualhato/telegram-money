import ModelSelector from "./ModelSelector.jsx";
import Field from "../../components/ui/Field.jsx";

export default function LMStudioFields({
  baseUrl,
  setBaseUrl,
  apiKey,
  setApiKey,
  model,
  setModel,
  hasApiKey,
  detectedModels = [],
}) {
  return (
    <>
      <Field label="URL do LM Studio">
        <input
          type="text"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
        />
      </Field>
      <Field label="Chave de API (opcional)">
        <input
          type="password"
          placeholder={
            hasApiKey
              ? "Chave configurada (deixe vazio para manter)"
              : "opcional"
          }
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </Field>
      <ModelSelector
        provider="lmstudio"
        value={model}
        onChange={setModel}
        detectedModels={detectedModels}
      />
    </>
  );
}
