import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Layers,
  Target,
  Wallet,
} from "lucide-react";
import { money, pct, percentage } from "../../lib/formatters.js";

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  change,
  featured = false,
}) {
  const tone = value < 0 ? "negative" : "positive";
  const ChangeIcon = value < 0 ? ArrowDownRight : ArrowUpRight;
  return (
    <article className={`portfolio-stat ${featured ? "featured" : ""}`}>
      <div className="portfolio-stat-label">
        <span>{title}</span>
        <Icon size={18} />
      </div>
      <strong className={featured || value === null ? "" : tone}>
        {value === null ? "—" : money(value)}
      </strong>
      <div className="portfolio-stat-detail">
        {Number.isFinite(change) && (
          <span className={`metric-pill ${tone}`}>
            <ChangeIcon size={13} />
            {pct(change)}
          </span>
        )}
        <small>{subtitle}</small>
      </div>
    </article>
  );
}

export default function OverviewStats({ metrics }) {
  const total =
    metrics.heldCount > 0 && metrics.pricedCount === 0 ? null : metrics.total;
  return (
    <>
      <div className="portfolio-stats">
        <StatCard
          title="Patrimônio em BRL"
          value={total}
          icon={Wallet}
          featured
          subtitle={`${metrics.pricedCount} posições com valor de mercado`}
        />
        <StatCard
          title="Custo de aquisição"
          value={metrics.cost}
          icon={Layers}
          subtitle={`${metrics.costCount} de ${metrics.pricedCount} posições com custo informado`}
        />
        <StatCard
          title="Resultado com custo"
          value={metrics.gain}
          icon={Target}
          change={metrics.gainPct}
          subtitle="Sem proventos e taxas"
        />
        <StatCard
          title="Variação do dia"
          value={metrics.dayChange}
          icon={Activity}
          change={metrics.dayPct}
          subtitle="Ponderada pelo valor das posições"
        />
      </div>
      <div
        className="portfolio-indicators"
        aria-label="Indicadores da carteira"
      >
        <span>
          <strong>{metrics.heldCount}</strong> posições em carteira
        </span>
        <span>
          <strong>{metrics.allocations.length}</strong> classes com cotação
        </span>
        <span>
          <strong>
            {metrics.topThree === null ? "—" : percentage(metrics.topThree)}
          </strong>{" "}
          nos 3 maiores ativos
        </span>
        <span>
          <i
            className={
              metrics.missingQuotes > 0 ? "coverage-warning" : "coverage-ok"
            }
          />
          <strong>{metrics.missingQuotes}</strong> sem cotação em BRL
        </span>
      </div>
    </>
  );
}
