import { useState } from "react";
import { Bell } from "lucide-react";
import Button from "../../components/ui/Button.jsx";
import Field from "../../components/ui/Field.jsx";
import Modal from "../../components/ui/Modal.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import { RULES } from "../../lib/constants.js";
import { api } from "../../services/api.js";

export default function RuleForm({ assets, close, done }) {
  const [kind, setKind] = useState("price_above"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    const values = Object.fromEntries(new FormData(event.target));
    try {
      await api("/rules", {
        method: "POST",
        body: {
          asset_id: Number(values.asset_id),
          kind,
          threshold: Number(values.threshold || 1),
          enabled: true,
        },
      });
      done("Alerta criado. Ele será avaliado na próxima cotação válida.");
      close();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Criar um alerta" onClose={close}>
      <form onSubmit={submit}>
        <Field label="Ativo">
          <select name="asset_id" required>
            {assets.map((a) => (
              <option key={a.id} value={a.id}>
                {a.ticker} · {a.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Quando me avisar">
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            {Object.entries(RULES).map(([key, value]) => (
              <option key={key} value={key}>
                {value}
              </option>
            ))}
          </select>
        </Field>
        {!kind.includes("52w") && (
          <Field
            label={
              kind.startsWith("price")
                ? "Preço-alvo (moeda do ativo)"
                : "Variação diária absoluta (%)"
            }
          >
            <input
              name="threshold"
              type="number"
              min="0.00000001"
              step="any"
              required
              placeholder="Ex.: 40,00"
            />
          </Field>
        )}
        <div className="notice">
          <Bell size={17} /> O alerta dispara uma vez e se rearma quando a
          condição deixa de ser atendida. Cotações com mais de 15 minutos não
          geram novos disparos.
        </div>
        <ErrorBox error={error} />
        <div className="modal-footer">
          <Button secondary type="button" onClick={close}>
            Cancelar
          </Button>
          <Button disabled={busy || !assets.length}>
            {busy ? "Criando…" : "Criar alerta"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
