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

function AssetQuoteCell({ quote }) {
  if (!quote) return <span className="muted">Aguardando dados</span>;
  return (
    <>
      <strong className="numeric">
        {quote.currency === "BRL"
          ? money(quote.price)
          : `${quote.currency} ${quote.price.toFixed(2)}`}
      </strong>
      <small className="quote-time">{date(quote.quoted_at)}</small>
    </>
  );
}

function AssetDayChangeCell({ quote }) {
  if (!quote) return "—";
  const isPos = quote.change_pct >= 0;
  return (
    <span className={`change ${isPos ? "positive" : "negative"}`}>
      {isPos ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}{" "}
      {pct(quote.change_pct)}
    </span>
  );
}

function AssetPositionCell({ value, averagePrice, quotePrice }) {
  if (value === null) return "—";
  const hasGain = averagePrice > 0 && quotePrice;
  const gain = hasGain ? (quotePrice / averagePrice - 1) * 100 : null;
  return (
    <>
      <div>{money(value)}</div>
      {gain !== null && (
        <small
          className={`quote-time ${gain >= 0 ? "positive" : "negative"}`}
          title="Variação sobre o preço médio"
        >
          {pct(gain)}
        </small>
      )}
    </>
  );
}

function AssetRow({ asset, edit, remove, compact }) {
  return (
    <tr>
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
        <AssetQuoteCell quote={asset.quote} />
      </td>
      <td>
        <AssetDayChangeCell quote={asset.quote} />
      </td>
      {!compact && (
        <>
          <td className="numeric">{asset.quantity.toLocaleString("pt-BR")}</td>
          <td className="numeric">{money(asset.average_price)}</td>
        </>
      )}
      <td className="numeric">
        <AssetPositionCell
          value={asset.value}
          averagePrice={asset.average_price}
          quotePrice={asset.quote?.price}
        />
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
  );
}

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
            <AssetRow
              key={asset.id}
              asset={asset}
              edit={edit}
              remove={remove}
              compact={compact}
            />
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
