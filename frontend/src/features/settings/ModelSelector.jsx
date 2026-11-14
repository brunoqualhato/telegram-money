import { useState } from "react";
import Field from "../../components/ui/Field.jsx";

const LM_PRESETS = [
  { id: "qwen3.5-9b", label: "Qwen 3.5 9B (Recomendado)" },
  { id: "qwen2.5-7b-instruct", label: "Qwen 2.5 7B Instruct" },
  { id: "qwen2.5-14b-instruct", label: "Qwen 2.5 14B Instruct" },
  { id: "llama-3.2-3b-instruct", label: "Llama 3.2 3B Instruct (Leve)" },
  { id: "deepseek-r1-distill-qwen-7b", label: "DeepSeek R1 Distill Qwen 7B" },
  { id: "mistral-7b-instruct-v0.3", label: "Mistral 7B Instruct" },
];

const OLLAMA_PRESETS = [
  { id: "qwen2.5:7b-instruct", label: "qwen2.5:7b-instruct (Recomendado)" },
  { id: "qwen2.5:14b-instruct", label: "qwen2.5:14b-instruct" },
  { id: "llama3.2:3b", label: "llama3.2:3b (Leve)" },
  { id: "deepseek-r1:7b", label: "deepseek-r1:7b (Raciocínio)" },
  { id: "mistral:7b", label: "mistral:7b" },
];

function DetectedOptGroup({ models }) {
  if (!models || models.length === 0) return null;
  return (
    <optgroup label="Detectados no Servidor">
      {models.map((m) => (
        <option key={m} value={m}>
          {m}
        </option>
      ))}
    </optgroup>
  );
}

function resolveSelected(customMode, value, fallback) {
  if (customMode) return "__custom__";
  return value || fallback;
}

export default function ModelSelector({
  provider,
  value,
  onChange,
  detectedModels,
}) {
  const isLM = provider === "lmstudio";
  const presets = isLM ? LM_PRESETS : OLLAMA_PRESETS;
  const models = detectedModels || [];
  const known = new Set([...presets.map((p) => p.id), ...models]);
  const isCustom = Boolean(value && !known.has(value));
  const [customMode, setCustomMode] = useState(isCustom);

  function handleSelect(e) {
    const val = e.target.value;
    const isCustomChoice = val === "__custom__";
    setCustomMode(isCustomChoice);
    if (!isCustomChoice) onChange(val);
  }

  const selected = resolveSelected(customMode, value, presets[0]?.id || "");
  const label = isLM ? "Modelo LM Studio" : "Modelo Ollama";

  return (
    <>
      <Field label={label}>
        <select value={selected} onChange={handleSelect}>
          <DetectedOptGroup models={models} />
          <optgroup label="Modelos Recomendados">
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </optgroup>
          <option value="__custom__">
            Outro modelo (digitar manualmente)...
          </option>
        </select>
      </Field>
      {customMode && (
        <Field label="Nome do Modelo Personalizado">
          <input
            type="text"
            placeholder={
              isLM ? "ex: meu-modelo-custom" : "ex: meu-modelo:latest"
            }
            value={value}
            onChange={(e) => onChange(e.target.value)}
          />
        </Field>
      )}
    </>
  );
}
