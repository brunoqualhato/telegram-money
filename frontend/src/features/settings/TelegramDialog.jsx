import { Send, ExternalLink } from "lucide-react";
import Modal from "../../components/ui/Modal.jsx";
export default function TelegramDialog({ modal, close }) {
  return (
    <Modal title="Conecte seu Telegram" onClose={close}>
      <div className="connect-modal">
        <span className="telegram-icon">
          <Send size={30} />
        </span>
        <h3>Seu canal está a um passo.</h3>
        <p>
          Abra o link no Telegram e toque em <strong>Iniciar</strong>. O código
          vale por 15 minutos e pode ser usado uma única vez.
        </p>
        <a className="button" href={modal.url} target="_blank" rel="noreferrer">
          Abrir meu bot no Telegram <ExternalLink size={16} />
        </a>
        <small>
          O processo do bot precisa estar rodando para concluir a conexão.
        </small>
      </div>
    </Modal>
  );
}
