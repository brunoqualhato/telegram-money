import { useState } from "react";
import Button from "../../components/ui/Button.jsx";
import Field from "../../components/ui/Field.jsx";
import Modal from "../../components/ui/Modal.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import { api } from "../../services/api.js";

export default function DocumentForm({ close, done }) {
  const [mode, setMode] = useState("text"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.target);
    try {
      const textData = Object.fromEntries(form);
      textData.ticker = textData.ticker.toUpperCase();
      await api(mode === "pdf" ? "/documents/pdf" : "/documents", {
        method: "POST",
        body: mode === "pdf" ? form : textData,
      });
      done(
        "Documento importado. A IA processará a fila quando estiver configurada.",
      );
      close();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Importar documento" onClose={close}>
      <div className="tabs">
        <button
          onClick={() => setMode("text")}
          className={mode === "text" ? "active" : ""}
        >
          Colar texto
        </button>
        <button
          onClick={() => setMode("pdf")}
          className={mode === "pdf" ? "active" : ""}
        >
          Enviar PDF
        </button>
      </div>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="Ticker">
            <input name="ticker" required placeholder="HGLG11" maxLength={24} />
          </Field>
          {mode === "text" && (
            <Field label="Tipo">
              <select name="kind">
                <option value="relatorio">Relatório gerencial</option>
                <option value="fato_relevante">Fato relevante</option>
                <option value="noticia">Notícia</option>
                <option value="subscricao">Subscrição</option>
              </select>
            </Field>
          )}
        </div>
        <Field label="Título">
          <input name="title" minLength={3} maxLength={200} required />
        </Field>
        <Field label="URL HTTPS do documento original">
          <input
            name="source_url"
            type="url"
            pattern="https://.*"
            required
            placeholder="https://…"
          />
        </Field>
        {mode === "pdf" ? (
          <Field label="PDF com texto (até 10 MB)">
            <input name="file" type="file" accept="application/pdf" required />
          </Field>
        ) : (
          <Field label="Texto do documento">
            <textarea
              name="text"
              minLength={100}
              maxLength={200000}
              rows={8}
              required
              placeholder="Cole o conteúdo original (mínimo de 100 caracteres)…"
            />
          </Field>
        )}
        <p className="form-note">
          A coleta automática de documentos da CVM e de notícias ainda não está
          implementada. PDFs digitalizados precisam de OCR externo.
        </p>
        <ErrorBox error={error} />
        <div className="modal-footer">
          <Button secondary type="button" onClick={close}>
            Cancelar
          </Button>
          <Button disabled={busy}>
            {busy ? "Importando…" : "Importar documento"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
