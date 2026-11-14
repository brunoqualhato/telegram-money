import { useState, useMemo } from "react";
import {
  FileText,
  Plus,
  RefreshCw,
  Sparkles,
  ExternalLink,
  Search,
} from "lucide-react";
import DocumentSummary from "./DocumentSummary.jsx";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { usePagination } from "../../lib/usePagination.js";
import { date } from "../../lib/formatters.js";

const STATUS_LABELS = {
  ready: "Resumo disponível",
  pending: "Aguardando IA",
  unconfigured: "IA não configurada",
  failed: "Falha no resumo",
  cancelled: "Resumo cancelado",
};

function DocumentItem({ doc, expanded, onToggle, onSummarize }) {
  const isExpanded = expanded === doc.id;
  const statusText = STATUS_LABELS[doc.status] || doc.status;

  return (
    <article className="document-row">
      <div className="document-top">
        <span className="document-icon">
          <FileText size={22} />
        </span>
        <div>
          <h3>{doc.title}</h3>
          <p>
            {doc.ticker} · {doc.kind?.replaceAll("_", " ")} ·{" "}
            {date(doc.created_at)}
          </p>
        </div>
        <Badge tone={doc.status === "ready" ? "green" : ""}>{statusText}</Badge>
      </div>
      <div className="document-actions">
        <a
          className="text-button"
          href={doc.source_url}
          target="_blank"
          rel="noreferrer"
        >
          Documento original <ExternalLink size={13} />
        </a>
        {doc.summary ? (
          <button className="text-button" onClick={() => onToggle(doc.id)}>
            <Sparkles size={14} />
            {isExpanded ? "Recolher resumo" : "Ler resumo e evidências"}
          </button>
        ) : (
          <button className="text-button" onClick={() => onSummarize(doc)}>
            Gerar resumo <Sparkles size={14} />
          </button>
        )}
      </div>
      {doc.error && <p className="inline-error">{doc.error}</p>}
      {isExpanded && doc.summary && <DocumentSummary summary={doc.summary} />}
    </article>
  );
}

export default function Documents({ items, add, summarize, fetchNews }) {
  const [expanded, setExpanded] = useState(null);
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState("all");

  const filtered = useMemo(() => {
    return items.filter((doc) => {
      const matchKind = kindFilter === "all" || doc.kind === kindFilter;
      const term = search.toLowerCase();
      const matchSearch =
        !search ||
        doc.title?.toLowerCase().includes(term) ||
        doc.ticker?.toLowerCase().includes(term);
      return matchKind && matchSearch;
    });
  }, [items, kindFilter, search]);

  const pagination = usePagination(filtered, 10);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Informação com contexto</h3>
          <p>
            Importe relatórios, fatos relevantes e notícias com a fonte
            original.
          </p>
        </div>
        <div className="button-row">
          {fetchNews && (
            <Button secondary icon={RefreshCw} onClick={fetchNews}>
              Buscar notícias
            </Button>
          )}
          <Button icon={Plus} onClick={add}>
            Importar documento
          </Button>
        </div>
      </div>

      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por título ou ativo"
            aria-label="Buscar documentos"
          />
        </div>
        <div className="tabs">
          {[
            ["all", "Todos"],
            ["relatorio", "Relatórios"],
            ["fato_relevante", "Fatos Relevantes"],
            ["noticia", "Notícias"],
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
        <small>{filtered.length} documentos</small>
      </div>

      {filtered.length ? (
        pagination.pagedItems.map((doc) => (
          <DocumentItem
            key={doc.id}
            doc={doc}
            expanded={expanded}
            onToggle={(id) => setExpanded(expanded === id ? null : id)}
            onSummarize={summarize}
          />
        ))
      ) : (
        <Empty icon={FileText} title="Nenhum documento encontrado">
          Importe texto ou PDF para guardar a referência e solicitar um resumo
          com IA local.
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
