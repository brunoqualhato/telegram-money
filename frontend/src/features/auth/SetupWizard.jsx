import { useState } from "react";
import { ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import SetupStepAdmin from "./SetupStepAdmin.jsx";
import SetupStepTelegram from "./SetupStepTelegram.jsx";
import SetupStepAI from "./SetupStepAI.jsx";
import SetupStepMarket from "./SetupStepMarket.jsx";
import Button from "../../components/ui/Button.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import { api } from "../../services/api.js";

const INITIAL_DATA = {
  email: "",
  password: "",
  confirm_password: "",
  timezone: "America/Sao_Paulo",
  telegram_bot_token: "",
  telegram_bot_username: "",
  brapi_token: "",
  poll_seconds: 120,
  ai_provider: "lmstudio",
  lm_studio_base_url: "http://host.docker.internal:1235/v1",
  lm_studio_model: "qwen3.5-9b",
  lm_studio_api_key: "",
  ai_timeout_seconds: 180,
  ollama_url: "http://host.docker.internal:11434",
  ollama_model: "qwen2.5:7b-instruct",
};

const STEPS = [
  { id: 1, label: "Conta" },
  { id: 2, label: "Telegram" },
  { id: 3, label: "IA Local" },
  { id: 4, label: "Mercado" },
];

export default function SetupWizard({ onComplete }) {
  const [step, setStep] = useState(1);
  const [data, setData] = useState(INITIAL_DATA);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function handleChange(field, value) {
    setData((prev) => ({ ...prev, [field]: value }));
  }

  function validateStep1() {
    if (!data.email.includes("@")) {
      setError("Informe um e-mail válido.");
      return false;
    }
    if (data.password.length < 12) {
      setError("A senha deve ter no mínimo 12 caracteres.");
      return false;
    }
    if (data.password !== data.confirm_password) {
      setError("As senhas não conferem.");
      return false;
    }
    return true;
  }

  function next() {
    setError("");
    if (step === 1 && !validateStep1()) return;
    setStep((s) => Math.min(s + 1, 4));
  }

  function prev() {
    setError("");
    setStep((s) => Math.max(s - 1, 1));
  }

  function goToStep(target) {
    if (step === 1 && target > 1 && !validateStep1()) return;
    setError("");
    setStep(target);
  }

  async function submit(e) {
    e.preventDefault();
    if (step < 4) {
      next();
      return;
    }
    setError("");
    if (!validateStep1()) {
      setStep(1);
      return;
    }
    setBusy(true);
    try {
      const payload = { ...data };
      delete payload.confirm_password;
      await api("/setup", { method: "POST", body: payload });
      onComplete();
    } catch (err) {
      setError(err.message || "Falha ao concluir configuração do ambiente.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wizard-box">
      <div className="eyebrow">SETUP WIZARD · PRIMEIRO ACESSO</div>
      <h2>Configurar Ambiente</h2>
      <p>Configure seu usuário e integrações diretamente pelo painel.</p>

      <div className="wizard-stepper">
        {STEPS.map((s) => (
          <button
            type="button"
            key={s.id}
            onClick={() => goToStep(s.id)}
            className={`wizard-step-pill ${step === s.id ? "active" : ""} ${step > s.id ? "done" : ""}`}
            style={{ cursor: "pointer", background: "none" }}
          >
            <span>{s.id}</span>
            <small>{s.label}</small>
          </button>
        ))}
      </div>

      <form onSubmit={submit}>
        {step === 1 && <SetupStepAdmin data={data} onChange={handleChange} />}
        {step === 2 && (
          <SetupStepTelegram data={data} onChange={handleChange} />
        )}
        {step === 3 && <SetupStepAI data={data} onChange={handleChange} />}
        {step === 4 && <SetupStepMarket data={data} onChange={handleChange} />}

        <ErrorBox error={error} />

        <div className="wizard-nav">
          {step > 1 && (
            <Button secondary type="button" icon={ArrowLeft} onClick={prev}>
              Voltar
            </Button>
          )}
          {step < 4 ? (
            <Button type="button" icon={ArrowRight} onClick={next}>
              Avançar
            </Button>
          ) : (
            <Button disabled={busy} type="submit" icon={CheckCircle2}>
              {busy ? "Salvando…" : "Concluir e Iniciar"}
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
