import assert from "node:assert/strict";
import { test } from "node:test";
import { api } from "../src/services/api.js";

test("API serializa JSON e preserva cookie, headers e cancelamento", async (t) => {
  const signal = new AbortController().signal;
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url, "/api/assets");
    assert.equal(options.credentials, "same-origin");
    assert.equal(options.method, "POST");
    assert.equal(options.headers["Content-Type"], "application/json");
    assert.equal(options.headers["X-Test"], "ok");
    assert.equal(options.body, '{"ticker":"PETR4"}');
    assert.equal(options.signal, signal);
    return Response.json({ id: 1 });
  });
  assert.deepEqual(
    await api("/assets", {
      method: "POST",
      headers: { "X-Test": "ok" },
      body: { ticker: "PETR4" },
      signal,
    }),
    { id: 1 },
  );
});

test("upload mantém FormData e deixa o navegador definir o boundary", async (t) => {
  const form = new FormData();
  form.set("title", "Relatório");
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    assert.equal(options.body, form);
    assert.equal(options.headers["Content-Type"], undefined);
    return Response.json({ id: 2 });
  });
  await api("/documents/pdf", { method: "POST", body: form });
});

test("API mantém status e detalhes de validação nos erros", async (t) => {
  t.mock.method(globalThis, "fetch", async () =>
    Response.json(
      {
        detail: [{ loc: ["body", "ticker"], msg: "obrigatório" }],
      },
      { status: 422 },
    ),
  );
  await assert.rejects(api("/assets"), {
    message: "ticker: obrigatório",
    status: 422,
  });
});

test("resposta sem JSON mantém erro genérico e status de autenticação", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response("Unauthorized", { status: 401 }),
  );
  await assert.rejects(api("/me"), {
    message: "Não foi possível completar a operação.",
    status: 401,
  });
});

test("testes de integração com ok falso mostram o erro mesmo com HTTP 200", async (t) => {
  t.mock.method(globalThis, "fetch", async () =>
    Response.json({ ok: false, error: "Gateway indisponível", models: [] }),
  );
  await assert.rejects(
    api("/integrations/test-ai", {
      method: "POST",
      body: { url: "http://localhost:1235/v1" },
    }),
    { message: "Gateway indisponível", status: 200 },
  );
});
