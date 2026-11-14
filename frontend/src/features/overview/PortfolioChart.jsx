import { useState } from "react";
import { TrendingUp } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import LineChart from "../../components/ui/LineChart.jsx";
import { money } from "../../lib/formatters.js";
import useChartHistory from "./useChartHistory.js";

function QuoteHistory({ state, asset }) {
  if (state.error)
    return (
      <p className="chart-message error-box" role="alert">
        Não foi possível carregar as cotações. {state.error}
      </p>
    );
  if (state.loading)
    return (
      <div className="chart-loading" role="status">
        <TrendingUp size={28} />
        <span>Carregando cotações…</span>
      </div>
    );
  const rows = state.rows
    .filter((quote) => quote.currency === asset.quote.currency)
    .map((quote) => ({ date: quote.quoted_at, value: Number(quote.price) }))
    .filter((quote) => Number.isFinite(quote.value))
    .sort((a, b) => new Date(a.date) - new Date(b.date));
  if (rows.length < 2)
    return (
      <Empty icon={TrendingUp} title="Cada atualização conta">
        O gráfico aparece após duas cotações coletadas para o ativo.
      </Empty>
    );
  const currency = asset.quote.currency;
  const formatValue =
    currency === "BRL"
      ? money
      : (value) =>
          `${currency} ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
  return (
    <>
      <div className="history-value">
        <strong>{formatValue(rows.at(-1).value)}</strong>
        <span>
          Preço por unidade <i /> {rows.length} observações
        </span>
      </div>
      <LineChart
        rows={rows}
        label={`Histórico de ${asset.ticker}`}
        formatValue={formatValue}
        reference={
          asset.average_price > 0 && currency === "BRL"
            ? asset.average_price
            : undefined
        }
        referenceLabel="Preço médio informado"
      />
    </>
  );
}

export default function PortfolioChart({ assets }) {
  const [selected, setSelected] = useState("");
  const quoted = assets.filter((asset) => asset.quote);
  const asset =
    quoted.find((item) => item.id === Number(selected)) || quoted[0];
  const state = useChartHistory(
    asset ? `/assets/${asset.id}/history` : null,
    assets,
  );
  return (
    <section className="panel asset-history">
      <div className="panel-heading">
        <div>
          <h3>Uma posição, mais de perto</h3>
          <p>Histórico de cotação por ativo</p>
        </div>
        {asset && (
          <select
            aria-label="Ativo do gráfico"
            value={asset.id}
            onChange={(e) => setSelected(e.target.value)}
          >
            {quoted.map((item) => (
              <option key={item.id} value={item.id}>
                {item.ticker}
              </option>
            ))}
          </select>
        )}
      </div>
      {asset ? (
        <QuoteHistory key={asset.id} state={state} asset={asset} />
      ) : (
        <Empty icon={TrendingUp} title="Aguardando a primeira cotação">
          Seu histórico por ativo aparecerá aqui.
        </Empty>
      )}
      <p className="panel-note">
        Preços nas datas coletadas. Referência de custo apenas para posições em
        BRL.
      </p>
    </section>
  );
}
