import Field from "../../components/ui/Field.jsx";

export default function SetupStepAdmin({ data, onChange }) {
  return (
    <div className="setup-step">
      <Field label="E-mail do Administrador">
        <input
          type="email"
          required
          placeholder="voce@exemplo.com"
          value={data.email}
          onChange={(e) => onChange("email", e.target.value)}
        />
      </Field>
      <Field label="Senha de Acesso (mínimo 12 caracteres)">
        <input
          type="password"
          required
          minLength={12}
          placeholder="••••••••••••"
          value={data.password}
          onChange={(e) => onChange("password", e.target.value)}
        />
      </Field>
      <Field label="Confirmar Senha">
        <input
          type="password"
          required
          minLength={12}
          placeholder="••••••••••••"
          value={data.confirm_password}
          onChange={(e) => onChange("confirm_password", e.target.value)}
        />
      </Field>
      <Field label="Fuso Horário">
        <input
          type="text"
          value={data.timezone}
          onChange={(e) => onChange("timezone", e.target.value)}
        />
      </Field>
    </div>
  );
}
