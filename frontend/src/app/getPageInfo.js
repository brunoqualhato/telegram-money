import { NAV } from "../lib/constants.js";

export default function getPageInfo({ page, data, search, filter }) {
  const title =
    NAV.find((n) => n[0] === page)?.[1] ||
    (page === "settings" ? "Configurações" : "Tesouro Direto");
  const filteredAssets = data.assets.filter(
    (a) =>
      (!search ||
        `${a.ticker} ${a.name}`.toLowerCase().includes(search.toLowerCase())) &&
      (filter === "all" || a.asset_class === filter),
  );
  const totalNotifications =
    data.latest_notifications?.filter((n) =>
      ["failed", "uncertain"].includes(n.status),
    ).length || 0;
  return { title, filteredAssets, totalNotifications };
}
