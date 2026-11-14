import { useState } from "react";
import { ChartNoAxesCombined } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import LineChart from "../../components/ui/LineChart.jsx";
import { money } from "../../lib/formatters.js";
import useChartHistory from "./useChartHistory.js";

function HistoryHeader({ metric, setMetric, days, setDays }) {
  return (
    <div className="panel-heading history-heading">
      <div>
        <h3>Evolução da carteira</h3>
        <p>Suas posições atuais aos preços históricos</p>
      </div>
      <div className="chart-controls">
        <div className="tabs" aria-label="Métrica do histórico">
          {[
            ["total", "Patrimônio"],
            ["gain", "Resultado"],
          ].map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-pressed={metric === key}
              className={metric === key ? "active" : ""}
              onClick={() => setMetric(key)}
            >
              {label}
            </button>
          ))}
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          aria-label="Período do gráfico"
        >
          {[7, 30, 60, 90].map((period) => (
            <option key={period} value={period}>
              {period} dias
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

function HistoryContent({ state, metric, metrics }) {
  if (state.error)
    return (
      <p className="chart-message error-box" role="alert">
        Não foi possível carregar o histórico. {state.error}
      </p>
    );
  if (state.loading)
    return (
      <div className="chart-loading" role="status">
        <ChartNoAxesCombined size={28} />
        <span>Carregando evolução da carteira…</span>
      </div>
    );
  if (metric === "gain" && metrics.missingCost > 0)
    return (
      <Empty title="Complete o custo das posições">
        Informe o preço médio de todos os ativos cotados para visualizar a
        evolução do resultado.
      </Empty>
    );
  const rows = state.rows
    .filter((row) => !row.partial && Number.isFinite(row[metric]))
    .map((row) => ({ date: row.date, value: row[metric] }));
  if (rows.length < 2)
    return (
      <Empty
        icon={ChartNoAxesCombined}
        title="Construindo histórico da carteira"
      >
        O gráfico aparece com cotações completas em pelo menos dois dias.
      </Empty>
    );
  const reference = metric === "gain" ? 0 : metrics.cost;
  return (
    <>
      <div className="history-value">
        <strong>{money(rows.at(-1).value)}</strong>
        <span>
          {rows.length} dias com dados <i /> última observação
        </span>
      </div>
      <LineChart
        key={metric}
        rows={rows}
        label="Evolução da carteira"
        negative={metrics.gain < 0}
        reference={metrics.missingCost === 0 ? reference : undefined}
        referenceLabel={metric === "gain" ? "Equilíbrio" : "Custo informado"}
      />
    </>
  );
}

export default function PortfolioHistoryChart({ overviewData, metrics }) {
  const [days, setDays] = useState(30);
  const [metric, setMetric] = useState("total");
  const state = useChartHistory(
    `/portfolio/history?days=${days}`,
    overviewData.assets,
  );
  return (
    <section className="panel portfolio-history">
      <HistoryHeader
        metric={metric}
        setMetric={setMetric}
        days={days}
        setDays={setDays}
      />
      <HistoryContent state={state} metric={metric} metrics={metrics} />
      <p className="panel-note">
        Estimativa com quantidade e custo atuais, sem reconstruir compras,
        vendas, proventos ou taxas. Dias incompletos são omitidos.
      </p>
    </section>
  );
}
