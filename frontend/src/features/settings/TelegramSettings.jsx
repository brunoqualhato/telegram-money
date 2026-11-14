import { Send } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Button from "../../components/ui/Button.jsx";
import TelegramBotForm from "./TelegramBotForm.jsx";

const COMMANDS = [
  "/cotacao PETR4",
  "/carteira",
  "/proventos",
  "/tesouro",
  "/resumo",
  "/alertas",
  "/pausar",
  "/retomar",
  "/sair",
];

function TelegramActions({ isConnected, connect, act }) {
  if (!isConnected) {
    return (
      <div className="button-row">
        <Button icon={Send} onClick={connect}>
          Conectar Telegram
        </Button>
      </div>
    );
  }
  return (
    <div className="button-row">
      <Button icon={Send} onClick={connect}>
        Gerar novo vínculo
      </Button>
      <Button secondary onClick={() => act("/telegram/test", "POST")}>
        Enviar teste
      </Button>
      <button
        className="text-button danger"
        onClick={() => act("/telegram/link", "DELETE")}
      >
        Desvincular
      </button>
    </div>
  );
}

export default function TelegramSettings({
  me,
  integrations = {},
  connect,
  act,
  reload,
  toast,
}) {
  const isConnected = Boolean(me?.telegram_connected);
  const accountName = me?.telegram_name ? `@${me.telegram_name}` : "pessoal";
  const statusNote = isConnected
    ? `Conta ${accountName} vinculada.`
    : "Crie um bot pelo BotFather, configure o token abaixo e gere seu link de conexão.";

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
        <Badge tone={isConnected ? "green" : ""}>
          {isConnected ? "Conectado" : "Não conectado"}
        </Badge>
        <p>{statusNote}</p>
        <TelegramActions
          isConnected={isConnected}
          connect={connect}
          act={act}
        />
        <div className="command-list">
          {COMMANDS.map((x) => (
            <code key={x}>{x}</code>
          ))}
        </div>
        <TelegramBotForm
          integrations={integrations}
          reload={reload}
          toast={toast}
        />
      </div>
    </section>
  );
}
