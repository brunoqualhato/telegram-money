import { useState, useEffect } from "react";
import Button from "../../components/ui/Button.jsx";

const AI_CONCURRENCY_OPTS = [
  { value: 1, label: "1 tarefa por vez (Recomendado para LLMs locais)" },
  { value: 2, label: "2 tarefas simultâneas (Placas com 16GB+ VRAM)" },
  { value: 4, label: "4 tarefas simultâneas (Alta capacidade)" },
];

const API_CONCURRENCY_OPTS = [
  { value: 1, label: "1 requisição por vez (Mínimo tráfego)" },
  { value: 2, label: "2 requisições simultâneas (Padrão)" },
  { value: 5, label: "5 requisições simultâneas (Rápido)" },
  { value: 10, label: "10 requisições simultâneas (Agressivo)" },
];

const TIMEOUT_OPTS = [
  { value: 60, label: "60 segundos (1 minuto)" },
  { value: 120, label: "120 segundos (2 minutos - Padrão)" },
  { value: 180, label: "180 segundos (3 minutos)" },
  { value: 300, label: "300 segundos (5 minutos)" },
];

const POLL_OPTS = [
  { value: 30, label: "A cada 30 segundos" },
  { value: 60, label: "A cada 1 minuto" },
  { value: 120, label: "A cada 2 minutos (Padrão)" },
  { value: 300, label: "A cada 5 minutos" },
];

function SettingSelect({ id, label, value, onChange, options, help }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        {!options.some((opt) => opt.value === value) && (
          <option value={value}>{value} (atual)</option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <small>{help}</small>
    </div>
  );
}

export default function QueueSettingsCard({ settings, onSave, saving }) {
  const [form, setForm] = useState({
    max_ai_concurrency: 1,
    max_api_concurrency: 2,
    ai_queue_paused: false,
    ai_job_timeout_seconds: 120,
    api_poll_interval_seconds: 120,
  });

  useEffect(() => {
    if (settings) {
      setForm({
        max_ai_concurrency: Number(settings.max_ai_concurrency || 1),
        max_api_concurrency: Number(settings.max_api_concurrency || 2),
        ai_queue_paused: Boolean(settings.ai_queue_paused),
        ai_job_timeout_seconds: Number(settings.ai_job_timeout_seconds || 120),
        api_poll_interval_seconds: Number(
          settings.api_poll_interval_seconds || 120,
        ),
      });
    }
  }, [settings]);

  const submit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3>Limites de Recursos & Concorrência</h3>
          <p>
            Configure quantos processos paralelos o sistema pode executar para
            proteger o dispositivo local.
          </p>
        </div>
      </div>
      <form onSubmit={submit} className="panel-body">
        <SettingSelect
          id="max_ai_concurrency"
          label="Agentes / Tarefas de IA em Paralelo"
          value={form.max_ai_concurrency}
          onChange={(v) => setForm((f) => ({ ...f, max_ai_concurrency: v }))}
          options={AI_CONCURRENCY_OPTS}
          help="Processamento sequencial (1 por vez) evita travar a máquina ou esgotar a memória GPU/CPU durante inferência local."
        />

        <SettingSelect
          id="max_api_concurrency"
          label="Concorrência de Busca em APIs Externas"
          value={form.max_api_concurrency}
          onChange={(v) => setForm((f) => ({ ...f, max_api_concurrency: v }))}
          options={API_CONCURRENCY_OPTS}
          help="Limite de requisições simultâneas para provedores de dados (Brapi, CVM, Tesouro Direto, RSS)."
        />

        <SettingSelect
          id="ai_job_timeout_seconds"
          label="Tempo Limite por Tarefa de IA"
          value={form.ai_job_timeout_seconds}
          onChange={(v) =>
            setForm((f) => ({ ...f, ai_job_timeout_seconds: v }))
          }
          options={TIMEOUT_OPTS}
          help="Libera o slot caso o modelo trave ou demore além do tempo limite."
        />

        <SettingSelect
          id="api_poll_interval_seconds"
          label="Intervalo de Varredura de Cotações"
          value={form.api_poll_interval_seconds}
          onChange={(v) =>
            setForm((f) => ({ ...f, api_poll_interval_seconds: v }))
          }
          options={POLL_OPTS}
          help="Frequência de atualização de cotações em segundo plano."
        />

        <div className="field" style={{ marginTop: "14px" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={form.ai_queue_paused}
              onChange={(e) =>
                setForm((f) => ({ ...f, ai_queue_paused: e.target.checked }))
              }
            />
            <strong>Pausar processamento da fila de IA temporariamente</strong>
          </label>
          <small>
            Suspende novas tarefas de IA sem desligar o sistema (útil para
            liberar memória e CPU para outras atividades).
          </small>
        </div>

        <div className="button-row" style={{ marginTop: "18px" }}>
          <Button type="submit" tone="primary" disabled={saving}>
            {saving ? "Salvando limites..." : "Salvar Parâmetros de Recursos"}
          </Button>
        </div>
      </form>
    </div>
  );
}
