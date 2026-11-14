import {
  ChevronDown,
  LogOut,
  Settings,
  ShieldCheck,
  Wallet,
  Landmark,
} from "lucide-react";
import Logo from "../Logo.jsx";
import IconButton from "../ui/IconButton.jsx";
import { NAV } from "../../lib/constants.js";
import { api } from "../../services/api.js";

export default function Sidebar({
  mobile,
  page,
  navigate,
  data,
  me,
  setMe,
  setError,
}) {
  return (
    <aside className={`sidebar ${mobile ? "open" : ""}`}>
      <Logo />
      <div className="workspace">
        <span className="workspace-icon">
          <Wallet size={18} />
        </span>
        <div>
          <strong>Minha carteira</strong>
          <small>Espaço pessoal</small>
        </div>
        <ChevronDown size={15} />
      </div>
      <div className="nav-label">ACOMPANHAMENTO</div>
      <nav aria-label="Menu principal">
        {NAV.map(([key, label, Icon]) => (
          <button
            key={key}
            className={page === key ? "selected" : ""}
            onClick={() => navigate(key)}
          >
            <Icon size={19} />
            {label}
            {key === "alerts" && (
              <span className="nav-count">{data.active_rules || 0}</span>
            )}
          </button>
        ))}
        <button
          className={page === "treasury" ? "selected" : ""}
          onClick={() => navigate("treasury")}
        >
          <Landmark size={19} />
          Tesouro Direto
        </button>
      </nav>
      <div className="sidebar-bottom">
        <div className="private-note">
          <ShieldCheck size={18} />
          <div>
            <strong>Um espaço só seu</strong>
            <small>Monitoramento pessoal e privado.</small>
          </div>
        </div>
        <button
          className={`settings-link ${page === "settings" ? "selected" : ""}`}
          onClick={() => navigate("settings")}
        >
          <Settings size={19} />
          Configurações
        </button>
        <div className="profile">
          <span className="avatar">{me.email[0].toUpperCase()}</span>
          <div>
            <strong>Meu acesso</strong>
            <small>{me.email}</small>
          </div>
          <IconButton
            label="Sair do painel"
            onClick={async () => {
              try {
                await api("/auth/logout", { method: "POST" });
                setMe(null);
              } catch (e) {
                setError(e.message);
              }
            }}
          >
            <LogOut size={17} />
          </IconButton>
        </div>
      </div>
    </aside>
  );
}
