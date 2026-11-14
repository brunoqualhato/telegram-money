import { useState, useMemo } from "react";
import { Search } from "lucide-react";
import ActivityList from "./ActivityList.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { usePagination } from "../../lib/usePagination.js";
import { STATUS } from "../../lib/constants.js";

export default function HistoryPage({ items, filter, setFilter, retry }) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return items.filter((i) => {
      const matchFilter = filter === "all" || i.status === filter;
      const term = search.toLowerCase();
      const matchSearch =
        !search ||
        i.title?.toLowerCase().includes(term) ||
        i.body?.toLowerCase().includes(term) ||
        i.ticker?.toLowerCase().includes(term);
      return matchFilter && matchSearch;
    });
  }, [items, filter, search]);

  const pagination = usePagination(filtered, 10);

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
      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar no histórico de notificações"
            aria-label="Buscar notificações"
          />
        </div>
        <small>{filtered.length} notificações</small>
      </div>
      <ActivityList items={pagination.pagedItems} all retry={retry} />
      <Pagination
        page={pagination.page}
        pageSize={pagination.pageSize}
        totalItems={pagination.totalItems}
        onPageChange={pagination.setPage}
        onPageSizeChange={pagination.setPageSize}
      />
    </section>
  );
}
