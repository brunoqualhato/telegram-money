import LoginCredentials from "./LoginCredentials.jsx";
import SetupWizard from "./SetupWizard.jsx";
import { useState, useEffect } from "react";
import { ArrowRight, BellRing, ShieldCheck, Sparkles } from "lucide-react";
import Logo from "../../components/Logo.jsx";
import Badge from "../../components/ui/Badge.jsx";
import Button from "../../components/ui/Button.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import { api } from "../../services/api.js";

export default function Login({ onLogin }) {
  const [setup, setSetup] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    api("/setup")
      .then(setSetup)
      .catch((e) => setError(e.message));
  }, []);
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.target);
    try {
      await api("/auth/login", {
        method: "POST",
        body: { email: form.get("email"), password: form.get("password") },
      });
      onLogin();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-layout">
      <section className="login-story">
        <Logo />
        <div>
          <Badge tone="light">INVESTIMENTOS, SEM O RUÍDO</Badge>
          <h1>
            Seu dinheiro.
            <br />
            No seu radar.
          </h1>
          <p>
            As informações que importam para a sua carteira, organizadas em um
            só lugar e entregues no Telegram.
          </p>
          <div className="login-features">
            <span>
              <BellRing size={19} /> Alertas que fazem sentido
            </span>
            <span>
              <Sparkles size={19} /> Documentos com mais clareza
            </span>
            <span>
              <ShieldCheck size={19} /> Um espaço só seu
            </span>
          </div>
        </div>
        <small>Monitor pessoal · Sem execução de ordens</small>
      </section>
      <section className="login-form">
        {setup && !setup.configured ? (
          <SetupWizard
            onComplete={() => {
              api("/setup")
                .then(setSetup)
                .catch(() => {});
              onLogin();
            }}
          />
        ) : (
          <div>
            <div className="eyebrow">BEM-VINDO AO SEU PAINEL</div>
            <h2>Bom ter você por aqui.</h2>
            <p>Acesse seu radar de investimentos.</p>
            {setup?.demo && (
              <div className="notice">
                Demonstração local com dados ilustrativos. Nenhuma mensagem será
                enviada.
              </div>
            )}
            <form onSubmit={submit}>
              <LoginCredentials demo={setup?.demo} />
              <ErrorBox error={error} />
              <Button disabled={busy || !setup?.configured} icon={ArrowRight}>
                {busy ? "Entrando…" : "Entrar no meu painel"}
              </Button>
            </form>
            <p className="login-foot">
              <ShieldCheck size={16} /> Acesso privado. Credenciais configuradas
              no seu servidor.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
