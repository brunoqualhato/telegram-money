import { ArrowUp, RotateCw, X } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import IconButton from "../../components/ui/IconButton.jsx";
import { date } from "../../lib/formatters.js";
import { STATUS } from "../../lib/constants.js";

function getStatusTone(status) {
  if (status === "completed") return "green";
  if (status === "failed") return "red";
  if (status === "running") return "blue";
  if (status === "pending") return "yellow";
  return "light";
}

function QueueRowActions({ job, onCancel, onRetry, onPrioritize }) {
  const isPending = job.status === "pending";
  const isRunning = job.status === "running";
  const canRetry = job.status === "failed" || job.status === "cancelled";

  return (
    <div style={{ display: "inline-flex", gap: "4px" }}>
      {isPending && (
        <IconButton label="Priorizar na fila" onClick={() => onPrioritize(job)}>
          <ArrowUp size={15} />
        </IconButton>
      )}
      {(isPending || isRunning) && (
        <IconButton label="Cancelar tarefa" onClick={() => onCancel(job)}>
          <X size={15} />
        </IconButton>
      )}
      {canRetry && (
        <IconButton label="Tentar novamente" onClick={() => onRetry(job)}>
          <RotateCw size={15} />
        </IconButton>
      )}
    </div>
  );
}

export default function QueueRow({ job, onCancel, onRetry, onPrioritize }) {
  const hasPriority = job.priority > 0;

  return (
    <tr>
      <td>
        <Badge tone={getStatusTone(job.status)}>
          {STATUS[job.status] || job.status}
        </Badge>
      </td>
      <td>
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          <strong>{job.title}</strong>
          <small className="muted" style={{ fontSize: "11px" }}>
            Tipo: {job.category.toUpperCase()} · Tentativas: {job.attempts}
          </small>
          {job.error && (
            <small style={{ color: "#c2410c", marginTop: "2px" }}>
              {job.error}
            </small>
          )}
        </div>
      </td>
      <td>
        {job.target_id ? (
          <code style={{ fontSize: "11px" }}>{job.target_id}</code>
        ) : (
          <span className="muted">—</span>
        )}
      </td>
      <td>
        <span
          style={{
            fontWeight: hasPriority ? "600" : "normal",
            color: hasPriority ? "#166534" : "inherit",
          }}
        >
          {hasPriority ? `+${job.priority} (Alta)` : "Normal"}
        </span>
      </td>
      <td>
        <small className="quote-time">{date(job.created_at)}</small>
      </td>
      <td style={{ textAlign: "right" }}>
        <QueueRowActions
          job={job}
          onCancel={onCancel}
          onRetry={onRetry}
          onPrioritize={onPrioritize}
        />
      </td>
    </tr>
  );
}
