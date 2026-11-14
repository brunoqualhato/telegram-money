import { CLASSES } from "../../lib/constants.js";

export const CLASS_COLORS = {
  acao: "#356b50",
  fii: "#9ab977",
  etf: "#c7a66a",
  bdr: "#719baa",
  indice: "#8e80a9",
  cripto: "#c88862",
  moeda: "#838c7a",
};

function hasBrlValue(asset) {
  return (
    asset.quote?.currency === "BRL" &&
    Number.isFinite(asset.value) &&
    asset.value >= 0
  );
}

function dailyResult(asset) {
  const change = asset.quote.change_pct;
  if (!Number.isFinite(change) || change <= -100) return null;
  const previous = asset.value / (1 + change / 100);
  return { amount: asset.value - previous, previous, pct: change };
}

function positionResult(asset, total) {
  const hasCost =
    Number.isFinite(asset.average_price) && asset.average_price > 0;
  const cost = hasCost ? asset.quantity * asset.average_price : null;
  const gain = hasCost ? asset.value - cost : null;
  return {
    ...asset,
    weight: total > 0 ? (asset.value / total) * 100 : 0,
    cost,
    gain,
    gainPct: hasCost ? (gain / cost) * 100 : null,
    daily: dailyResult(asset),
  };
}

function allocations(positions, total) {
  const classes = {};
  for (const asset of positions) {
    classes[asset.asset_class] =
      (classes[asset.asset_class] || 0) + asset.value;
  }
  return Object.entries(classes)
    .map(([key, value]) => ({
      key,
      label: CLASSES[key] || key,
      value,
      weight: total > 0 ? (value / total) * 100 : 0,
      color: CLASS_COLORS[key] || "#838c7a",
    }))
    .sort((a, b) => b.value - a.value);
}

export function portfolioMetrics(assets = []) {
  const held = assets.filter(
    (asset) => Number.isFinite(asset.quantity) && asset.quantity > 0,
  );
  const priced = held.filter(hasBrlValue);
  const total = priced.reduce((sum, asset) => sum + asset.value, 0);
  const positions = priced
    .map((asset) => positionResult(asset, total))
    .sort((a, b) => b.value - a.value);
  const withCost = positions.filter((asset) => asset.cost !== null);
  const cost = withCost.reduce((sum, asset) => sum + asset.cost, 0);
  const gain = withCost.reduce((sum, asset) => sum + asset.gain, 0);
  const daily = positions.filter((asset) => asset.daily !== null);
  const previous = daily.reduce((sum, asset) => sum + asset.daily.previous, 0);
  const dayChange = daily.reduce((sum, asset) => sum + asset.daily.amount, 0);
  return {
    positions,
    allocations: allocations(positions, total),
    total,
    cost: withCost.length ? cost : null,
    gain: withCost.length ? gain : null,
    gainPct: cost > 0 ? (gain / cost) * 100 : null,
    dayChange: daily.length ? dayChange : null,
    dayPct: previous > 0 ? (dayChange / previous) * 100 : null,
    heldCount: held.length,
    pricedCount: positions.length,
    costCount: withCost.length,
    missingQuotes: held.length - positions.length,
    missingCost: positions.length - withCost.length,
    missingDaily: positions.length - daily.length,
    topThree:
      total > 0
        ? positions.slice(0, 3).reduce((sum, asset) => sum + asset.weight, 0)
        : null,
    advancing: daily.filter((asset) => asset.daily.pct > 0).length,
    declining: daily.filter((asset) => asset.daily.pct < 0).length,
    unchanged: daily.filter((asset) => asset.daily.pct === 0).length,
  };
}
