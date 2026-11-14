import { useState, useMemo } from "react";
import { BellRing, Plus, Trash2, Pause, Play, Search } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import IconButton from "../../components/ui/IconButton.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { usePagination } from "../../lib/usePagination.js";
import { RULES } from "../../lib/constants.js";

function RuleCard({ rule, act, setConfirm }) {
  const valueDisplay = rule.kind.includes("52w")
    ? "Extremo anual"
    : rule.kind.startsWith("price")
      ? Number(rule.threshold).toLocaleString("pt-BR", {
          minimumFractionDigits: 2,
        })
      : `${Number(rule.threshold)}%`;

  return (
    <article className={`rule-card ${!rule.enabled ? "disabled" : ""}`}>
      <div className="rule-top">
        <span className="ticker-logo">{rule.ticker.slice(0, 2)}</span>
        <strong>{rule.ticker}</strong>
        <Badge tone={rule.enabled ? "green" : ""}>
          {rule.enabled ? "Ativo" : "Pausado"}
        </Badge>
      </div>
      <h3>{RULES[rule.kind]}</h3>
      <strong className="rule-value">{valueDisplay}</strong>
      <p>
        {rule.triggered
          ? "Disparou · aguardando condição normal para rearmar"
          : "Aguardando próxima cotação válida"}
      </p>
      <div className="rule-footer">
        <button
          className="text-button"
          onClick={() =>
            act(`/rules/${rule.id}`, "PATCH", { enabled: !rule.enabled })
          }
        >
          {rule.enabled ? <Pause size={14} /> : <Play size={14} />}{" "}
          {rule.enabled ? "Pausar" : "Retomar"}
        </button>
        <IconButton
          label={`Excluir regra ${rule.ticker}`}
          onClick={() =>
            setConfirm({
              title: "Excluir este alerta?",
              text: "Esta regra deixará de monitorar o ativo.",
              action: () => act(`/rules/${rule.id}`, "DELETE"),
            })
          }
        >
          <Trash2 size={15} />
        </IconButton>
      </div>
    </article>
  );
}

export default function AlertsPage({ data, items, setModal, act, setConfirm }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return items.filter((rule) => {
      const matchStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && rule.enabled) ||
        (statusFilter === "paused" && !rule.enabled);
      const term = search.toLowerCase();
      const matchSearch =
        !search ||
        rule.ticker?.toLowerCase().includes(term) ||
        RULES[rule.kind]?.toLowerCase().includes(term);
      return matchStatus && matchSearch;
    });
  }, [items, statusFilter, search]);

  const pagination = usePagination(filtered, 10);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Regras de monitoramento</h3>
          <p>Alta, queda, preço-alvo e extremos de 52 semanas.</p>
        </div>
        <Button
          icon={Plus}
          disabled={!data.assets.length}
          onClick={() => setModal({ type: "rule" })}
        >
          Criar alerta
        </Button>
      </div>

      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por ativo ou tipo de alerta"
            aria-label="Buscar alertas"
          />
        </div>
        <div className="tabs">
          {[
            ["all", "Todos"],
            ["active", "Ativos"],
            ["paused", "Pausados"],
          ].map(([val, label]) => (
            <button
              key={val}
              className={statusFilter === val ? "active" : ""}
              onClick={() => setStatusFilter(val)}
            >
              {label}
            </button>
          ))}
        </div>
        <small>{filtered.length} alertas</small>
      </div>

      {filtered.length ? (
        <div className="rule-grid">
          {pagination.pagedItems.map((rule) => (
            <RuleCard
              key={rule.id}
              rule={rule}
              act={act}
              setConfirm={setConfirm}
            />
          ))}
        </div>
      ) : (
        <Empty icon={BellRing} title="Nenhum alerta encontrado">
          {data.assets.length
            ? "Defina o preço ou a variação que você quer acompanhar."
            : "Adicione um ativo na sua lista antes de criar um alerta."}
        </Empty>
      )}

      <Pagination
        page={pagination.page}
        pageSize={pagination.pageSize}
        totalItems={pagination.totalItems}
        onPageChange={pagination.setPage}
        onPageSizeChange={pagination.setPageSize}
      />
    </section>
  );
}
