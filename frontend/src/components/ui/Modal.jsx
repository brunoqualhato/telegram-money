import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import IconButton from "./IconButton.jsx";

export default function Modal({ title, children, onClose }) {
  const ref = useRef(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
    >
      <div className="modal-header">
        <h2>{title}</h2>
        <IconButton label="Fechar janela" onClick={onClose}>
          <X size={20} />
        </IconButton>
      </div>
      {children}
    </dialog>
  );
}
