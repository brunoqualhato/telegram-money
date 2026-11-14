import { useState, useEffect, useCallback, useMemo } from "react";
import { api } from "../../services/api.js";
import { usePagination } from "../../lib/usePagination.js";
import QueueStats from "./QueueStats.jsx";
import QueueHeaderBar from "./QueueHeaderBar.jsx";
import QueueFilters from "./QueueFilters.jsx";
import QueueTable from "./QueueTable.jsx";
import QueueSettingsCard from "./QueueSettingsCard.jsx";

function matchText(job, search) {
  if (!search) return true;
  const q = search.toLowerCase();
  const text =
    `${job.title} ${job.target_id || ""} ${job.category}`.toLowerCase();
  return text.includes(q);
}

function matchJob(job, search, statusFilter, categoryFilter) {
  if (statusFilter !== "all" && job.status !== statusFilter) return false;
  if (categoryFilter !== "all" && job.category !== categoryFilter) return false;
  return matchText(job, search);
}

export default function QueuePage({ notify, setError }) {
  const [activeTab, setActiveTab] = useState("queue");
  const [data, setData] = useState({ stats: null, settings: null, jobs: [] });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const loadQueue = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api("/queue");
      setData(res);
    } catch (err) {
      if (setError) setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [setError]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const filteredJobs = useMemo(
    () =>
      (data.jobs || []).filter((j) =>
        matchJob(j, search, statusFilter, categoryFilter),
      ),
    [data.jobs, search, statusFilter, categoryFilter],
  );

  const pagination = usePagination(filteredJobs);

  const handleAction = async (endpoint, options, successMsg) => {
    try {
      await api(endpoint, options);
      if (notify && successMsg) notify(successMsg);
      await loadQueue();
    } catch (err) {
      if (setError) setError(err.message);
    }
  };

  const handleSaveSettings = async (newSettings) => {
    try {
      setSaving(true);
      await api("/queue/settings", {
        method: "POST",
        body: newSettings,
      });
      if (notify) notify("Parâmetros de recursos salvos com sucesso.");
      await loadQueue();
    } catch (err) {
      if (setError) setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <QueueHeaderBar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isPaused={data.stats?.ai_queue_paused}
        onTogglePause={() =>
          handleAction(
            "/queue/pause",
            { method: "POST" },
            data.stats?.ai_queue_paused
              ? "Processamento de IA retomado."
              : "Processamento de IA pausado.",
          )
        }
        onDispatch={() =>
          handleAction(
            "/queue/dispatch",
            { method: "POST" },
            "Varredura da fila disparada com sucesso.",
          )
        }
        onClearCompleted={() =>
          handleAction(
            "/queue/completed",
            { method: "DELETE" },
            "Histórico de tarefas concluídas limpo.",
          )
        }
        onRefresh={loadQueue}
        loading={loading}
      />

      <QueueStats stats={data.stats} />

      {activeTab === "queue" && (
        <div className="panel">
          <QueueFilters
            search={search}
            setSearch={setSearch}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            categoryFilter={categoryFilter}
            setCategoryFilter={setCategoryFilter}
          />
          <QueueTable
            pagedJobs={pagination.pagedItems}
            totalItems={pagination.totalItems}
            page={pagination.page}
            pageSize={pagination.pageSize}
            totalPages={pagination.totalPages}
            setPage={pagination.setPage}
            setPageSize={pagination.setPageSize}
            onCancel={(job) =>
              handleAction(
                `/queue/${job.id}/cancel`,
                { method: "POST" },
                `Tarefa #${job.id} cancelada.`,
              )
            }
            onRetry={(job) =>
              handleAction(
                `/queue/${job.id}/retry`,
                { method: "POST" },
                `Tarefa #${job.id} reenfileirada.`,
              )
            }
            onPrioritize={(job) =>
              handleAction(
                `/queue/${job.id}/prioritize`,
                { method: "POST" },
                `Prioridade da tarefa #${job.id} aumentada.`,
              )
            }
          />
        </div>
      )}

      {activeTab === "settings" && (
        <QueueSettingsCard
          settings={data.settings}
          onSave={handleSaveSettings}
          saving={saving}
        />
      )}
    </div>
  );
}
