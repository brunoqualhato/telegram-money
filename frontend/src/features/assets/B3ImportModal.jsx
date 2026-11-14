import { useState } from "react";
import Button from "../../components/ui/Button.jsx";
import Modal from "../../components/ui/Modal.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import { api } from "../../services/api.js";

export default function B3ImportModal({ close, done }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.target);
    try {
      const result = await api("/assets/import-b3", {
        method: "POST",
        body: form,
      });
      done(result.message || "Importação concluída.");
      close();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Importar carteira da B3" onClose={close}>
      <form onSubmit={submit}>
        <p className="form-note">
          Envie a planilha de posição exportada da Área do Investidor da B3
          (.xlsx ou .csv). As abas de Ações, Fundos Imobiliários, BDRs e ETFs
          serão lidas e consolidadas automaticamente.
        </p>
        <div className="field">
          <label htmlFor="b3-file">Arquivo de posição (.xlsx ou .csv)</label>
          <input
            id="b3-file"
            name="file"
            type="file"
            accept=".xlsx,.csv"
            required
            onChange={(e) => setFileName(e.target.files[0]?.name || "")}
          />
        </div>
        <label className="check-field" style={{ marginTop: "12px" }}>
          <input type="checkbox" name="update_average_price" value="true" />
          <span>
            Atualizar preço médio com o preço de fechamento da planilha
          </span>
        </label>
        <ErrorBox error={error} />
        <div className="modal-footer">
          <Button type="button" secondary onClick={close}>
            Cancelar
          </Button>
          <Button disabled={busy || !fileName}>
            {busy ? "Importando…" : "Importar posições"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
