import assert from "node:assert/strict";
import { test } from "node:test";
import { ESLint } from "eslint";

const eslint = new ESLint();

async function violations(code, rule) {
  const [result] = await eslint.lintText(code, { filePath: "src/limits.js" });
  return result.messages.filter((message) => message.ruleId === rule);
}

function branches(count) {
  return `function example(value) { ${"if (value) value--;".repeat(count)} }`;
}

function lines(count) {
  return [
    "function example() {",
    ...Array(count - 2).fill("  void 0;"),
    "}",
  ].join("\n");
}

test("complexidade aceita 10 e rejeita 11", async () => {
  assert.equal((await violations(branches(9), "complexity")).length, 0);
  assert.equal((await violations(branches(10), "complexity")).length, 1);
});

test("funções aceitam 150 linhas e rejeitam 151, contando comentários e espaços", async () => {
  assert.equal(
    (await violations(lines(150), "max-lines-per-function")).length,
    0,
  );
  assert.equal(
    (await violations(lines(151), "max-lines-per-function")).length,
    1,
  );
});

test("funções aceitam 5 parâmetros e rejeitam 6", async () => {
  assert.equal(
    (await violations("function example(a,b,c,d,e) {}", "max-params")).length,
    0,
  );
  assert.equal(
    (await violations("function example(a,b,c,d,e,f) {}", "max-params")).length,
    1,
  );
});

test("comentários inline não conseguem desativar os limites", async () => {
  assert.equal(
    (
      await violations(
        `/* eslint complexity: off */\n${branches(10)}`,
        "complexity",
      )
    ).length,
    1,
  );
});
