import { RefreshCw, ShieldCheck } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Button from "../../components/ui/Button.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import AIGatewayForm from "./AIGatewayForm.jsx";

export default function IntegrationsSettings({
  integrations = {},
  checkingAI,
  checkAI,
  aiCheck,
  error,
  reload,
  toast,
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Integrações</h3>
          <p>Credenciais ficam no servidor, fora do navegador.</p>
        </div>
        <ShieldCheck size={20} />
      </div>
      <div className="panel-body">
        {[
          ["Bot Telegram", integrations.telegram_configured],
          ["brapi · token", integrations.brapi_configured],
          [
            `${integrations.ai_provider === "ollama" ? "Ollama" : "LM Studio"} · gateway de IA`,
            integrations.ai_configured,
          ],
        ].map(([name, configured]) => (
          <div className="integration-row" key={name}>
            <span>{name}</span>
            <Badge tone={configured ? "green" : ""}>
              {configured ? "Configurado" : "Não configurado"}
            </Badge>
          </div>
        ))}
        <p className="form-note">
          Configurado indica presença da configuração, não conectividade
          validada. Coleta de cotações a cada {integrations.poll_seconds || 120}{" "}
          segundos.
        </p>
        <p className="form-note">
          Modelo:{" "}
          <strong>
            {integrations.ai_model || "não definido nas configurações"}
          </strong>
          . O teste consulta apenas a lista de modelos; não envia documentos.
        </p>
        <Button
          secondary
          small
          icon={RefreshCw}
          disabled={checkingAI}
          onClick={checkAI}
        >
          {checkingAI ? "Verificando…" : "Testar gateway de IA"}
        </Button>
        {aiCheck && (
          <div className="notice">
            <div>
              <strong>
                {aiCheck.model_available
                  ? "Modelo encontrado na lista"
                  : "Gateway acessível"}
              </strong>
              <p>
                Modelos:{" "}
                {aiCheck.models?.length
                  ? aiCheck.models.join(", ")
                  : "nenhum modelo disponível"}
              </p>
            </div>
          </div>
        )}
        <ErrorBox error={error} />
        <AIGatewayForm
          integrations={integrations}
          reload={reload}
          toast={toast}
        />
      </div>
    </section>
  );
}
