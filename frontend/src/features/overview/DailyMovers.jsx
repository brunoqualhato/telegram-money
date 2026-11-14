import { Activity } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import DivergingBars from "../../components/ui/DivergingBars.jsx";
import { money, pct } from "../../lib/formatters.js";

function MarketBreadth({ metrics }) {
  const segments = [
    { key: "up", label: "em alta", count: metrics.advancing },
    { key: "flat", label: "estáveis", count: metrics.unchanged },
    { key: "down", label: "em queda", count: metrics.declining },
  ];
  const total = segments.reduce((sum, item) => sum + item.count, 0);
  return (
    <div className="market-breadth">
      <div className="breadth-bar" aria-hidden="true">
        {segments.map((item) => (
          <span
            key={item.key}
            className={item.key}
            style={{ width: `${(item.count / total) * 100}%` }}
          />
        ))}
      </div>
      <div className="breadth-legend">
        {segments.map((item) => (
          <span key={item.key}>
            <i className={item.key} />
            <strong>{item.count}</strong> {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function DailyMovers({ metrics }) {
  const items = metrics.positions
    .filter((asset) => asset.daily !== null)
    .sort((a, b) => Math.abs(b.daily.amount) - Math.abs(a.daily.amount))
    .slice(0, 5)
    .map((asset) => ({
      id: asset.id,
      label: asset.ticker,
      value: asset.daily.amount,
      detail: `${pct(asset.daily.pct)} no ativo`,
    }));
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>O que moveu sua carteira</h3>
          <p>Os 5 maiores impactos na variação do dia</p>
        </div>
        <Activity size={19} />
      </div>
      {items.length ? (
        <>
          <div className="panel-metric">
            <strong className={metrics.dayChange < 0 ? "negative" : "positive"}>
              {money(metrics.dayChange)}
            </strong>
            <span>variação estimada em BRL</span>
          </div>
          <MarketBreadth metrics={metrics} />
          <DivergingBars items={items} />
          <p className="panel-note">
            Impacto ponderado pela posição, a partir da variação de cada
            cotação.{" "}
            {metrics.missingDaily > 0 &&
              `${metrics.missingDaily} posições sem variação disponível.`}
          </p>
        </>
      ) : (
        <Empty icon={Activity} title="Aguardando variações do dia">
          As contribuições aparecem com posições cotadas em BRL e variação
          disponível.
        </Empty>
      )}
    </section>
  );
}
