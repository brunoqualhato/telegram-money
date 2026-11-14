import { CheckCircle2, X } from "lucide-react";
import Logo from "../components/Logo.jsx";
import IconButton from "../components/ui/IconButton.jsx";
import ErrorBox from "../components/ui/ErrorBox.jsx";
import Login from "../features/auth/Login.jsx";
import Sidebar from "../components/layout/Sidebar.jsx";
import Header from "../components/layout/Header.jsx";
import PageContent from "./PageContent.jsx";
import AppDialogs from "./AppDialogs.jsx";
import useApp from "./useApp.js";

export default function App() {
  const panel = useApp();
  const {
    loading,
    me,
    reload,
    error,
    setError,
    mobile,
    setMobile,
    toast,
    setToast,
  } = panel;
  if (loading)
    return (
      <div className="boot">
        <Logo />
        <p>Preparando seu radar…</p>
      </div>
    );
  if (!me)
    return (
      <>
        <Login onLogin={() => reload().catch((e) => setError(e.message))} />
        {error && (
          <div className="floating-error" role="alert">
            {error}
          </div>
        )}
      </>
    );
  return (
    <div className="app-shell">
      <Sidebar {...panel} />
      {mobile && (
        <button
          className="sidebar-overlay"
          aria-label="Fechar menu"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="main-shell">
        <Header {...panel} />
        <main className="content">
          {error && (
            <div className="page-error">
              <ErrorBox error={error} />
              <IconButton label="Fechar erro" onClick={() => setError("")}>
                <X size={17} />
              </IconButton>
            </div>
          )}
          <PageContent {...panel} />
          <footer className="footer">
            <span>
              telegrammoney <span>·</span> Seu radar pessoal de investimentos.
            </span>
            <small>Informação para acompanhar. Decisões sempre suas.</small>
          </footer>
        </main>
      </div>
      <AppDialogs {...panel} />
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={19} />
          {toast}
          <button aria-label="Fechar aviso" onClick={() => setToast("")}>
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
