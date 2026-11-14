import AssetFields from "./AssetFields.jsx";
import { useState } from "react";
import Button from "../../components/ui/Button.jsx";
import Modal from "../../components/ui/Modal.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import { api } from "../../services/api.js";

export default function AssetForm({ asset, close, done }) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    const form = Object.fromEntries(new FormData(event.target));
    form.quantity = Number(form.quantity);
    form.average_price = Number(form.average_price);
    try {
      await api(asset ? `/assets/${asset.id}` : "/assets", {
        method: asset ? "PUT" : "POST",
        body: form,
      });
      done("Ativo salvo na sua lista.");
      close();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title={asset ? `Editar ${asset.ticker}` : "Adicionar ativo"}
      onClose={close}
    >
      <form onSubmit={submit}>
        <AssetFields asset={asset} />
        <p className="form-note">
          A coleta inicial cobre a B3 pela brapi. Cripto, câmbio e exterior
          ainda não têm coletores. Informar quantidades não registra operações.
        </p>
        <ErrorBox error={error} />
        <div className="modal-footer">
          <Button type="button" secondary onClick={close}>
            Cancelar
          </Button>
          <Button disabled={busy}>{busy ? "Salvando…" : "Salvar ativo"}</Button>
        </div>
      </form>
    </Modal>
  );
}
