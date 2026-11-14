import { useState } from "react";
import Button from "../../components/ui/Button.jsx";
import Field from "../../components/ui/Field.jsx";
import Modal from "../../components/ui/Modal.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";

import { api } from "../../services/api.js";

export default function EventForm({ close, done }) {
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.target));
    for (const key of [
      "amount",
      "announced_on",
      "com_date",
      "ex_date",
      "payment_date",
    ])
      form[key] = form[key] || null;
    form.ticker = form.ticker.toUpperCase();
    try {
      await api("/events", { method: "POST", body: form });
      done(
        "Evento importado. O mesmo identificador atualiza o evento existente.",
      );
      close();
    } catch (e) {
      setError(e.message);
    }
  }
  return (
    <Modal title="Registrar evento corporativo" onClose={close}>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="Ticker">
            <input name="ticker" required maxLength={24} />
          </Field>
          <Field label="Tipo">
            <select name="kind">
              {[
                "dividendo",
                "jcp",
                "rendimento",
                "amortizacao",
                "desdobramento",
                "grupamento",
                "subscricao",
              ].map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <Field
          label="Identificador estável na fonte"
          note="Reutilize este identificador ao corrigir ou cancelar o evento."
        >
          <input name="source_id" required maxLength={200} />
        </Field>
        <div className="form-grid">
          <Field label="Valor por unidade">
            <input name="amount" type="number" min="0" step="any" />
          </Field>
          <Field label="Situação">
            <select name="status">
              <option value="confirmed">Confirmado</option>
              <option value="estimated">Estimado</option>
              <option value="cancelled">Cancelado</option>
            </select>
          </Field>
        </div>
        <div className="form-grid">
          {[
            ["announced_on", "Anúncio"],
            ["com_date", "Data-com"],
            ["ex_date", "Data-ex"],
            ["payment_date", "Pagamento"],
          ].map(([key, label]) => (
            <Field key={key} label={label}>
              <input name={key} type="date" />
            </Field>
          ))}
        </div>
        <Field label="Fonte original (HTTPS)">
          <input name="source_url" type="url" required pattern="https://.*" />
        </Field>
        <ErrorBox error={error} />
        <div className="modal-footer">
          <Button type="button" secondary onClick={close}>
            Cancelar
          </Button>
          <Button>Salvar evento</Button>
        </div>
      </form>
    </Modal>
  );
}
