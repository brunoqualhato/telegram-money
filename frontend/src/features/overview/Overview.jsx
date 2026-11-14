import { ArrowRight, Plus, RefreshCw, Sparkles } from "lucide-react";
import Button from "../../components/ui/Button.jsx";
import AssetTable from "../assets/AssetTable.jsx";
import ActivityList from "../notifications/ActivityList.jsx";
import PortfolioChart from "./PortfolioChart.jsx";
import OverviewStats from "./OverviewStats.jsx";
import OverviewAside from "./OverviewAside.jsx";

export default function Overview({
  data,
  me,
  add,
  edit,
  remove,
  navigate,
  connect,
  report,
  refreshing,
  refresh,
}) {
  const assets = data.assets || [],
    classes = {};
  assets.forEach((a) => {
    if (a.value)
      classes[a.asset_class] = (classes[a.asset_class] || 0) + a.value;
  });
  return (
    <>
      <div className="welcome">
        <div className="eyebrow">
          <span className="status-dot" /> SEU MERCADO, EM PERSPECTIVA
        </div>
        <div className="welcome-title">
          <h1>
            Seu radar está aqui<span>.</span>
          </h1>
          <Button
            secondary
            icon={RefreshCw}
            onClick={refresh}
            disabled={refreshing}
          >
            {refreshing ? "Agendando…" : "Atualizar cotações"}
          </Button>
        </div>
        <p>Acompanhe seus ativos. Deixe que os alertas encontrem você.</p>
      </div>
      {data.demo && (
        <div className="demo-banner">
          <Sparkles size={17} />
          <strong>Modo demonstração</strong>
          <span>
            Valores e eventos ilustrativos. Nenhuma mensagem é enviada.
          </span>
        </div>
      )}
      <OverviewStats data={data} assets={assets} />
      <div className="dashboard-grid">
        <div className="dashboard-main">
          <PortfolioChart assets={assets} />
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Seus ativos, de perto</h3>
                <p>O essencial da sua lista de acompanhamento.</p>
              </div>
              <button
                className="text-button"
                onClick={() => navigate("assets")}
              >
                Ver todos <ArrowRight size={15} />
              </button>
            </div>
            <AssetTable
              assets={assets.slice(0, 5)}
              edit={edit}
              remove={remove}
              compact
            />
            {!assets.length && (
              <div className="empty-bottom">
                <Button icon={Plus} onClick={add}>
                  Adicionar primeiro ativo
                </Button>
              </div>
            )}
          </section>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Últimos sinais</h3>
                <p>Eventos detectados e situação da entrega.</p>
              </div>
              <button
                className="text-button"
                onClick={() => navigate("history")}
              >
                Ver histórico <ArrowRight size={15} />
              </button>
            </div>
            <ActivityList items={data.latest_notifications || []} />
          </section>
        </div>
        <OverviewAside
          data={data}
          classes={classes}
          me={me}
          navigate={navigate}
          connect={connect}
          report={report}
        />
      </div>
    </>
  );
}
