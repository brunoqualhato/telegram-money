import Field from "../../components/ui/Field.jsx";
export default function LoginCredentials({ demo }) {
  return (
    <>
      <Field label="E-mail">
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          defaultValue={demo ? "demo@example.com" : ""}
          placeholder="voce@exemplo.com"
        />
      </Field>
      <Field label="Senha">
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          defaultValue={demo ? "demonstracao-local" : ""}
          placeholder="Sua senha de acesso"
        />
      </Field>
    </>
  );
}
