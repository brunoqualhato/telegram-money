import { Landmark } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import { money } from "../../lib/formatters.js";
import { date } from "../../lib/formatters.js";

export default function TreasuryPage({ items }) {
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
      {items.length ? (
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
              {items.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>{row.title}</strong>
                  </td>
                  <td>{row.maturity}</td>
                  <td className="positive numeric">
                    {Number(row.rate).toFixed(2)}% a.a.
                  </td>
                  <td className="numeric">{money(row.price)}</td>
                  <td>{date(row.observed_on)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty icon={Landmark} title="Taxas ainda não coletadas">
          O worker consulta o CSV oficial às 10h10 e 15h10. Nenhum valor
          fictício é mostrado aqui.
        </Empty>
      )}
    </section>
  );
}
