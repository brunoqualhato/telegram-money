import {
  ArrowUpRight,
  ArrowRight,
  Clock3,
  FileText,
  Send,
  ShieldCheck,
  Layers,
} from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import { CLASSES } from "../../lib/constants.js";

export default function OverviewAside({
  data,
  classes,
  me,
  navigate,
  connect,
  report,
}) {
  return (
    <aside className="dashboard-aside">
      <div className="telegram-card">
        <span className="telegram-icon">
          <Send size={25} />
        </span>
        <Badge tone="light">SEU RADAR NO TELEGRAM</Badge>
        <h2>
          O mercado se move.
          <br />
          Você fica sabendo.
        </h2>
        <p>
          {me.telegram_connected
            ? "Seu Telegram está conectado. Os alertas seguem suas preferências de envio."
            : "Conecte seu Telegram para receber os alertas que realmente importam para você."}
        </p>
        <button
          onClick={me.telegram_connected ? () => navigate("settings") : connect}
        >
          {me.telegram_connected
            ? "Gerenciar conexão"
            : "Conectar meu Telegram"}
          <ArrowUpRight size={17} />
        </button>
        <small>
          <ShieldCheck size={13} /> Conexão por código único e temporário
        </small>
      </div>
      <section className="panel allocation">
        <div className="panel-heading">
          <h3>Sua distribuição</h3>
          <Layers size={17} />
        </div>
        {Object.keys(classes).length ? (
          <>
            <div className="allocation-bar">
              {Object.entries(classes).map(([key, value], i) => (
                <span
                  key={key}
                  className={`allocation-color color-${i}`}
                  style={{ width: `${(value / data.total) * 100}%` }}
                />
              ))}
            </div>
            {Object.entries(classes).map(([key, value], i) => (
              <div className="allocation-row" key={key}>
                <span>
                  <i className={`allocation-color color-${i}`} />
                  {CLASSES[key]}
                </span>
                <strong>{((value / data.total) * 100).toFixed(1)}%</strong>
              </div>
            ))}
            <small>Posições avaliadas em BRL</small>
          </>
        ) : (
          <p className="muted">
            Informe quantidades para visualizar a distribuição da sua carteira.
          </p>
        )}
      </section>
      <div className="insight-note">
        <span>
          <FileText size={19} />
        </span>
        <h3>Um resumo. Mais clareza.</h3>
        <p>
          Gere uma fotografia da carteira, com cotações e próximos pagamentos.
        </p>
        <button className="text-button" onClick={report}>
          Gerar meu resumo <ArrowRight size={15} />
        </button>
      </div>
      <p className="data-footnote">
        <Clock3 size={15} /> Dados sujeitos a atraso. Consulte o horário e a
        fonte de cada cotação.
      </p>
    </aside>
  );
}
