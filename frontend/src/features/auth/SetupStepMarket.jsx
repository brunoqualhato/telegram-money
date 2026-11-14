import Field from "../../components/ui/Field.jsx";

export default function SetupStepMarket({ data, onChange }) {
  return (
    <div className="setup-step">
      <p className="form-note">
        O sistema já inclui conectores abertos da B3 (Status Invest / Tesouro
        Nacional) para cotações e proventos sem custo.
      </p>
      <Field label="Token brapi.dev (opcional)">
        <input
          type="text"
          placeholder="Deixe em branco para usar o conector aberto B3 gratuito"
          value={data.brapi_token}
          onChange={(e) => onChange("brapi_token", e.target.value)}
        />
      </Field>
      <Field label="Intervalo de Coleta de Cotações (segundos)">
        <input
          type="number"
          min={30}
          max={3600}
          value={data.poll_seconds}
          onChange={(e) => onChange("poll_seconds", Number(e.target.value))}
        />
      </Field>
    </div>
  );
}
