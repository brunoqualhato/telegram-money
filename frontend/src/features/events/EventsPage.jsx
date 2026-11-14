import { Plus, RefreshCw, ExternalLink, Landmark } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import { money } from "../../lib/formatters.js";
import { date } from "../../lib/formatters.js";

export default function EventsPage({ items, setModal, act }) {
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
      {items.length ? (
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
              {items.map((event) => (
                <tr key={event.id}>
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
                    <Badge
                      tone={
                        event.status === "confirmed"
                          ? "green"
                          : event.status === "cancelled"
                            ? "red"
                            : ""
                      }
                    >
                      {
                        {
                          confirmed: "Confirmado",
                          estimated: "Estimado",
                          cancelled: "Cancelado",
                        }[event.status]
                      }
                    </Badge>
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
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty icon={Landmark} title="Nenhum provento coletado">
          O worker consulta a brapi periodicamente. Você também pode registrar
          eventos com sua fonte original.
        </Empty>
      )}
    </section>
  );
}
