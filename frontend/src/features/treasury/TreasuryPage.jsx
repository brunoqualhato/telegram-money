import { useState, useMemo } from "react";
import { Landmark, Search } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { usePagination } from "../../lib/usePagination.js";
import { money, date } from "../../lib/formatters.js";

function TreasuryRow({ row }) {
  return (
    <tr>
      <td>
        <strong>{row.title}</strong>
      </td>
      <td>{row.maturity}</td>
      <td className="positive numeric">{Number(row.rate).toFixed(2)}% a.a.</td>
      <td className="numeric">{money(row.price)}</td>
      <td>{date(row.observed_on)}</td>
    </tr>
  );
}

export default function TreasuryPage({ items }) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = useMemo(() => {
    return items.filter((row) => {
      const titleLower = row.title?.toLowerCase() || "";
      const matchType =
        typeFilter === "all" || titleLower.includes(typeFilter.toLowerCase());
      const term = search.toLowerCase();
      const matchSearch =
        !search ||
        titleLower.includes(term) ||
        row.maturity?.toLowerCase().includes(term);
      return matchType && matchSearch;
    });
  }, [items, typeFilter, search]);

  const pagination = usePagination(filtered, 10);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Títulos públicos</h3>
          <p>
            Atualização diária. A taxa tem o significado do título: nominal,
            real ou spread.
          </p>
        </div>
        <Badge>Fonte: Tesouro Nacional</Badge>
      </div>

      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por título ou vencimento"
            aria-label="Buscar títulos públicos"
          />
        </div>
        <div className="tabs">
          {[
            ["all", "Todos"],
            ["selic", "Tesouro Selic"],
            ["ipca", "Tesouro IPCA+"],
            ["prefixado", "Prefixados"],
          ].map(([val, label]) => (
            <button
              key={val}
              className={typeFilter === val ? "active" : ""}
              onClick={() => setTypeFilter(val)}
            >
              {label}
            </button>
          ))}
        </div>
        <small>{filtered.length} títulos</small>
      </div>

      {filtered.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Título</th>
                <th>Vencimento</th>
                <th>Taxa de compra</th>
                <th>Preço unitário</th>
                <th>Data-base</th>
              </tr>
            </thead>
            <tbody>
              {pagination.pagedItems.map((row) => (
                <TreasuryRow key={row.id} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty icon={Landmark} title="Nenhum título encontrado">
          O worker consulta o CSV oficial às 10h10 e 15h10. Nenhum valor
          fictício é mostrado aqui.
        </Empty>
      )}

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
