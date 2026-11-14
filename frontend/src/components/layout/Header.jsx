import { Bell, ChevronRight, Menu } from "lucide-react";
import IconButton from "../ui/IconButton.jsx";

export default function Header({
  title,
  mobile,
  setMobile,
  navigate,
  me,
  totalNotifications,
}) {
  return (
    <header className="topbar">
      <div className="breadcrumb">
        <IconButton
          label="Abrir menu"
          className="mobile-menu icon-button"
          onClick={() => setMobile(!mobile)}
        >
          <Menu size={20} />
        </IconButton>
        <span>Minha carteira</span>
        <ChevronRight size={14} />
        <strong>{title}</strong>
      </div>
      <div className="topbar-actions">
        <span className="today">
          {new Date().toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "long",
            year: "numeric",
          })}
        </span>
        <button
          className={`connection-pill ${me.telegram_connected ? "connected" : ""}`}
          onClick={() => navigate("settings")}
        >
          <span className="status-dot" />
          {me.telegram_connected
            ? "Telegram conectado"
            : "Telegram não conectado"}
        </button>
        <IconButton
          label="Ver histórico de alertas"
          onClick={() => navigate("history")}
        >
          <Bell size={19} />
          {totalNotifications > 0 && <i className="notification-dot" />}
        </IconButton>
      </div>
    </header>
  );
}
