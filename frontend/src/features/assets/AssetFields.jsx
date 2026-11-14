import Field from "../../components/ui/Field.jsx";
import { CLASSES } from "../../lib/constants.js";
export default function AssetFields({ asset }) {
  const values = asset || {};
  return (
    <>
      <div className="form-grid">
        <Field label="Ticker">
          <input
            name="ticker"
            required
            maxLength={24}
            defaultValue={values.ticker}
            readOnly={!!asset}
            placeholder="Ex.: PETR4"
            className="uppercase"
          />
        </Field>
        <Field label="Classe">
          <select
            name="asset_class"
            defaultValue={values.asset_class || "acao"}
          >
            {Object.entries(CLASSES).map(([key, value]) => (
              <option key={key} value={key}>
                {value}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Nome (opcional)">
        <input
          name="name"
          maxLength={150}
          defaultValue={values.name}
          placeholder="Nome da empresa ou fundo"
        />
      </Field>
      <Field label="Lista">
        <input
          name="watchlist"
          maxLength={80}
          required
          defaultValue={values.watchlist || "Principal"}
        />
      </Field>
      <div className="form-grid">
        <Field label="Quantidade">
          <input
            name="quantity"
            type="number"
            step="any"
            min="0"
            required
            defaultValue={values.quantity || 0}
          />
        </Field>
        <Field label="Preço médio (moeda do ativo)">
          <input
            name="average_price"
            type="number"
            step="any"
            min="0"
            required
            defaultValue={values.average_price || 0}
          />
        </Field>
      </div>
    </>
  );
}
