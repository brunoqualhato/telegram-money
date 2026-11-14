import { useState, useMemo } from "react";
import { ChevronDown, FileText, Plus, Download, Search } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { usePagination } from "../../lib/usePagination.js";
import { date } from "../../lib/formatters.js";

const REPORT_KINDS = {
  demand: "Resumo sob demanda",
  daily: "Fechamento diário",
  weekly: "Resumo semanal",
  monthly: "Resumo mensal",
};

function downloadReport(item) {
  const blob = new Blob([item.body], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `relatorio-${item.id}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

function ReportItem({ item }) {
  const kindLabel = REPORT_KINDS[item.kind] || item.kind;

  return (
    <details className="report-row">
      <summary>
        <span className="document-icon">
          <FileText size={20} />
        </span>
        <span>
          <strong>{kindLabel}</strong>
          <small>{date(item.created_at)}</small>
        </span>
        <ChevronDown size={17} />
      </summary>
      <pre>{item.body}</pre>
      <Button
        secondary
        small
        icon={Download}
        onClick={() => downloadReport(item)}
      >
        Baixar relatório
      </Button>
    </details>
  );
}

export default function ReportsPage({ items, report }) {
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState("all");

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const matchKind = kindFilter === "all" || item.kind === kindFilter;
      const term = search.toLowerCase();
      const matchSearch =
        !search ||
        item.body?.toLowerCase().includes(term) ||
        REPORT_KINDS[item.kind]?.toLowerCase().includes(term);
      return matchKind && matchSearch;
    });
  }, [items, kindFilter, search]);

  const pagination = usePagination(filtered, 10);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Relatórios da carteira</h3>
          <p>Diários, semanais, mensais e sob demanda.</p>
        </div>
        <Button icon={Plus} onClick={report}>
          Gerar agora
        </Button>
      </div>

      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar no conteúdo dos relatórios"
            aria-label="Buscar relatórios"
          />
        </div>
        <div className="tabs">
          {[
            ["all", "Todos"],
            ["daily", "Diários"],
            ["weekly", "Semanais"],
            ["monthly", "Mensais"],
            ["demand", "Sob demanda"],
          ].map(([val, label]) => (
            <button
              key={val}
              className={kindFilter === val ? "active" : ""}
              onClick={() => setKindFilter(val)}
            >
              {label}
            </button>
          ))}
        </div>
        <small>{filtered.length} relatórios</small>
      </div>

      {filtered.length ? (
        pagination.pagedItems.map((item) => (
          <ReportItem key={item.id} item={item} />
        ))
      ) : (
        <Empty icon={FileText} title="Nenhum relatório encontrado">
          Gere o primeiro resumo ou aguarde o fechamento programado.
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
