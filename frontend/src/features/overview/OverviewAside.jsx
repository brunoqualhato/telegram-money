import { ArrowRight, FileText, Send, ShieldCheck } from "lucide-react";
import { percentage } from "../../lib/formatters.js";

function CoverageRow({ label, count, total }) {
  const coverage = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="coverage-row">
      <div>
        <span>{label}</span>
        <strong>
          {count} de {total}
        </strong>
      </div>
      <div className="weight-track" aria-hidden="true">
        <span style={{ width: `${coverage}%` }} />
      </div>
      <small>
        {total > 0
          ? `${percentage(coverage)} de cobertura`
          : "Adicione posições para começar"}
      </small>
    </div>
  );
}

export default function OverviewAside({
  metrics,
  me,
  navigate,
  connect,
  report,
}) {
  return (
    <aside className="dashboard-aside portfolio-aside">
      <section className="panel data-coverage">
        <div className="panel-heading">
          <div>
            <h3>Dados da carteira</h3>
            <p>O que entra nos seus indicadores</p>
          </div>
          <ShieldCheck size={19} />
        </div>
        <CoverageRow
          label="Cotações em BRL"
          count={metrics.pricedCount}
          total={metrics.heldCount}
        />
        <CoverageRow
          label="Custo nas posições cotadas"
          count={metrics.costCount}
          total={metrics.pricedCount}
        />
        <p className="panel-note">
          Sem cotação, a posição não entra no patrimônio. Sem preço médio, não
          entra no resultado.
        </p>
        <button
          type="button"
          className="text-button coverage-action"
          onClick={() => navigate("assets")}
        >
          Revisar meus ativos <ArrowRight size={15} />
        </button>
      </section>
      <div className="portfolio-telegram">
        <Send size={22} />
        <div>
          <h3>Seu radar no Telegram</h3>
          <p>
            {me.telegram_connected
              ? "Conexão ativa. Alertas conforme suas preferências."
              : "Receba os sinais da sua carteira onde você estiver."}
          </p>
        </div>
        <button
          type="button"
          onClick={me.telegram_connected ? () => navigate("settings") : connect}
        >
          {me.telegram_connected ? "Gerenciar conexão" : "Conectar Telegram"}
          <ArrowRight size={15} />
        </button>
      </div>
      <button type="button" className="portfolio-report" onClick={report}>
        <FileText size={19} />
        <span>
          <strong>Resumo da carteira</strong>
          <small>Gere uma fotografia das suas posições</small>
        </span>
        <ArrowRight size={16} />
      </button>
    </aside>
  );
}
