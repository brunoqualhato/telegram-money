import { ChartPie } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import { money, percentage } from "../../lib/formatters.js";

function AllocationRing({ allocations }) {
  let offset = 0;
  return (
    <div className="allocation-donut">
      <svg
        viewBox="0 0 220 220"
        role="img"
        aria-label="Distribuição do patrimônio por classe de ativo"
      >
        <circle
          cx="110"
          cy="110"
          r="84"
          fill="none"
          stroke="#eef1e9"
          strokeWidth="24"
        />
        {allocations.map((item) => {
          const start = offset;
          offset += item.weight;
          return (
            <circle
              key={item.key}
              cx="110"
              cy="110"
              r="84"
              fill="none"
              pathLength="100"
              stroke={item.color}
              strokeWidth="24"
              strokeDasharray={`${item.weight} ${100 - item.weight}`}
              strokeDashoffset={-start}
              transform="rotate(-90 110 110)"
            >
              <title>{`${item.label}: ${percentage(item.weight)}`}</title>
            </circle>
          );
        })}
      </svg>
      <div>
        <strong>{allocations.length}</strong>
        <span>classes de ativos</span>
      </div>
    </div>
  );
}

export default function AllocationChart({ metrics }) {
  return (
    <section className="panel allocation-panel">
      <div className="panel-heading">
        <div>
          <h3>Alocação da carteira</h3>
          <p>Como seu patrimônio está distribuído</p>
        </div>
        <ChartPie size={19} />
      </div>
      {metrics.total > 0 ? (
        <>
          <AllocationRing allocations={metrics.allocations} />
          <ul className="allocation-legend">
            {metrics.allocations.map((item) => (
              <li key={item.key}>
                <i style={{ background: item.color }} />
                <span>
                  {item.label}
                  <small>{money(item.value)}</small>
                </span>
                <strong>{percentage(item.weight)}</strong>
              </li>
            ))}
          </ul>
          <p className="panel-note">
            Participação sobre as posições cotadas em BRL.
          </p>
        </>
      ) : (
        <Empty icon={ChartPie} title="Sua distribuição começa aqui">
          Adicione posições com quantidade e cotação em reais.
        </Empty>
      )}
    </section>
  );
}
