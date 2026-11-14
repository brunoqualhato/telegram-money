import { ChevronDown, FileText, Plus, Download } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import { date } from "../../lib/formatters.js";

export default function ReportsPage({ items, report }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Relatórios da carteira</h3>
          <p>Diários, semanais, mensais e sob demanda.</p>
        </div>
        <Button icon={Plus} onClick={report}>
          Gerar agora
        </Button>
      </div>
      {items.length ? (
        items.map((item) => (
          <details className="report-row" key={item.id}>
            <summary>
              <span className="document-icon">
                <FileText size={20} />
              </span>
              <span>
                <strong>
                  {
                    {
                      demand: "Resumo sob demanda",
                      daily: "Fechamento diário",
                      weekly: "Resumo semanal",
                      monthly: "Resumo mensal",
                    }[item.kind]
                  }
                </strong>
                <small>{date(item.created_at)}</small>
              </span>
              <ChevronDown size={17} />
            </summary>
            <pre>{item.body}</pre>
            <Button
              secondary
              small
              icon={Download}
              onClick={() => {
                const blob = new Blob([item.body], {
                    type: "text/plain;charset=utf-8",
                  }),
                  url = URL.createObjectURL(blob),
                  a = document.createElement("a");
                a.href = url;
                a.download = `relatorio-${item.id}.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              Baixar relatório
            </Button>
          </details>
        ))
      ) : (
        <Empty icon={FileText} title="A história da sua carteira, organizada">
          Gere o primeiro resumo ou aguarde o fechamento programado.
        </Empty>
      )}
    </section>
  );
}
