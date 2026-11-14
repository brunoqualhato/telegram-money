import csv
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import html
import io
import json
import re
import xml.etree.ElementTree as ET
import httpx
from sqlalchemy import func, select
from ..config import settings
from ..db import aware, utcnow
from ..models import Asset, Document, ProviderState, Quote, TreasuryRate
from ..schemas import DocumentInput, EventInput
from .alerts import evaluate_rules, latest_quote
from .documents import save_document
from .events import upsert_event

TREASURY_URL = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"

OPEN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def open_http_client():
    return httpx.Client(headers=OPEN_HEADERS, timeout=15, follow_redirects=True)


def parse_date_dmy(val):
    if not val or val == "-":
        return None
    try:
        return datetime.strptime(str(val).strip(), "%d/%m/%Y").date()
    except Exception:
        return None


def state(db, name, error=None):
    row = db.get(ProviderState, name)
    if not row:
        row = ProviderState(name=name)
        db.add(row)
    row.updated_at = utcnow()
    row.last_error = error
    if error is None:
        row.last_success = utcnow()


def number(value):
    if value is None:
        return None
    result = Decimal(str(value))
    if not result.is_finite() or abs(result) > Decimal("1000000000000"):
        raise ValueError("Número inválido retornado pelo provedor")
    return result


def parse_time(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    return aware(datetime.fromisoformat(str(value).replace("Z", "+00:00")))


def parse_quote(data):
    price, change = number(data.get("regularMarketPrice")), number(data.get("regularMarketChangePercent"))
    if price is None or price <= 0 or change is None or change < -100:
        raise ValueError("Cotação incompleta ou inválida")
    return dict(
        price=price,
        change_pct=change,
        currency=data.get("currency", "BRL"),
        day_high=number(data.get("regularMarketDayHigh")),
        day_low=number(data.get("regularMarketDayLow")),
        high_52w=number(data.get("fiftyTwoWeekHigh")),
        low_52w=number(data.get("fiftyTwoWeekLow")),
        quoted_at=parse_time(data["regularMarketTime"]),
        source="brapi",
    )


def brapi_client():
    headers = {"Authorization": f"Bearer {settings().brapi_token}"} if settings().brapi_token else {}
    return httpx.Client(base_url="https://brapi.dev", headers=headers, timeout=20)


def fetch_open_quote(ticker: str, asset_class: str = "acao", client: httpx.Client | None = None):
    own = client is None
    c = client or open_http_client()
    try:
        sec = (
            "fundos-imobiliarios"
            if asset_class == "fii"
            else ("bdrs" if asset_class == "bdr" else ("etfs" if asset_class == "etf" else "acoes"))
        )
        url = f"https://statusinvest.com.br/{sec}/{ticker.lower()}"
        resp = c.get(url)
        if resp.status_code != 200 and sec != "acoes":
            resp = c.get(f"https://statusinvest.com.br/acoes/{ticker.lower()}")
        if resp.status_code != 200:
            return None
        text = resp.text
        m_price = re.search(r'Valor atual.*?<strong class="value">([^<]+)</strong>', text, re.S | re.I)
        if not m_price:
            return None
        price = Decimal(m_price.group(1).strip().replace(".", "").replace(",", "."))

        change_pct = Decimal(0)
        m_var = re.search(
            r'Variação do valor do ativo com base no dia anterior.*?class="material-icons[^"]*">([^<]+)</i>.*?<b class="v-align-middle">([^<]+)</b>',
            text,
            re.S | re.I,
        )
        if m_var:
            direction = m_var.group(1).strip()
            val_str = m_var.group(2).strip().replace("%", "").replace(".", "").replace(",", ".")
            change_pct = Decimal(val_str)
            if "down" in direction:
                change_pct = -change_pct

        low_52w = high_52w = None
        m_low = re.search(r'M[íi]n\. 52 semanas.*?<strong class="value">([^<]+)</strong>', text, re.S | re.I)
        if m_low:
            low_52w = Decimal(m_low.group(1).strip().replace(".", "").replace(",", "."))
        m_high = re.search(r'M[áa]x\. 52 semanas.*?<strong class="value">([^<]+)</strong>', text, re.S | re.I)
        if m_high:
            high_52w = Decimal(m_high.group(1).strip().replace(".", "").replace(",", "."))

        return dict(
            price=price,
            change_pct=change_pct,
            currency="BRL",
            day_high=None,
            day_low=None,
            high_52w=high_52w,
            low_52w=low_52w,
            quoted_at=utcnow(),
            source="open-b3",
        )
    finally:
        if own:
            c.close()


def _collect_quotes_brapi(db, client):
    count = 0
    for asset in db.scalars(select(Asset)).all():
        if asset.asset_class in ("cripto", "moeda"):
            state(
                db,
                f"quote:{asset.ticker}",
                "Classe cadastrada, mas o conector desta classe ainda não está implementado",
            )
            continue
        try:
            response = client.get("/api/v2/stocks/quote", params={"symbols": asset.ticker})
            response.raise_for_status()
            results = response.json().get("results", [])
            item = next(
                (r for r in results if r.get("requestedSymbol", r.get("symbol")) == asset.ticker), None
            )
            if not item or item.get("symbol") != asset.ticker or item.get("changed"):
                raise ValueError("Ticker ausente ou convertido pelo provedor; revise a lista")
            values = parse_quote(item["data"])
            previous = latest_quote(db, asset.id)
            if previous and values["quoted_at"] <= aware(previous.quoted_at):
                state(db, f"quote:{asset.ticker}")
                db.commit()
                continue
            quote = Quote(asset_id=asset.id, **values)
            db.add(quote)
            db.flush()
            if not asset.name:
                asset.name = item["data"].get("shortName", asset.ticker)[:150]
            evaluate_rules(db, asset, quote)
            state(db, f"quote:{asset.ticker}")
            db.commit()
            count += 1
        except (httpx.HTTPError, ValueError, KeyError, TypeError, InvalidOperation) as error:
            db.rollback()
            status = getattr(getattr(error, "response", None), "status_code", None)
            state(
                db,
                f"quote:{asset.ticker}",
                f"Falha de coleta ({status or type(error).__name__}).",
            )
            db.commit()
    return count


def collect_quotes(db, client=None):
    if client is not None:
        return _collect_quotes_brapi(db, client)

    if settings().brapi_token:
        try:
            with brapi_client() as c:
                res = _collect_quotes_brapi(db, c)
                if res > 0:
                    return res
        except Exception:
            pass

    # Provedor aberto e gratuito da B3
    count = 0
    with open_http_client() as open_c:
        for asset in db.scalars(select(Asset)).all():
            if asset.asset_class in ("cripto", "moeda"):
                state(db, f"quote:{asset.ticker}", "Classe sem conector ativo")
                continue
            try:
                values = fetch_open_quote(asset.ticker, asset.asset_class, client=open_c)
                if not values:
                    state(db, f"quote:{asset.ticker}", "Ativo não encontrado na consulta aberta")
                    continue
                previous = latest_quote(db, asset.id)
                if previous and values["quoted_at"] <= aware(previous.quoted_at):
                    state(db, f"quote:{asset.ticker}")
                    db.commit()
                    continue
                quote = Quote(asset_id=asset.id, **values)
                db.add(quote)
                db.flush()
                evaluate_rules(db, asset, quote)
                state(db, f"quote:{asset.ticker}")
                db.commit()
                count += 1
            except Exception as error:
                db.rollback()
                state(db, f"quote:{asset.ticker}", f"Falha de coleta aberta ({type(error).__name__}).")
                db.commit()
    return count


def fetch_open_dividends(ticker: str, asset_class: str = "acao", client: httpx.Client | None = None):
    own = client is None
    c = client or open_http_client()
    try:
        sec = (
            "fundos-imobiliarios"
            if asset_class == "fii"
            else ("bdrs" if asset_class == "bdr" else ("etfs" if asset_class == "etf" else "acoes"))
        )
        url = f"https://statusinvest.com.br/{sec}/{ticker.lower()}"
        resp = c.get(url)
        if resp.status_code != 200 and sec != "acoes":
            resp = c.get(f"https://statusinvest.com.br/acoes/{ticker.lower()}")
        if resp.status_code != 200:
            return []
        m = re.search(r'id="results"[^\>]*value="([^"]+)"', resp.text)
        if not m:
            return []
        raw = json.loads(html.unescape(m.group(1)))
        events = []
        labels = {
            "DIVIDENDO": "dividendo",
            "DIVIDENDOS": "dividendo",
            "JCP": "jcp",
            "JUROS SOBRE CAPITAL PRÓPRIO": "jcp",
            "JUROS SOBRE CAPITAL PROPRIO": "jcp",
            "RENDIMENTO": "rendimento",
            "REND. TRIBUTADO": "rendimento",
            "AMORTIZAÇÃO": "amortizacao",
            "AMORTIZACAO": "amortizacao",
        }
        for item in raw:
            kind = labels.get(str(item.get("et") or item.get("etd") or "").upper(), "dividendo")
            raw_val = item.get("v") or item.get("sv") or "0"
            try:
                amt = (
                    Decimal(str(raw_val).replace(".", "").replace(",", "."))
                    if isinstance(raw_val, str)
                    else Decimal(str(raw_val))
                )
            except Exception:
                continue
            if amt <= 0:
                continue
            com = parse_date_dmy(item.get("ed"))
            payment = parse_date_dmy(item.get("pd"))
            events.append(
                {
                    "ticker": ticker,
                    "kind": kind,
                    "amount": amt,
                    "com_date": com,
                    "payment_date": payment,
                    "source_url": url,
                }
            )
        return events
    finally:
        if own:
            c.close()


def collect_dividends(db, client=None):
    labels = {
        "DIVIDENDO": "dividendo",
        "DIVIDENDOS": "dividendo",
        "JCP": "jcp",
        "JUROS SOBRE CAPITAL PROPRIO": "jcp",
        "JUROS SOBRE CAPITAL PRÓPRIO": "jcp",
        "RENDIMENTO": "rendimento",
        "AMORTIZAÇÃO": "amortizacao",
        "AMORTIZACAO": "amortizacao",
    }
    count = 0
    assets = db.scalars(select(Asset).where(Asset.asset_class.in_(["acao", "fii", "bdr", "etf"]))).all()

    # Se cliente mock foi fornecido em testes ou se há token brapi configurado
    if client is not None or (settings().brapi_token and client is None):
        with client if client is not None else brapi_client() as c:
            for asset in assets:
                try:
                    endpoint = (
                        "/api/v2/fii/dividends"
                        if asset.asset_class == "fii"
                        else "/api/v2/stocks/dividends"
                    )
                    response = c.get(
                        endpoint,
                        params={
                            "symbols": asset.ticker,
                            "startDate": (utcnow().date() - timedelta(days=30)).isoformat(),
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    rows = payload.get("dividends")
                    if rows is None:
                        rows = []
                        for result in payload.get("results", []):
                            data = result.get("data", {})
                            if isinstance(data, dict):
                                rows.extend(data.get("cashDividends", []))
                    for row in rows:
                        kind = labels.get(str(row.get("label", "")).upper())
                        if not kind or row.get("remarks"):
                            continue
                        symbol = row.get("symbol", asset.ticker)
                        if symbol != asset.ticker:
                            continue
                        identity = "|".join(
                            str(row.get(k) or "")
                            for k in ("label", "lastDatePrior", "approvedOn", "relatedTo")
                        )
                        source_id = (
                            "brapi:"
                            + asset.ticker
                            + ":"
                            + hashlib.sha256(identity.encode()).hexdigest()
                        )
                        event = EventInput(
                            source_id=source_id,
                            ticker=asset.ticker,
                            kind=kind,
                            amount=number(row.get("rawRate", row.get("rate"))),
                            announced_on=date_part(row.get("approvedOn")),
                            com_date=date_part(row.get("lastDatePrior")),
                            ex_date=date_part(row.get("exDate")),
                            payment_date=date_part(row.get("paymentDate")),
                            source_url=f"https://brapi.dev{endpoint}?symbols={asset.ticker}",
                        )
                        _, changed = upsert_event(db, event)
                        if changed:
                            count += 1
                    state(db, f"events:{asset.ticker}")
                    db.commit()
                except (httpx.HTTPError, ValueError, TypeError, KeyError, InvalidOperation):
                    db.rollback()

    # Provedor aberto e gratuito (Status Invest)
    with open_http_client() as open_c:
        for asset in assets:
            try:
                evs = fetch_open_dividends(asset.ticker, asset.asset_class, client=open_c)
                for ev in evs:
                    source_id = (
                        f"open:{asset.ticker}:{ev['kind']}:"
                        f"{ev['com_date'] or ''}:{ev['payment_date'] or ''}:{ev['amount']}"
                    )
                    event = EventInput(
                        source_id=source_id,
                        ticker=asset.ticker,
                        kind=ev["kind"],
                        amount=ev["amount"],
                        announced_on=None,
                        com_date=ev["com_date"],
                        ex_date=None,
                        payment_date=ev["payment_date"],
                        source_url=ev["source_url"],
                    )
                    _, changed = upsert_event(db, event)
                    if changed:
                        count += 1
                state(db, f"events:{asset.ticker}")
                db.commit()
            except Exception as e:
                db.rollback()
                state(db, f"events:{asset.ticker}", f"Falha ao coletar proventos abertos: {e}")
                db.commit()
    return count


def date_part(value):
    return date.fromisoformat(str(value)[:10]) if value else None


def fetch_open_news(ticker: str, limit: int = 5, client: httpx.Client | None = None):
    own = client is None
    c = client or open_http_client()
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+mercado+financeiro&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        resp = c.get(url)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.text)
        items = []
        for it in root.findall(".//item")[:limit]:
            title = it.find("title").text if it.find("title") is not None else ""
            link = it.find("link").text if it.find("link") is not None else ""
            pub_date = it.find("pubDate").text if it.find("pubDate") is not None else ""
            if title and link:
                items.append(
                    {
                        "ticker": ticker,
                        "title": title.strip(),
                        "link": link.strip(),
                        "pub_date": pub_date.strip(),
                    }
                )
        return items
    finally:
        if own:
            c.close()


def collect_news(db, client=None):
    own = client is None
    c = client or open_http_client()
    created = 0
    try:
        assets = db.scalars(select(Asset)).all()
        for asset in assets:
            try:
                items = fetch_open_news(asset.ticker, limit=3, client=c)
                for item in items:
                    title = item["title"][:200]
                    text = (
                        f"Notícia sobre {asset.ticker}: {item['title']}\n"
                        f"Data: {item['pub_date']}\n"
                        f"Link original: {item['link']}"
                    )
                    doc = DocumentInput(
                        ticker=asset.ticker,
                        title=title,
                        kind="noticia",
                        source_url=item["link"][:500],
                        text=text[:200_000],
                    )
                    before_count = db.scalar(select(func.count()).select_from(Document))
                    save_document(db, doc)
                    after_count = db.scalar(select(func.count()).select_from(Document))
                    if after_count > before_count:
                        created += 1
                state(db, f"news:{asset.ticker}")
                db.commit()
            except Exception as e:
                db.rollback()
                state(db, f"news:{asset.ticker}", f"Falha ao coletar notícias: {e}")
                db.commit()
        state(db, "noticias")
        db.commit()
        return created
    finally:
        if own:
            c.close()


def parse_treasury_csv(text):
    rows = []
    latest = None
    for row in csv.DictReader(io.StringIO(text.lstrip("\ufeff")), delimiter=";"):
        observed = datetime.strptime(row["Data Base"], "%d/%m/%Y").date()
        if latest is None or observed > latest:
            latest, rows = observed, []
        if observed == latest:
            rows.append(
                {
                    "title": f"{row['Tipo Titulo']} · {row['Data Vencimento']}",
                    "maturity": row["Data Vencimento"],
                    "rate": Decimal(row["Taxa Compra Manha"].replace(",", ".")),
                    "price": Decimal(row["PU Compra Manha"].replace(",", ".")),
                    "observed_on": observed,
                    "source_url": TREASURY_URL,
                }
            )
    if not rows:
        raise ValueError("O Tesouro não retornou taxas")
    return rows


def collect_treasury(db):
    try:
        chunks, size = [], 0
        with httpx.stream("GET", TREASURY_URL, timeout=60, follow_redirects=True) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > 40_000_000:
                    raise ValueError("CSV excede o limite de 40 MB")
                chunks.append(chunk)
        raw = b"".join(chunks)
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        rows = parse_treasury_csv(text)
        for values in rows:
            row = db.scalar(select(TreasuryRate).where(TreasuryRate.title == values["title"]))
            if row:
                for key, value in values.items():
                    setattr(row, key, value)
            else:
                db.add(TreasuryRate(**values))
        state(db, "tesouro")
        db.commit()
        return len(rows)
    except (httpx.HTTPError, ValueError, KeyError, InvalidOperation):
        db.rollback()
        state(db, "tesouro", "Falha ao ler CSV oficial do Tesouro. Taxas anteriores foram preservadas.")
        db.commit()
        return 0
