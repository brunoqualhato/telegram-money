import { Activity, CheckCircle2, Clock3, Cpu } from "lucide-react";

function getSlotSubtitle(isPaused, maxAi) {
  if (isPaused) return "Processamento de IA temporariamente pausado.";
  if (maxAi === 1) return "1 tarefa por vez (recomendado).";
  return `${maxAi} tarefas simultâneas.`;
}

function RunningCard({ count }) {
  const sub =
    count > 0 ? "Processando no momento..." : "Nenhuma tarefa em execução";
  return (
    <div className="stat">
      <div>
        <span>EM EXECUÇÃO</span>
        <Activity size={16} />
      </div>
      <strong>{count}</strong>
      <small>{sub}</small>
    </div>
  );
}

function AiSlotCard({ isPaused, running, maxAi }) {
  const value = isPaused ? "Pausada" : `${running} / ${maxAi}`;
  return (
    <div className="stat">
      <div>
        <span>SLOTS DE IA DISPONÍVEIS</span>
        <Cpu size={16} />
      </div>
      <strong>{value}</strong>
      <small>{getSlotSubtitle(isPaused, maxAi)}</small>
    </div>
  );
}

export default function QueueStats({ stats }) {
  const safe = stats || {};
  const isPaused = Boolean(safe.ai_queue_paused);
  const running = safe.running || 0;
  const maxAi = safe.max_ai_concurrency || 1;

  return (
    <div className="stats">
      <div className="stat">
        <div>
          <span>AGUARDANDO NA FILA</span>
          <Clock3 size={16} />
        </div>
        <strong>{safe.pending || 0}</strong>
        <small>Tarefas prontas para processamento sequencial.</small>
      </div>

      <RunningCard count={running} />

      <div className="stat">
        <div>
          <span>CONCLUÍDAS</span>
          <CheckCircle2 size={16} />
        </div>
        <strong>{safe.completed || 0}</strong>
        <small>Processadas com sucesso.</small>
      </div>

      <AiSlotCard isPaused={isPaused} running={running} maxAi={maxAi} />
    </div>
  );
}
