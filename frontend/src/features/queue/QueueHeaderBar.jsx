import { Pause, Play, RotateCw, Trash2, Cpu, Sliders } from "lucide-react";
import Button from "../../components/ui/Button.jsx";

export default function QueueHeaderBar({
  activeTab,
  setActiveTab,
  isPaused,
  onTogglePause,
  onDispatch,
  onClearCompleted,
  onRefresh,
  loading,
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "12px",
        marginBottom: "16px",
      }}
    >
      <div className="tabs" role="tablist">
        <button
          type="button"
          className={activeTab === "queue" ? "active" : ""}
          onClick={() => setActiveTab("queue")}
        >
          <Cpu size={16} style={{ marginRight: "6px" }} />
          Fila de Tarefas
        </button>
        <button
          type="button"
          className={activeTab === "settings" ? "active" : ""}
          onClick={() => setActiveTab("settings")}
        >
          <Sliders size={16} style={{ marginRight: "6px" }} />
          Limites de Recursos
        </button>
      </div>

      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        <Button
          tone={isPaused ? "primary" : "secondary"}
          onClick={onTogglePause}
          disabled={loading}
        >
          {isPaused ? (
            <>
              <Play size={15} style={{ marginRight: "6px" }} />
              Retomar IA
            </>
          ) : (
            <>
              <Pause size={15} style={{ marginRight: "6px" }} />
              Pausar IA
            </>
          )}
        </Button>

        <Button tone="primary" onClick={onDispatch} disabled={loading}>
          <Play size={15} style={{ marginRight: "6px" }} />
          Processar Agora
        </Button>

        <Button tone="secondary" onClick={onClearCompleted} disabled={loading}>
          <Trash2 size={15} style={{ marginRight: "6px" }} />
          Limpar Concluídas
        </Button>

        <Button tone="secondary" onClick={onRefresh} disabled={loading}>
          <RotateCw size={15} style={{ marginRight: "6px" }} />
          Atualizar
        </Button>
      </div>
    </div>
  );
}
