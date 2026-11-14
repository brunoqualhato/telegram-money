import assert from "node:assert/strict";
import { test } from "node:test";
import { portfolioMetrics } from "../src/features/overview/portfolioMetrics.js";
import { chartGeometry } from "../src/lib/chartGeometry.js";

function position(overrides = {}) {
  return {
    id: 1,
    ticker: "TEST3",
    quantity: 10,
    average_price: 8,
    value: 110,
    asset_class: "acao",
    quote: { currency: "BRL", change_pct: 10 },
    ...overrides,
  };
}

test("variação diária é ponderada pelo patrimônio anterior de cada posição", () => {
  const metrics = portfolioMetrics([
    position(),
    position({
      id: 2,
      ticker: "MOCK4",
      value: 180,
      quote: { currency: "BRL", change_pct: -10 },
    }),
  ]);
  assert.equal(metrics.total, 290);
  assert.ok(Math.abs(metrics.dayChange + 10) < 1e-8);
  assert.ok(Math.abs(metrics.dayPct - (-10 / 300) * 100) < 1e-8);
  assert.equal(metrics.advancing, 1);
  assert.equal(metrics.declining, 1);
});

test("custos ausentes não viram lucro e valores fora de BRL não são somados", () => {
  const metrics = portfolioMetrics([
    position(),
    position({ id: 2, average_price: 0, value: 90 }),
    position({ id: 3, value: null, quote: null }),
    position({ id: 4, quote: { currency: "USD", change_pct: 3 } }),
    position({ id: 5, quantity: 0, value: 0 }),
  ]);
  assert.equal(metrics.heldCount, 4);
  assert.equal(metrics.pricedCount, 2);
  assert.equal(metrics.missingQuotes, 2);
  assert.equal(metrics.missingCost, 1);
  assert.equal(metrics.total, 200);
  assert.equal(metrics.cost, 80);
  assert.equal(metrics.gain, 30);
  assert.equal(metrics.gainPct, 37.5);
  assert.equal(metrics.positions.find((asset) => asset.id === 2).gain, null);
});

test("alocação e concentração usam somente posições com valor válido", () => {
  const metrics = portfolioMetrics([
    position({ id: 1, value: 100 }),
    position({ id: 2, value: 200, asset_class: "fii" }),
    position({ id: 3, value: 300, asset_class: "etf" }),
    position({ id: 4, value: 400 }),
    position({ id: 5, value: NaN }),
  ]);
  assert.equal(metrics.topThree, 90);
  assert.deepEqual(
    metrics.positions.map((asset) => asset.id),
    [4, 3, 2, 1],
  );
  assert.equal(
    metrics.allocations.reduce((sum, item) => sum + item.weight, 0),
    100,
  );
  assert.equal(metrics.allocations[0].key, "acao");
  assert.equal(metrics.allocations[0].weight, 50);
});

test("variações indisponíveis e carteira vazia não produzem percentuais fictícios", () => {
  const empty = portfolioMetrics();
  assert.equal(empty.total, 0);
  assert.equal(empty.gain, null);
  assert.equal(empty.dayPct, null);
  assert.equal(empty.topThree, null);
  const metrics = portfolioMetrics([
    position({ quote: { currency: "BRL", change_pct: -100 } }),
  ]);
  assert.equal(metrics.dayChange, null);
  assert.equal(metrics.missingDaily, 1);
  const zero = portfolioMetrics([position({ value: 0 })]);
  assert.equal(zero.topThree, null);
  assert.equal(zero.dayPct, null);
});

test("eixo temporal preserva intervalos irregulares e inclui a referência de custo", () => {
  const chart = chartGeometry(
    [
      { date: "2026-01-01", value: 100 },
      { date: "2026-01-02", value: 110 },
      { date: "2026-01-04", value: 105 },
    ],
    80,
  );
  const [first, middle, last] = chart.points;
  assert.ok(Math.abs(last.x - middle.x - 2 * (middle.x - first.x)) < 1e-8);
  assert.ok(chart.referenceY <= 200 && chart.referenceY >= 20);
  assert.ok(chart.points.every((point) => Number.isFinite(point.y)));
});

test("gráfico com preços constantes ou resultados negativos tem escala finita", () => {
  for (const value of [0, -20, 100]) {
    const chart = chartGeometry(
      [
        { date: "2026-01-01", value },
        { date: "2026-01-02", value },
      ],
      0,
    );
    assert.ok(chart.ticks.every((tick) => Number.isFinite(tick.y)));
    assert.ok(!chart.line.includes("NaN"));
  }
});
