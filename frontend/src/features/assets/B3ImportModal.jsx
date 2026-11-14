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
          Envie a planilha exportada da Área do Investidor da B3 (.xlsx ou
          .csv): suporta tanto a <strong>Posição de Custódia</strong> quanto o{" "}
          <strong>Extrato de Movimentação</strong>. No extrato, o preço médio e
          as quantidades são calculados automaticamente com base no histórico de
          compras e vendas.
        </p>
        <div className="field">
          <label htmlFor="b3-file">Planilha da B3 (.xlsx ou .csv)</label>
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
            Atualizar preço médio dos ativos existentes com o custo calculado no
            extrato de movimentação
          </span>
        </label>
        <p className="form-note">
          Custódia atualiza quantidades, sem usar o preço de fechamento como
          custo. Para calcular preço médio, envie o histórico completo de
          movimentações; um extrato parcial pode gerar posições incompletas.
        </p>
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
