import Badge from "../../components/ui/Badge.jsx";
import { date } from "../../lib/formatters.js";
import MarketSourcesForm from "./MarketSourcesForm.jsx";

export default function SourcesSettings({ integrations = {}, reload, toast }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h3>Cobertura e saúde das fontes</h3>
      </div>
      <div className="panel-body">
        {Object.entries(integrations.capabilities || {}).map(([key, value]) => (
          <p className="capability" key={key}>
            {value}
          </p>
        ))}
        <hr />
        {integrations.sources?.length ? (
          integrations.sources.map((source) => (
            <div className="source-row" key={source.name}>
              <strong>{source.name}</strong>
              <small>
                {source.last_error ||
                  `Último sucesso: ${date(source.last_success)}`}
              </small>
              {source.last_error && <Badge tone="red">Atenção</Badge>}
            </div>
          ))
        ) : (
          <p className="muted">
            Os resultados de coleta aparecerão após o primeiro ciclo do worker.
          </p>
        )}
        <MarketSourcesForm
          integrations={integrations}
          reload={reload}
          toast={toast}
        />
      </div>
    </section>
  );
}
