import { Focus } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import { money, percentage } from "../../lib/formatters.js";
import { CLASS_COLORS } from "./portfolioMetrics.js";

export default function ConcentrationChart({ metrics }) {
  return (
    <section className="panel concentration-panel">
      <div className="panel-heading">
        <div>
          <h3>Concentração por ativo</h3>
          <p>As maiores posições, em valor de mercado</p>
        </div>
        <Focus size={19} />
      </div>
      {metrics.total > 0 ? (
        <>
          <div className="concentration-summary">
            <strong>{percentage(metrics.topThree)}</strong>
            <span>
              do patrimônio nos
              <br />
              <b>3 maiores ativos</b>
            </span>
          </div>
          <ol className="concentration-list">
            {metrics.positions.slice(0, 5).map((asset, index) => (
              <li key={asset.id}>
                <span className="position-rank">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <div className="position-label">
                    <strong>{asset.ticker}</strong>
                    <span>{percentage(asset.weight)}</span>
                  </div>
                  <div className="weight-track">
                    <span
                      style={{
                        width: `${asset.weight}%`,
                        background: CLASS_COLORS[asset.asset_class],
                      }}
                    />
                  </div>
                  <small>{money(asset.value)}</small>
                </div>
              </li>
            ))}
          </ol>
          <p className="panel-note">
            Pesos sobre o total cotado em BRL. Não representa uma avaliação de
            risco.
          </p>
        </>
      ) : (
        <Empty icon={Focus} title="Sem posições para comparar">
          Cadastre posições para acompanhar os pesos da carteira.
        </Empty>
      )}
    </section>
  );
}
