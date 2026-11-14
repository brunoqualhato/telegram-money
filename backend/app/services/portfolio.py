import csv
from datetime import datetime, timedelta
from decimal import Decimal
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from sqlalchemy import select
from ..db import utcnow
from ..models import Asset, Quote
from .alerts import latest_quote

TICKER_REGEX = re.compile(r"^[A-Z0-9]{4,6}\d{1,2}[B]?$")


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


def _detect_asset_class(ticker: str, name: str) -> str:
    ticker = ticker.upper().strip()
    norm = f"{ticker} {name}".lower()
    if ticker.endswith(("31", "32", "33", "34", "35", "39")) or "bdr" in norm:
        return "bdr"
    if any(k in norm for k in ("fii", "imobiliario", "imobiliário", "imob", "real estate", "fdo inv", "fundo de inv")):
        return "fii"
    if "etf" in norm or "índice" in norm or "indice" in norm or "index" in norm:
        return "etf"
    if any(k in norm for k in ("s/a", "s.a.", "cia ", "companhia")):
        return "acao"
    if ticker.endswith("11"):
        return "fii"
    return "acao"


def _parse_date(val):
    if not val:
        return datetime.min
    s = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        f = float(s)
        if 30000 <= f <= 60000:
            return datetime(1899, 12, 30) + timedelta(days=f)
    except Exception:
        pass
    return datetime.min


def _consolidate_movimentacao(parsed_rows):
    # Ordena cronologicamente (do mais antigo para o mais recente).
    # -r_idx preserva a ordem intradia quando o arquivo original é mais recente -> mais antigo.
    parsed_rows.sort(key=lambda item: (_parse_date(item[1].get("Data")), -item[0]))

    state = {}
    for r_idx, r in parsed_rows:
        prod = str(r.get("Produto") or "").strip()
        if " - " in prod:
            ticker, name = prod.split(" - ", 1)
        else:
            ticker, name = prod, prod
        ticker = ticker.strip().upper()
        if not ticker or ticker.startswith(("CDB", "RDB", "LCA", "LCI", "CRI", "CRA", "DEB", "TESOURO", "TOTAL")):
            continue
        if not TICKER_REGEX.match(ticker):
            continue

        io_type = str(r.get("Entrada/Saída") or r.get("Entrada/Saida") or "").strip().lower().replace("é", "e")
        mov_type = str(r.get("Movimentação") or r.get("Movimentacao") or "").strip().lower()
        if not any(k in mov_type for k in ("liquida", "compra", "venda", "subscr", "bonifica", "transfer", "desdobro", "grupamento")):
            continue
        qty = parse_decimal(r.get("Quantidade"))
        if io_type not in ("credito", "debito") or qty <= 0:
            continue
        price = parse_decimal(r.get("Preço unitário") or r.get("Preco unitario"))
        val = parse_decimal(r.get("Valor da Operação") or r.get("Valor da Operacao"))

        if price == Decimal(0) and val > Decimal(0) and qty > Decimal(0):
            price = val / qty

        if ticker not in state:
            state[ticker] = {
                "ticker": ticker,
                "name": name.strip()[:150],
                "asset_class": _detect_asset_class(ticker, name),
                "quantity": Decimal(0),
                "average_price": Decimal(0),
            }

        # Compras e aquisições (crédito com liquidação ou compra)
        if io_type == "credito" and any(
            k in mov_type
            for k in (
                "transferência - liquidação",
                "transferencia - liquidacao",
                "compra",
                "liquidação",
                "liquidacao",
                "subscrição",
                "subscricao",
                "bonificação",
                "bonificacao",
            )
        ):
            curr_qty = state[ticker]["quantity"]
            curr_avg = state[ticker]["average_price"]
            new_qty = curr_qty + qty
            if new_qty > Decimal(0):
                if price > Decimal(0):
                    new_avg = ((curr_qty * curr_avg) + (qty * price)) / new_qty
                else:
                    new_avg = ((curr_qty * curr_avg) / new_qty) if curr_qty > Decimal(0) else Decimal(0)
            else:
                new_avg = Decimal(0)
            state[ticker]["quantity"] = new_qty
            state[ticker]["average_price"] = new_avg

        # Vendas e desinvestimentos (débito com liquidação ou venda)
        elif io_type == "debito" and any(
            k in mov_type
            for k in (
                "transferência - liquidação",
                "transferencia - liquidacao",
                "venda",
                "liquidação",
                "liquidacao",
            )
        ):
            curr_qty = state[ticker]["quantity"]
            new_qty = max(Decimal(0), curr_qty - qty)
            state[ticker]["quantity"] = new_qty
            # Venda reduz a posição sem alterar o preço médio das cotas restantes
            if new_qty == Decimal(0):
                state[ticker]["average_price"] = Decimal(0)

        # Transferências neutras
        elif "transferência" in mov_type or "transferencia" in mov_type:
            if io_type == "debito":
                state[ticker]["quantity"] = max(Decimal(0), state[ticker]["quantity"] - qty)
                if state[ticker]["quantity"] == Decimal(0):
                    state[ticker]["average_price"] = Decimal(0)
            elif io_type == "credito":
                curr_qty = state[ticker]["quantity"]
                curr_avg = state[ticker]["average_price"]
                new_qty = curr_qty + qty
                if price > Decimal(0) and new_qty > Decimal(0):
                    state[ticker]["average_price"] = ((curr_qty * curr_avg) + (qty * price)) / new_qty
                state[ticker]["quantity"] = new_qty

        # Desdobros e grupamentos
        elif "desdobro" in mov_type:
            curr_qty = state[ticker]["quantity"]
            curr_avg = state[ticker]["average_price"]
            new_qty = curr_qty + qty
            state[ticker]["quantity"] = new_qty
            if new_qty > Decimal(0):
                state[ticker]["average_price"] = (curr_qty * curr_avg) / new_qty
        elif "grupamento" in mov_type:
            curr_qty = state[ticker]["quantity"]
            curr_avg = state[ticker]["average_price"]
            new_qty = max(Decimal(0), curr_qty - qty)
            state[ticker]["quantity"] = new_qty
            if new_qty > Decimal(0):
                state[ticker]["average_price"] = (curr_qty * curr_avg) / new_qty

    return [{**item, "average_price": round(item["average_price"], 4), "average_price_known": True} for item in state.values()]


def _extract_sheet_rows(sheet_tree, sst):
    sheet_data = sheet_tree.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData")
    if sheet_data is None:
        return []
    rows = []
    for row in sheet_data.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
        cells = []
        for c in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
            t = c.get("t")
            v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
            val = v.text if v is not None else ""
            if t == "s" and val.isdigit() and int(val) < len(sst):
                val = sst[int(val)]
            cells.append(val)
        rows.append(cells)
    return rows


def _parse_b3_movimentacao_xlsx(z, sst, sheets, rel_map):
    parsed_rows = []
    r_counter = 0
    for s in sheets:
        rId = s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = "xl/" + rel_map[rId]
        sheet_tree = ET.fromstring(z.read(target))
        rows = _extract_sheet_rows(sheet_tree, sst)
        headers = None
        for cells in rows:
            if not headers:
                h_lower = [str(x or "").strip().lower() for x in cells]
                if any("moviment" in h or "produto" in h for h in h_lower):
                    headers = [str(h or "").strip() for h in cells]
                continue
            row_dict = {headers[idx]: cells[idx] for idx in range(min(len(headers), len(cells)))}
            r_counter += 1
            parsed_rows.append((r_counter, row_dict))
    return _consolidate_movimentacao(parsed_rows)


def _parse_b3_posicao_xlsx(z, sst, sheets, rel_map):
    results = {}
    for s in sheets:
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
        rows = _extract_sheet_rows(sheet_tree, sst)

        headers = None
        for cells in rows:
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
            # Custódia informa cotação de fechamento, não custo de aquisição.
            price = Decimal(0)

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
                    "average_price_known": False,
                }
    return list(results.values())


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

        sheets = wb_tree.findall(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet"
        )
        sheet_names = [s.attrib["name"].strip() for s in sheets]

        # Se houver aba de movimentação, usamos o consolidador de extrato
        if any("moviment" in s.lower() for s in sheet_names):
            return _parse_b3_movimentacao_xlsx(z, sst, sheets, rel_map)

        return _parse_b3_posicao_xlsx(z, sst, sheets, rel_map)


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
    rows_iter = csv.reader(text.splitlines(), delimiter=delimiter)
    headers = None
    is_mov = False
    parsed_rows = []
    pos_results = {}
    r_idx = 0

    for row in rows_iter:
        if not headers:
            h_lower = [str(x or "").strip().lower() for x in row]
            if any("moviment" in h for h in h_lower) or (
                any("entrada/sa" in h for h in h_lower) and any("preço" in h or "preco" in h for h in h_lower)
            ):
                headers = [str(h or "").strip() for h in row]
                is_mov = True
            elif any("código" in h or "codigo" in h or "produto" in h or "ticker" in h for h in h_lower):
                headers = [str(h or "").strip() for h in row]
                is_mov = False
            continue

        row_dict = {headers[idx]: row[idx] for idx in range(min(len(headers), len(row)))}
        if is_mov:
            r_idx += 1
            parsed_rows.append((r_idx, row_dict))
        else:
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
            price = Decimal(0)
            tipo = str(row_dict.get("Tipo") or "").upper()
            if "BDR" in tipo or ticker.endswith(("34", "35", "39")):
                asset_class = "bdr"
            elif "COTAS" in tipo or (ticker.endswith("11") and ("FII" in prod.upper() or "FDO" in prod.upper())):
                asset_class = "fii"
            elif "ETF" in tipo or "INDEX" in prod.upper():
                asset_class = "etf"
            else:
                asset_class = "acao"

            if ticker in pos_results:
                pos_results[ticker]["quantity"] += qty
            else:
                pos_results[ticker] = {
                    "ticker": ticker,
                    "name": name[:150],
                    "asset_class": asset_class,
                    "quantity": qty,
                    "average_price": price,
                    "average_price_known": False,
                }

    if is_mov:
        return _consolidate_movimentacao(parsed_rows)
    return list(pos_results.values())


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


def portfolio_history(db, days=30):
    """Estima a posição atual aos preços históricos; não reconstrói operações."""
    assets = db.scalars(select(Asset).where(Asset.quantity > 0)).all()
    if not assets:
        return []

    asset_map = {
        a.id: {
            "ticker": a.ticker,
            "quantity": float(a.quantity),
            "cost": float(a.quantity * a.average_price),
        }
        for a in assets
    }
    total_cost = sum(a["cost"] for a in asset_map.values())
    since = utcnow() - timedelta(days=days)
    last_known = {}
    for asset in assets:
        previous = db.scalar(
            select(Quote).where(Quote.asset_id == asset.id, Quote.quoted_at < since, Quote.currency == "BRL")
            .order_by(Quote.quoted_at.desc()).limit(1)
        )
        if previous:
            last_known[asset.id] = float(previous.price)

    quotes = db.scalars(
        select(Quote)
        .where(Quote.asset_id.in_(list(asset_map.keys())), Quote.quoted_at >= since, Quote.currency == "BRL")
        .order_by(Quote.quoted_at.asc())
    ).all()

    if not quotes:
        return []

    daily_quotes = {}
    for q in quotes:
        day_str = q.quoted_at.strftime("%Y-%m-%d")
        if day_str not in daily_quotes:
            daily_quotes[day_str] = {}
        daily_quotes[day_str][q.asset_id] = float(q.price)

    history = []
    for day_str in sorted(daily_quotes.keys()):
        last_known.update(daily_quotes[day_str])
        missing = [info["ticker"] for aid, info in asset_map.items() if aid not in last_known]
        day_total = sum(
            ainfo["quantity"] * last_known.get(aid, 0.0)
            for aid, ainfo in asset_map.items()
        )
        gain = day_total - total_cost
        gain_pct = ((day_total / total_cost) - 1) * 100 if total_cost > 0 else 0.0
        history.append(
            {
                "date": day_str,
                "total": None if missing else round(day_total, 2),
                "cost": round(total_cost, 2),
                "gain": None if missing else round(gain, 2),
                "gain_pct": None if missing else round(gain_pct, 2),
                "partial": bool(missing),
                "missing_positions": missing,
                "estimated": True,
            }
        )

    return history
