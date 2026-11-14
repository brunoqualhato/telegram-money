import DocumentSummary from "./DocumentSummary.jsx";
import { useState } from "react";
import {
  FileText,
  Plus,
  RefreshCw,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import { date } from "../../lib/formatters.js";

export default function Documents({ items, add, summarize, fetchNews }) {
  const [expanded, setExpanded] = useState(null);
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
      {items.length ? (
        items.map((doc) => (
          <article className="document-row" key={doc.id}>
            <div className="document-top">
              <span className="document-icon">
                <FileText size={22} />
              </span>
              <div>
                <h3>{doc.title}</h3>
                <p>
                  {doc.ticker} · {doc.kind.replaceAll("_", " ")} ·{" "}
                  {date(doc.created_at)}
                </p>
              </div>
              <Badge tone={doc.status === "ready" ? "green" : ""}>
                {{
                  ready: "Resumo disponível",
                  pending: "Aguardando IA",
                  unconfigured: "IA não configurada",
                  failed: "Falha no resumo",
                }[doc.status] || doc.status}
              </Badge>
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
                <button
                  className="text-button"
                  onClick={() =>
                    setExpanded(expanded === doc.id ? null : doc.id)
                  }
                >
                  <Sparkles size={14} />
                  {expanded === doc.id
                    ? "Recolher resumo"
                    : "Ler resumo e evidências"}
                </button>
              ) : (
                <button className="text-button" onClick={() => summarize(doc)}>
                  Gerar resumo <Sparkles size={14} />
                </button>
              )}
            </div>
            {doc.error && <p className="inline-error">{doc.error}</p>}
            {expanded === doc.id && doc.summary && (
              <DocumentSummary summary={doc.summary} />
            )}
          </article>
        ))
      ) : (
        <Empty icon={FileText} title="Os documentos ganham contexto aqui">
          Importe texto ou PDF para guardar a referência e solicitar um resumo
          com IA local.
        </Empty>
      )}
    </section>
  );
}
