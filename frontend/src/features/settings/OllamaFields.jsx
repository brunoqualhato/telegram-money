import ModelSelector from "./ModelSelector.jsx";
import Field from "../../components/ui/Field.jsx";

export default function OllamaFields({
  url,
  setUrl,
  model,
  setModel,
  detectedModels = [],
}) {
  return (
    <>
      <Field label="URL do Ollama">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      </Field>
      <ModelSelector
        provider="ollama"
        value={model}
        onChange={setModel}
        detectedModels={detectedModels}
      />
    </>
  );
}
