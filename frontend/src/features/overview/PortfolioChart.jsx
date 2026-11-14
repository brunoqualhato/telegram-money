import { useState, useEffect } from "react";
import { TrendingUp } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import { money } from "../../lib/formatters.js";
import { date } from "../../lib/formatters.js";
import { api } from "../../services/api.js";

export default function PortfolioChart({ assets }) {
  const [selected, setSelected] = useState(""),
    [history, setHistory] = useState([]);
  const assetId = selected || assets[0]?.id;
  useEffect(() => {
    let active = true;
    if (assetId)
      api(`/assets/${assetId}/history`)
        .then((rows) => {
          if (active) setHistory(rows.reverse());
        })
        .catch(() => {
          if (active) setHistory([]);
        });
    return () => {
      active = false;
    };
  }, [assetId, assets.length]);
  const prices = history.map((q) => Number(q.price)),
    min = Math.min(...prices),
    max = Math.max(...prices),
    spread = max - min || 1;
  const points = prices
    .map(
      (p, i) =>
        `${20 + (i / Math.max(1, prices.length - 1)) * 660},${160 - ((p - min) / spread) * 125}`,
    )
    .join(" ");
  const selectedAsset = assets.find((a) => a.id === Number(assetId));
  return (
    <div className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <h3>Um olhar para o movimento</h3>
          <p>Histórico coletado · preço por unidade</p>
        </div>
        {assets.length > 0 && (
          <select
            aria-label="Ativo do gráfico"
            value={assetId}
            onChange={(e) => setSelected(e.target.value)}
          >
            {assets.map((a) => (
              <option key={a.id} value={a.id}>
                {a.ticker}
              </option>
            ))}
          </select>
        )}
      </div>
      {history.length > 1 ? (
        <>
          <div className="chart-number">
            {chartPrice(selectedAsset, prices.at(-1))}
            <Badge tone="green">{history.length} observações</Badge>
          </div>
          <svg
            className="price-chart"
            viewBox="0 0 700 190"
            role="img"
            aria-label={`Histórico de cotação de ${selectedAsset?.ticker}`}
          >
            <defs>
              <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6a9d65" stopOpacity=".25" />
                <stop offset="100%" stopColor="#6a9d65" stopOpacity="0" />
              </linearGradient>
            </defs>
            {[40, 100, 160].map((y) => (
              <line
                key={y}
                x1="20"
                x2="680"
                y1={y}
                y2={y}
                stroke="#e9ece5"
                strokeDasharray="4 5"
              />
            ))}
            <polygon points={`20,180 ${points} 680,180`} fill="url(#fill)" />
            <polyline
              points={points}
              fill="none"
              stroke="#46784b"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />
            <circle
              cx="680"
              cy={160 - ((prices.at(-1) - min) / spread) * 125}
              r="5"
              fill="#46784b"
              stroke="white"
              strokeWidth="3"
            />
          </svg>
          <div className="chart-dates">
            <span>{date(history[0].quoted_at)}</span>
            <span>{date(history.at(-1).quoted_at)}</span>
          </div>
        </>
      ) : (
        <Empty icon={TrendingUp} title="Cada atualização conta">
          O gráfico aparece após duas cotações coletadas para o ativo.
        </Empty>
      )}
    </div>
  );
}

function chartPrice(asset, price) {
  return asset?.quote?.currency === "BRL" ? money(price) : price?.toFixed(2);
}
