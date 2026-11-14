import assert from "node:assert/strict";
import { after, test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";
import getPageInfo from "../src/app/getPageInfo.js";

const server = await createServer({
  server: { middlewareMode: true, watch: null, hmr: false, ws: false },
  appType: "custom",
});
after(() => server.close());
const { default: PageContent } = await server.ssrLoadModule(
  "/src/app/PageContent.jsx",
);
const { default: AssetFields } = await server.ssrLoadModule(
  "/src/features/assets/AssetFields.jsx",
);
const { default: DocumentSummary } = await server.ssrLoadModule(
  "/src/features/documents/DocumentSummary.jsx",
);
const noop = () => {};
const asset = {
  id: 1,
  ticker: "PETR4",
  name: "Petrobras",
  asset_class: "acao",
  quantity: 2,
  average_price: 30,
  value: 80,
  quote: {
    price: 40,
    currency: "BRL",
    change_pct: 2,
    quoted_at: "2026-01-01T12:00:00Z",
  },
};
const data = {
  assets: [asset],
  total: 80,
  gain: 20,
  gain_pct: 33,
  latest_notifications: [],
};
const props = {
  data,
  me: { email: "teste@example.com", timezone: "America/Sao_Paulo" },
  items: [],
  filter: "all",
  search: "",
  filteredAssets: [asset],
  integrations: {},
  setFilter: noop,
  setSearch: noop,
  setModal: noop,
  setConfirm: noop,
  removeAsset: noop,
  navigate: noop,
  connect: noop,
  report: noop,
  refresh: noop,
  act: noop,
  reload: noop,
  notify: noop,
  retry: noop,
};

for (const [page, expected] of Object.entries({
  overview: "Seu radar está aqui",
  assets: "PETR4",
  alerts: "Regras de monitoramento",
  events: "Calendário de eventos",
  documents: "Informação com contexto",
  reports: "Relatórios da carteira",
  history: "Histórico de notificações",
  treasury: "Títulos públicos",
  settings: "Controle o ritmo",
})) {
  test(`tela ${page} renderiza com os componentes extraídos`, () => {
    const html = renderToStaticMarkup(
      createElement(PageContent, { ...props, page, title: page }),
    );
    assert.ok(html.includes(expected));
  });
}

test("campos preservam ticker editável na criação e bloqueado na edição", () => {
  const creation = renderToStaticMarkup(createElement(AssetFields));
  assert.ok(!creation.includes('readOnly=""'));
  assert.ok(creation.includes('value="Principal"'));
  const edition = renderToStaticMarkup(createElement(AssetFields, { asset }));
  assert.ok(edition.includes('readOnly=""'));
  assert.ok(edition.includes('value="PETR4"'));
});

test("resumo preserva fatos, evidências, riscos e informações ausentes", () => {
  const summary = {
    facts: [{ fact: "Receita cresceu", evidence: "Receita +10%" }],
    risks: [{ fact: "Risco cambial", evidence: "Exposição ao dólar" }],
    interpretations: ["Margem estável"],
    missing: ["Lucro por ação"],
    incomplete: true,
  };
  const html = renderToStaticMarkup(
    createElement(DocumentSummary, { summary }),
  );
  for (const expected of [
    "Receita +10%",
    "Risco cambial",
    "Margem estável",
    "Lucro por ação",
    "contexto incompleto",
  ])
    assert.ok(html.includes(expected));
});

test("busca e classe se combinam e notificações pendentes de conferência são contadas", () => {
  const info = getPageInfo({
    page: "assets",
    search: "PETRO",
    filter: "acao",
    data: {
      ...data,
      assets: [
        asset,
        {
          ...asset,
          id: 2,
          ticker: "HGLG11",
          name: "Fundo",
          asset_class: "fii",
        },
      ],
      latest_notifications: [
        { status: "sent" },
        { status: "failed" },
        { status: "uncertain" },
      ],
    },
  });
  assert.equal(info.title, "Meus ativos");
  assert.deepEqual(info.filteredAssets, [asset]);
  assert.equal(info.totalNotifications, 2);
  assert.equal(
    getPageInfo({ page: "assets", data, search: "", filter: "fii" })
      .filteredAssets.length,
    0,
  );
});
