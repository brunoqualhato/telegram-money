import ActivityList from "./ActivityList.jsx";
import { STATUS } from "../../lib/constants.js";

export default function HistoryPage({ items, filter, setFilter, retry }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h3>Histórico de notificações</h3>
        <select
          aria-label="Filtrar situação"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">Todas as situações</option>
          {Object.entries(STATUS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>
      <ActivityList
        items={items.filter((i) => filter === "all" || i.status === filter)}
        all
        retry={retry}
      />
    </section>
  );
}
