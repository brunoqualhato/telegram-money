const { chromium } = require("/Users/brunoqualhato/Documents/meus/HeritagePowerPro/node_modules/playwright");
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

async function main() {
  const screenshotsDir = path.resolve(__dirname, "../docs/screenshots");
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  // Get active session token
  const token = execSync(
    'env -u DOCKER_HOST docker --context desktop-linux compose exec -T api python -c "from app.db import SessionLocal; from app.models import Owner; from app.auth import create_session; from sqlalchemy import select; db = SessionLocal(); o = db.scalar(select(Owner)); t = create_session(db, o); print(t)"'
  )
    .toString()
    .trim();

  console.log("Token obtained:", token.slice(0, 10) + "...");

  const browser = await chromium.launch({
    executablePath: "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 2,
  });

  await context.addCookies([
    {
      name: "tm_session",
      value: token,
      domain: "localhost",
      path: "/",
      httpOnly: true,
      secure: false,
      sameSite: "Strict",
    },
  ]);

  const page = await context.newPage();
  await page.goto("http://localhost:8000", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);

  // 1. Visão Geral
  console.log("Capturing 01-visao-geral.png...");
  await page.screenshot({ path: path.join(screenshotsDir, "01-visao-geral.png") });

  // 2. Meus Ativos
  console.log("Capturing 02-meus-ativos.png...");
  await page.click('nav button:has-text("Meus ativos")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "02-meus-ativos.png") });

  // 3. Modal Importar B3
  console.log("Capturing 03-importar-b3-modal.png...");
  await page.click('button:has-text("Importar B3")');
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(screenshotsDir, "03-importar-b3-modal.png") });
  // Close modal
  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);

  // 4. Proventos
  console.log("Capturing 04-proventos.png...");
  await page.click('nav button:has-text("Proventos")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "04-proventos.png") });

  // 5. Documentos e Notícias
  console.log("Capturing 05-documentos-noticias.png...");
  await page.click('nav button:has-text("Documentos e IA")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "05-documentos-noticias.png") });

  // 6. Alertas
  console.log("Capturing 06-alertas.png...");
  await page.click('nav button:has-text("Meus alertas")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "06-alertas.png") });

  // 7. Tesouro Direto
  console.log("Capturing 07-tesouro-direto.png...");
  await page.click('button:has-text("Tesouro Direto")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "07-tesouro-direto.png") });

  // 8. Relatórios
  console.log("Capturing 08-relatorios.png...");
  await page.click('nav button:has-text("Relatórios")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "08-relatorios.png") });

  // 9. Histórico
  console.log("Capturing 09-historico.png...");
  await page.click('nav button:has-text("Histórico de alertas")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "09-historico.png") });

  // 10. Configurações
  console.log("Capturing 10-configuracoes.png...");
  await page.click('button:has-text("Configurações")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, "10-configuracoes.png") });

  console.log("All screenshots successfully captured!");
  await browser.close();
}

main().catch((err) => {
  console.error("Error capturing screenshots:", err);
  process.exit(1);
});
