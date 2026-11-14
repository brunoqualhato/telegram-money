import { Plus, Search, Upload } from "lucide-react";
import Button from "../../components/ui/Button.jsx";
import AssetTable from "./AssetTable.jsx";
import { CLASSES } from "../../lib/constants.js";

export default function AssetsPage({
  data,
  filter,
  setFilter,
  search,
  setSearch,
  filteredAssets,
  setModal,
  removeAsset,
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div className="tabs">
          <button
            className={filter === "all" ? "active" : ""}
            onClick={() => setFilter("all")}
          >
            Todos <small>{data.assets.length}</small>
          </button>
          {["acao", "fii", "etf"].map((k) => (
            <button
              key={k}
              className={filter === k ? "active" : ""}
              onClick={() => setFilter(k)}
            >
              {CLASSES[k]}
            </button>
          ))}
        </div>
        <div className="button-row">
          <Button
            secondary
            icon={Upload}
            onClick={() => setModal({ type: "import-b3" })}
          >
            Importar B3
          </Button>
          <Button icon={Plus} onClick={() => setModal({ type: "asset" })}>
            Adicionar ativo
          </Button>
        </div>
      </div>
      <div className="table-toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por ticker ou nome"
            aria-label="Buscar ativos"
          />
        </div>
        <small>{filteredAssets.length} ativos na lista</small>
      </div>
      <AssetTable
        assets={filteredAssets}
        edit={(asset) => setModal({ type: "asset", asset })}
        remove={removeAsset}
      />
    </section>
  );
}
