import { BellRing, Plus, Trash2, Pause, Play } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import IconButton from "../../components/ui/IconButton.jsx";
import { RULES } from "../../lib/constants.js";

export default function AlertsPage({ data, items, setModal, act, setConfirm }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Regras de monitoramento</h3>
          <p>Alta, queda, preço-alvo e extremos de 52 semanas.</p>
        </div>
        <Button
          icon={Plus}
          disabled={!data.assets.length}
          onClick={() => setModal({ type: "rule" })}
        >
          Criar alerta
        </Button>
      </div>
      {items.length ? (
        <div className="rule-grid">
          {items.map((rule) => (
            <article
              className={`rule-card ${!rule.enabled ? "disabled" : ""}`}
              key={rule.id}
            >
              <div className="rule-top">
                <span className="ticker-logo">{rule.ticker.slice(0, 2)}</span>
                <strong>{rule.ticker}</strong>
                <Badge tone={rule.enabled ? "green" : ""}>
                  {rule.enabled ? "Ativo" : "Pausado"}
                </Badge>
              </div>
              <h3>{RULES[rule.kind]}</h3>
              <strong className="rule-value">
                {rule.kind.includes("52w")
                  ? "Extremo anual"
                  : rule.kind.startsWith("price")
                    ? Number(rule.threshold).toLocaleString("pt-BR", {
                        minimumFractionDigits: 2,
                      })
                    : `${Number(rule.threshold)}%`}
              </strong>
              <p>
                {rule.triggered
                  ? "Disparou · aguardando condição normal para rearmar"
                  : "Aguardando próxima cotação válida"}
              </p>
              <div className="rule-footer">
                <button
                  className="text-button"
                  onClick={() =>
                    act(`/rules/${rule.id}`, "PATCH", {
                      enabled: !rule.enabled,
                    })
                  }
                >
                  {rule.enabled ? <Pause size={14} /> : <Play size={14} />}{" "}
                  {rule.enabled ? "Pausar" : "Retomar"}
                </button>
                <IconButton
                  label={`Excluir regra ${rule.ticker}`}
                  onClick={() =>
                    setConfirm({
                      title: "Excluir este alerta?",
                      text: "Esta regra deixará de monitorar o ativo.",
                      action: () => act(`/rules/${rule.id}`, "DELETE"),
                    })
                  }
                >
                  <Trash2 size={15} />
                </IconButton>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty icon={BellRing} title="Um bom alerta começa com uma regra">
          {data.assets.length
            ? "Defina o preço ou a variação que você quer acompanhar."
            : "Adicione um ativo na sua lista antes de criar um alerta."}
        </Empty>
      )}
    </section>
  );
}
