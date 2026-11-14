import { useState, useMemo } from "react";
import { Plus, RefreshCw, ExternalLink, Landmark, Search } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import { usePagination } from "../../lib/usePagination.js";
import { money, date } from "../../lib/formatters.js";

function EventRow({ event }) {
  const tone =
    event.status === "confirmed"
      ? "green"
      : event.status === "cancelled"
        ? "red"
        : "";
  const label =
    {
      confirmed: "Confirmado",
      estimated: "Estimado",
      cancelled: "Cancelado",
    }[event.status] || event.status;

  return (
    <tr>
      <td>
        <strong>{event.ticker}</strong>
        <small className="quote-time">
          {event.kind} · revisão {event.revision}
        </small>
      </td>
      <td className="numeric">
        {event.amount !== null ? money(event.amount) : "—"}
      </td>
      <td>{date(event.com_date)}</td>
      <td>{date(event.payment_date)}</td>
      <td>
        <Badge tone={tone}>{label}</Badge>
      </td>
      <td>
        <a
          className="text-button"
          href={event.source_url}
          target="_blank"
          rel="noreferrer"
        >
          Original <ExternalLink size={13} />
        </a>
      </td>
    </tr>
  );
}

export default function EventsPage({ items, setModal, act }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return items.filter((ev) => {
      const matchStatus = statusFilter === "all" || ev.status === statusFilter;
      const term = search.toLowerCase();
      const matchSearch =
        !search ||
        ev.ticker?.toLowerCase().includes(term) ||
        ev.kind?.toLowerCase().includes(term);
      return matchStatus && matchSearch;
    });
  }, [items, statusFilter, search]);

  const pagination = usePagination(filtered, 10);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Calendário de eventos</h3>
          <p>Valores por unidade. Elegibilidade da posição não verificada.</p>
        </div>
        <div className="button-row">
          {act && (
            <Button
              secondary
              icon={RefreshCw}
              onClick={() => act("/events/refresh")}
            >
              Buscar proventos
            </Button>
          )}
          <Button icon={Plus} onClick={() => setModal({ type: "event" })}>
            Registrar evento
          </Button>
        </div>
      </div>

      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por ativo ou tipo de evento"
            aria-label="Buscar eventos"
          />
        </div>
        <div className="tabs">
          {[
            ["all", "Todos"],
            ["confirmed", "Confirmados"],
            ["estimated", "Estimados"],
            ["cancelled", "Cancelados"],
          ].map(([val, name]) => (
            <button
              key={val}
              className={statusFilter === val ? "active" : ""}
              onClick={() => setStatusFilter(val)}
            >
              {name}
            </button>
          ))}
        </div>
        <small>{filtered.length} eventos</small>
      </div>

      {filtered.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Ativo / evento</th>
                <th>Valor por unidade</th>
                <th>Data-com</th>
                <th>Pagamento</th>
                <th>Situação</th>
                <th>Fonte</th>
              </tr>
            </thead>
            <tbody>
              {pagination.pagedItems.map((event) => (
                <EventRow key={event.id} event={event} />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty icon={Landmark} title="Nenhum provento encontrado">
          O worker consulta a brapi periodicamente. Você também pode registrar
          eventos com sua fonte original.
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
