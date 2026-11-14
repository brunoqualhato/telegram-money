import { useState } from "react";
import Button from "./Button.jsx";
import Modal from "./Modal.jsx";

export default function ConfirmDialog({ title, children, onConfirm, onClose }) {
  const [busy, setBusy] = useState(false);
  async function confirm() {
    setBusy(true);
    try {
      await onConfirm();
      onClose();
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title={title}
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <p className="confirm-text">{children}</p>
      <div className="modal-footer">
        <Button secondary disabled={busy} onClick={onClose}>
          Cancelar
        </Button>
        <Button disabled={busy} onClick={confirm}>
          {busy ? "Aguarde…" : "Confirmar"}
        </Button>
      </div>
    </Modal>
  );
}
