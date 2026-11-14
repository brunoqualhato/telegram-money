import csv
from decimal import Decimal
import io
import xml.etree.ElementTree as ET
import zipfile
from sqlalchemy import select
from ..models import Asset
from .alerts import latest_quote


def parse_decimal(value):
    if value is None:
        return Decimal(0)
    s = str(value).strip().replace("R$", "").replace(" ", "")
    if not s or s == "-":
        return Decimal(0)
    if "," in s and "." in s:
        if s.find(".") < s.find(","):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return Decimal(0)


def parse_b3_position(raw: bytes, filename: str = ""):
    is_xlsx = False
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if "xl/workbook.xml" in z.namelist():
                is_xlsx = True
    except Exception:
        pass

    if is_xlsx:
        return _parse_b3_xlsx(raw)
    return _parse_b3_csv(raw)


def _parse_b3_xlsx(raw: bytes):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        sst = []
        if "xl/sharedStrings.xml" in z.namelist():
            tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                t = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                if t is not None:
                    sst.append(t.text or "")
                else:
                    sst.append(
                        "".join(
                            node.text or ""
                            for node in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                        )
                    )

        wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
        rels_tree = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels_tree}

        results = {}
        for s in wb_tree.findall(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet"
        ):
            s_name = s.attrib["name"].strip()
            norm_name = s_name.lower().replace("ç", "c").replace("õ", "o").replace("ã", "a")
            if "renda fixa" in norm_name or "tesouro" in norm_name:
                continue

            if "acao" in norm_name or "acoes" in norm_name:
                asset_class = "acao"
            elif "fundo" in norm_name or "fii" in norm_name:
                asset_class = "fii"
            elif "bdr" in norm_name:
                asset_class = "bdr"
            elif "etf" in norm_name:
                asset_class = "etf"
            else:
                asset_class = "acao"

            rId = s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = "xl/" + rel_map[rId]
            sheet_tree = ET.fromstring(z.read(target))
            sheet_data = sheet_tree.find(
                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData"
            )
            if sheet_data is None:
                continue

            headers = None
            for row in sheet_data.findall(
                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"
            ):
                cells = []
                for c in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                    t = c.get("t")
                    v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                    val = v.text if v is not None else ""
                    if t == "s" and val.isdigit() and int(val) < len(sst):
                        val = sst[int(val)]
                    cells.append(val)

                if not headers:
                    h_lower = [str(x or "").strip().lower() for x in cells]
                    if any("código" in h or "codigo" in h or "produto" in h or "ticker" in h for h in h_lower):
                        headers = [str(h or "").strip() for h in cells]
                    continue

                row_dict = {headers[idx]: cells[idx] for idx in range(min(len(headers), len(cells)))}
                ticker = ""
                for k in ("Código de Negociação", "Codigo de Negociacao", "Código", "Codigo", "Ticker"):
                    if k in row_dict and row_dict[k]:
                        ticker = str(row_dict[k]).strip().upper()
                        break

                if not ticker or ticker.upper() == "TOTAL" or len(ticker) < 3:
                    continue

                prod = str(row_dict.get("Produto") or "").strip()
                name = prod.split(" - ", 1)[1].strip() if " - " in prod else prod

                qty = parse_decimal(row_dict.get("Quantidade") or row_dict.get("Quantidade Disponível"))
                price = parse_decimal(
                    row_dict.get("Preço de Fechamento") or row_dict.get("Preco de Fechamento")
                )

                if ticker in results:
                    results[ticker]["quantity"] += qty
                    if price > 0 and results[ticker]["average_price"] == 0:
                        results[ticker]["average_price"] = price
                else:
                    results[ticker] = {
                        "ticker": ticker,
                        "name": name[:150],
                        "asset_class": asset_class,
                        "quantity": qty,
                        "average_price": price,
                    }
        return list(results.values())


def _parse_b3_csv(raw: bytes):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")

    first_lines = text.splitlines()[:5]
    if not first_lines:
        return []
    delimiter = (
        ";"
        if sum(line.count(";") for line in first_lines) >= sum(line.count(",") for line in first_lines)
        else ","
    )
    reader = csv.reader(text.splitlines(), delimiter=delimiter)
    headers = None
    results = {}
    for row in reader:
        if not headers:
            h_lower = [str(x or "").strip().lower() for x in row]
            if any("código" in h or "codigo" in h or "produto" in h or "ticker" in h for h in h_lower):
                headers = [str(h or "").strip() for h in row]
            continue
        row_dict = {headers[idx]: row[idx] for idx in range(min(len(headers), len(row)))}
        ticker = ""
        for k in ("Código de Negociação", "Codigo de Negociacao", "Código", "Codigo", "Ticker"):
            if k in row_dict and row_dict[k]:
                ticker = str(row_dict[k]).strip().upper()
                break
        if not ticker or ticker.upper() == "TOTAL" or len(ticker) < 3:
            continue
        prod = str(row_dict.get("Produto") or "").strip()
        name = prod.split(" - ", 1)[1].strip() if " - " in prod else prod
        qty = parse_decimal(row_dict.get("Quantidade") or row_dict.get("Quantidade Disponível"))
        price = parse_decimal(
            row_dict.get("Preço de Fechamento") or row_dict.get("Preco de Fechamento")
        )

        tipo = str(row_dict.get("Tipo") or "").upper()
        if "BDR" in tipo or ticker.endswith(("34", "35", "39")):
            asset_class = "bdr"
        elif "COTAS" in tipo or (ticker.endswith("11") and ("FII" in prod.upper() or "FDO" in prod.upper())):
            asset_class = "fii"
        elif "ETF" in tipo or "INDEX" in prod.upper():
            asset_class = "etf"
        else:
            asset_class = "acao"

        if ticker in results:
            results[ticker]["quantity"] += qty
        else:
            results[ticker] = {
                "ticker": ticker,
                "name": name[:150],
                "asset_class": asset_class,
                "quantity": qty,
                "average_price": price,
            }
    return list(results.values())


def portfolio_snapshot(db):
    assets = []
    total = cost = day_change = Decimal(0)
    missing = 0
    for asset in db.scalars(select(Asset).order_by(Asset.ticker)).all():
        quote = latest_quote(db, asset.id)
        position_cost = asset.quantity * asset.average_price
        # Não soma moedas diferentes em um patrimônio fictício.
        included = quote is not None and quote.currency == "BRL"
        value = asset.quantity * quote.price if included else None
        if included:
            total += value
            cost += position_cost
            if quote.change_pct > -100:
                previous = quote.price / (1 + quote.change_pct / 100)
                day_change += asset.quantity * (quote.price - previous)
        elif asset.quantity > 0:
            missing += 1
        assets.append(
            {
                "id": asset.id,
                "ticker": asset.ticker,
                "name": asset.name,
                "asset_class": asset.asset_class,
                "watchlist": asset.watchlist,
                "quantity": float(asset.quantity),
                "average_price": float(asset.average_price),
                "value": float(value) if value is not None else None,
                "quote": {
                    "price": float(quote.price),
                    "change_pct": float(quote.change_pct),
                    "currency": quote.currency,
                    "quoted_at": quote.quoted_at.isoformat(),
                    "source": quote.source,
                    "day_high": quote.day_high,
                    "day_low": quote.day_low,
                    "high_52w": quote.high_52w,
                    "low_52w": quote.low_52w,
                }
                if quote
                else None,
            }
        )
    return {
        "assets": assets,
        "total": float(total),
        "cost": float(cost),
        "gain": float(total - cost),
        "gain_pct": float((total / cost - 1) * 100) if cost else None,
        "day_change": float(day_change),
        "missing_positions": missing,
        "performance_note": "Variação contra custo informado; não inclui proventos, taxas ou fluxo de caixa. Valores apenas em BRL.",
    }
