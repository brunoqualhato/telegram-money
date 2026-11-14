import { ArrowRight, Plus, RefreshCw, Sparkles } from "lucide-react";
import Button from "../../components/ui/Button.jsx";
import AssetTable from "../assets/AssetTable.jsx";
import ActivityList from "../notifications/ActivityList.jsx";
import PortfolioChart from "./PortfolioChart.jsx";
import PortfolioHistoryChart from "./PortfolioHistoryChart.jsx";
import ProfitLossChart from "./ProfitLossChart.jsx";
import OverviewStats from "./OverviewStats.jsx";
import OverviewAside from "./OverviewAside.jsx";
import AllocationChart from "./AllocationChart.jsx";
import DailyMovers from "./DailyMovers.jsx";
import ConcentrationChart from "./ConcentrationChart.jsx";
import { portfolioMetrics } from "./portfolioMetrics.js";
import "../../styles/dashboard.css";

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
  const assets = data.assets || [];
  const metrics = portfolioMetrics(assets);
  return (
    <div className="portfolio-dashboard">
      <div className="welcome">
        <div className="eyebrow">
          <span className="status-dot" /> VISÃO CONSOLIDADA DA CARTEIRA
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
            aria-label="Atualizar cotações"
          >
            {refreshing ? "Agendando…" : "Atualizar cotações"}
          </Button>
        </div>
        <p>
          Patrimônio, distribuição e desempenho. Sua carteira, por todos os
          ângulos.
        </p>
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
      <OverviewStats metrics={metrics} />
      <div className="overview-top-grid">
        <PortfolioHistoryChart overviewData={data} metrics={metrics} />
        <AllocationChart metrics={metrics} />
      </div>
      <div className="overview-charts-grid">
        <DailyMovers metrics={metrics} />
        <ProfitLossChart metrics={metrics} />
      </div>
      <div className="overview-top-grid overview-secondary-grid">
        <PortfolioChart assets={assets} />
        <ConcentrationChart metrics={metrics} />
      </div>
      <div className="dashboard-grid">
        <div className="dashboard-main">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Seus ativos, de perto</h3>
                <p>As maiores posições primeiro. Cotações e valores em BRL.</p>
              </div>
              <button
                type="button"
                className="text-button"
                onClick={() => navigate("assets")}
              >
                Ver todos <ArrowRight size={15} />
              </button>
            </div>
            <AssetTable
              assets={metrics.positions.slice(0, 5)}
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
                type="button"
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
          metrics={metrics}
          me={me}
          navigate={navigate}
          connect={connect}
          report={report}
        />
      </div>
      <p className="portfolio-footnote">
        Dados sujeitos a atraso. Consulte horário e fonte nas posições.
        Histórico estimado, sem reconstrução de operações.
      </p>
    </div>
  );
}
