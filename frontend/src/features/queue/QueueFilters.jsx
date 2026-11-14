import { Search } from "lucide-react";

export default function QueueFilters({
  search,
  setSearch,
  statusFilter,
  setStatusFilter,
  categoryFilter,
  setCategoryFilter,
}) {
  return (
    <div className="filter-bar">
      <div className="search-box">
        <Search size={16} />
        <input
          type="text"
          placeholder="Buscar tarefa por título, alvo ou tipo..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Buscar na fila"
        />
      </div>

      <div className="tabs" role="tablist" aria-label="Filtrar por status">
        {[
          ["all", "Todos"],
          ["pending", "Aguardando"],
          ["running", "Processando"],
          ["completed", "Concluídos"],
          ["failed", "Falhas"],
        ].map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={statusFilter === key ? "active" : ""}
            onClick={() => setStatusFilter(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="tabs" role="tablist" aria-label="Filtrar por categoria">
        {[
          ["all", "Todas categorias"],
          ["ai", "IA Local"],
          ["api", "APIs & Mercado"],
        ].map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={categoryFilter === key ? "active" : ""}
            onClick={() => setCategoryFilter(key)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
