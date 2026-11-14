import { BellRing, TrendingUp, Wallet, Layers } from "lucide-react";
import { money } from "../../lib/formatters.js";
import { pct } from "../../lib/formatters.js";

export default function OverviewStats({ data, assets }) {
  return (
    <div className="stats">
      <div className="stat">
        <div>
          <span>Patrimônio acompanhado</span>
          <Wallet size={18} />
        </div>
        <strong>{money(data.total)}</strong>
        <small>
          Posições com cotação em reais
          {data.missing_positions > 0
            ? ` · ${data.missing_positions} sem avaliação`
            : ""}
        </small>
      </div>
      <div className="stat">
        <div>
          <span>Variação contra custo</span>
          <TrendingUp size={18} />
        </div>
        <strong className={data.gain >= 0 ? "positive" : "negative"}>
          {money(data.gain)}
        </strong>
        <small>
          {data.gain_pct !== null
            ? pct(data.gain_pct)
            : "Informe os preços médios"}{" "}
          · sem proventos e taxas
        </small>
      </div>
      <div className="stat">
        <div>
          <span>Ativos no radar</span>
          <Layers size={18} />
        </div>
        <strong>{assets.length.toString().padStart(2, "0")}</strong>
        <small>
          {new Set(assets.map((a) => a.asset_class)).size} classes acompanhadas
        </small>
      </div>
      <div className="stat">
        <div>
          <span>Alertas ativos</span>
          <BellRing size={18} />
        </div>
        <strong>{String(data.active_rules || 0).padStart(2, "0")}</strong>
        <small>{data.notifications_today || 0} eventos nas últimas 24h</small>
      </div>
    </div>
  );
}
