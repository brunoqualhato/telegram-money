import { Send } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Button from "../../components/ui/Button.jsx";

export default function TelegramSettings({ me, connect, act }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Seu Telegram</h3>
          <p>Um canal privado para seus alertas.</p>
        </div>
        <Send size={20} />
      </div>
      <div className="panel-body">
        <Badge tone={me.telegram_connected ? "green" : ""}>
          {me.telegram_connected ? "Conectado" : "Não conectado"}
        </Badge>
        <p>
          {me.telegram_connected
            ? `Conta ${me.telegram_name ? `@${me.telegram_name}` : "pessoal"} vinculada.`
            : "Crie um bot pelo BotFather, configure o token no .env e gere seu link de conexão."}
        </p>
        <div className="button-row">
          <Button icon={Send} onClick={connect}>
            {me.telegram_connected ? "Gerar novo vínculo" : "Conectar Telegram"}
          </Button>
          {me.telegram_connected && (
            <>
              <Button secondary onClick={() => act("/telegram/test", "POST")}>
                Enviar teste
              </Button>
              <button
                className="text-button danger"
                onClick={() => act("/telegram/link", "DELETE")}
              >
                Desvincular
              </button>
            </>
          )}
        </div>
        <div className="command-list">
          {[
            "/cotacao PETR4",
            "/carteira",
            "/proventos",
            "/tesouro",
            "/resumo",
            "/alertas",
            "/pausar",
            "/retomar",
            "/sair",
          ].map((x) => (
            <code key={x}>{x}</code>
          ))}
        </div>
      </div>
    </section>
  );
}
