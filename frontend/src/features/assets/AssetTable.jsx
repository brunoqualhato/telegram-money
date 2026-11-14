import {
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  Trash2,
  Pencil,
} from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import IconButton from "../../components/ui/IconButton.jsx";
import { money } from "../../lib/formatters.js";
import { pct } from "../../lib/formatters.js";
import { date } from "../../lib/formatters.js";
import { CLASSES } from "../../lib/constants.js";

export default function AssetTable({ assets, edit, remove, compact = false }) {
  return assets.length ? (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Ativo</th>
            <th>Cotação</th>
            <th>Hoje</th>
            {!compact && (
              <>
                <th>Quantidade</th>
                <th>Preço médio</th>
              </>
            )}
            <th>Posição</th>
            <th aria-label="Ações" />
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id}>
              <td>
                <div className="asset-name">
                  <span className={`ticker-logo ${asset.asset_class}`}>
                    {asset.ticker.slice(0, 2)}
                  </span>
                  <div>
                    <strong>{asset.ticker}</strong>
                    <small>
                      {asset.name || CLASSES[asset.asset_class]}{" "}
                      <span className="dot-separator">·</span>{" "}
                      {CLASSES[asset.asset_class]}
                    </small>
                  </div>
                </div>
              </td>
              <td>
                {asset.quote ? (
                  <>
                    <strong className="numeric">
                      {asset.quote.currency === "BRL"
                        ? money(asset.quote.price)
                        : `${asset.quote.currency} ${asset.quote.price.toFixed(2)}`}
                    </strong>
                    <small className="quote-time">
                      {date(asset.quote.quoted_at)}
                    </small>
                  </>
                ) : (
                  <span className="muted">Aguardando dados</span>
                )}
              </td>
              <td>
                {asset.quote ? (
                  <span
                    className={`change ${asset.quote.change_pct >= 0 ? "positive" : "negative"}`}
                  >
                    {asset.quote.change_pct >= 0 ? (
                      <ArrowUpRight size={14} />
                    ) : (
                      <ArrowDownRight size={14} />
                    )}{" "}
                    {pct(asset.quote.change_pct)}
                  </span>
                ) : (
                  "—"
                )}
              </td>
              {!compact && (
                <>
                  <td className="numeric">
                    {asset.quantity.toLocaleString("pt-BR")}
                  </td>
                  <td className="numeric">{money(asset.average_price)}</td>
                </>
              )}
              <td className="numeric">
                {asset.value !== null ? money(asset.value) : "—"}
              </td>
              <td>
                <div className="row-actions">
                  <IconButton
                    label={`Editar ${asset.ticker}`}
                    onClick={() => edit(asset)}
                  >
                    <Pencil size={15} />
                  </IconButton>
                  {!compact && (
                    <IconButton
                      label={`Remover ${asset.ticker}`}
                      onClick={() => remove(asset)}
                    >
                      <Trash2 size={15} />
                    </IconButton>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <Empty icon={Wallet} title="Sua carteira começa aqui">
      Adicione os ativos que você quer manter no radar.
    </Empty>
  );
}
