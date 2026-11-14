import { useState } from "react";
import Field from "../../components/ui/Field.jsx";
import Button from "../../components/ui/Button.jsx";
import { api } from "../../services/api.js";

function getPasswordError(newPassword, confirmPassword, currentPassword) {
  if (!newPassword) return null;
  if (newPassword.length < 12) {
    return "A nova senha deve ter no mínimo 12 caracteres.";
  }
  if (newPassword !== confirmPassword) {
    return "As novas senhas não conferem.";
  }
  if (!currentPassword) {
    return "Informe a senha atual para alterar a senha.";
  }
  return null;
}

export default function ProfileForm({ me, reload, toast }) {
  const [email, setEmail] = useState(me?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function saveProfile(e) {
    e.preventDefault();
    setError("");
    const validationError = getPasswordError(
      newPassword,
      confirmPassword,
      currentPassword,
    );
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    try {
      const payload = {
        email: email !== me?.email ? email : undefined,
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      };
      await api("/auth/profile", { method: "PUT", body: payload });
      toast("Perfil de acesso atualizado.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      await reload();
    } catch (err) {
      setError(err.message || "Erro ao atualizar perfil");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={saveProfile} style={{ marginTop: "16px" }}>
      <hr style={{ margin: "16px 0", borderColor: "var(--border-subtle)" }} />
      <h4 style={{ margin: "0 0 8px", fontSize: "14px", fontWeight: "600" }}>
        Credenciais do Administrador
      </h4>
      <Field label="E-mail de Acesso">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Field>
      <Field label="Senha Atual (necessária para alterar a senha)">
        <input
          type="password"
          placeholder="••••••••••••"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
      </Field>
      <div className="form-grid">
        <Field label="Nova Senha (mín. 12 caracteres)">
          <input
            type="password"
            minLength={12}
            placeholder="••••••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </Field>
        <Field label="Confirmar Nova Senha">
          <input
            type="password"
            minLength={12}
            placeholder="••••••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </Field>
      </div>
      {error && (
        <div className="error-box" style={{ marginBottom: "12px" }}>
          {error}
        </div>
      )}
      <Button small disabled={saving}>
        {saving ? "Salvando…" : "Atualizar Credenciais"}
      </Button>
    </form>
  );
}
