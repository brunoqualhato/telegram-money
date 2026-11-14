import { useState } from "react";
import { Scale } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import DivergingBars from "../../components/ui/DivergingBars.jsx";
import { money, pct } from "../../lib/formatters.js";

export default function ProfitLossChart({ metrics }) {
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState(false);
  const known = metrics.positions.filter((asset) => asset.cost !== null);
  const filtered = known
    .filter((asset) => {
      if (filter === "profit") return asset.gain > 0;
      if (filter === "loss") return asset.gain < 0;
      return true;
    })
    .sort((a, b) => Math.abs(b.gain) - Math.abs(a.gain));
  const visible = expanded ? filtered : filtered.slice(0, 5);
  const items = visible.map((asset) => ({
    id: asset.id,
    label: asset.ticker,
    value: asset.gain,
    detail: pct(asset.gainPct),
  }));
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Resultado por ativo</h3>
          <p>Ganhos e perdas contra o custo informado</p>
        </div>
        <Scale size={19} />
      </div>
      <div className="result-toolbar">
        <div className="tabs" aria-label="Filtrar resultado por ativo">
          {[
            ["all", "Todos"],
            ["profit", "Lucro"],
            ["loss", "Prejuízo"],
          ].map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-pressed={filter === key}
              className={filter === key ? "active" : ""}
              onClick={() => {
                setFilter(key);
                setExpanded(false);
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <span>{known.length} com custo</span>
      </div>
      <div className="panel-metric">
        <strong className={metrics.gain < 0 ? "negative" : "positive"}>
          {metrics.gain === null ? "—" : money(metrics.gain)}
        </strong>
        <span>resultado das posições com custo</span>
      </div>
      {items.length ? (
        <DivergingBars items={items} />
      ) : (
        <Empty icon={Scale} title="Nenhuma posição neste filtro">
          Informe quantidade, cotação e preço médio para acompanhar o resultado.
        </Empty>
      )}
      {filtered.length > 5 && (
        <button
          type="button"
          className="text-button chart-expand"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded
            ? "Mostrar os 5 principais"
            : `Ver todos os ${filtered.length} ativos`}
        </button>
      )}
      <p className="panel-note">
        Sem proventos ou taxas.{" "}
        {metrics.missingCost > 0 &&
          `${metrics.missingCost} posições sem custo informado foram excluídas.`}
      </p>
    </section>
  );
}
