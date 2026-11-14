import { Sparkles } from "lucide-react";
import Overview from "../features/overview/Overview.jsx";
import Documents from "../features/documents/Documents.jsx";
import SettingsPage from "../features/settings/SettingsPage.jsx";
import AssetsPage from "../features/assets/AssetsPage.jsx";
import AlertsPage from "../features/alerts/AlertsPage.jsx";
import EventsPage from "../features/events/EventsPage.jsx";
import ReportsPage from "../features/reports/ReportsPage.jsx";
import HistoryPage from "../features/notifications/HistoryPage.jsx";
import TreasuryPage from "../features/treasury/TreasuryPage.jsx";
import QueuePage from "../features/queue/QueuePage.jsx";

const PAGES = {
  assets: AssetsPage,
  alerts: AlertsPage,
  events: EventsPage,
  reports: ReportsPage,
  history: HistoryPage,
  treasury: TreasuryPage,
  queue: QueuePage,
};

export default function PageContent(props) {
  const {
    page,
    data,
    me,
    setModal,
    removeAsset,
    navigate,
    connect,
    report,
    refreshing,
    refresh,
    title,
    items,
    act,
    integrations,
    reload,
    loadPage,
    notify,
  } = props;
  const Page = PAGES[page];
  return (
    <>
      {page === "overview" ? (
        <Overview
          data={data}
          me={me}
          add={() => setModal({ type: "asset" })}
          edit={(asset) => setModal({ type: "asset", asset })}
          remove={removeAsset}
          navigate={navigate}
          connect={connect}
          report={report}
          refreshing={refreshing}
          refresh={refresh}
        />
      ) : (
        <>
          <div className="page-heading">
            <div className="eyebrow">SEU RADAR PESSOAL</div>
            <h1>
              {title}
              <span>.</span>
            </h1>
            <p>
              {
                {
                  assets: "Os investimentos que merecem a sua atenção.",
                  alerts:
                    "Escolha o que importa. Receba o sinal na hora certa.",
                  events:
                    "Datas e distribuições, com a fonte sempre por perto.",
                  documents:
                    "Menos páginas. Mais contexto para entender seus ativos.",
                  reports: "Uma fotografia da carteira, a cada período.",
                  history: "Cada evento, cada tentativa, cada entrega.",
                  settings: "Seu painel, suas preferências, seu ritmo.",
                  treasury:
                    "Taxas de compra da base oficial do Tesouro Nacional.",
                  queue:
                    "Controle de concorrência, limites de máquina e tarefas em espera.",
                }[page]
              }
            </p>
          </div>
          {data.demo && (
            <div className="demo-banner">
              <Sparkles size={17} /> Modo demonstração · valores ilustrativos ·
              envio desativado
            </div>
          )}

          {Page && <Page {...props} />}
          {page === "documents" && (
            <Documents
              items={items}
              add={() => setModal({ type: "document" })}
              summarize={(doc) => act(`/documents/${doc.id}/summarize`)}
              fetchNews={() => act("/news/refresh")}
            />
          )}

          {page === "settings" && (
            <SettingsPage
              key={me.email}
              me={me}
              integrations={integrations}
              connect={connect}
              act={act}
              reload={async () => {
                await reload();
                await loadPage();
              }}
              toast={notify}
            />
          )}
        </>
      )}
    </>
  );
}
