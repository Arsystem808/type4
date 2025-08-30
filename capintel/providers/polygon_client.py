
import os
from datetime import datetime, timedelta, timezone
from typing import Tuple
import httpx

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_KEY") or os.getenv("API_KEY")
BASE = "https://api.polygon.io"

class PolygonError(RuntimeError): pass

def _headers():
    if not POLYGON_API_KEY:
        raise PolygonError("POLYGON_API_KEY не задан. Укажи ключ в окружении или Secrets.")
    return {"Authorization": f"Bearer {POLYGON_API_KEY}"}

def _today_range_utc(hours_back: int = 48):
    now = datetime.now(timezone.utc); start = now - timedelta(hours=hours_back)
    return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

def _norm_crypto_pair(ticker: str) -> Tuple[str,str]:
    t = ticker.replace("X:", "").replace(":", "").replace("-", "").replace("_","").upper()
    if "/" in ticker: 
        a,b = ticker.upper().split("/"); return a,b
    for q in ("USDT","USD","EUR","GBP","RUB"):
        if t.endswith(q) and len(t)>len(q): return t[:-len(q)], q
    return t[:3], t[3:]

def last_trade_equity(ticker: str) -> float:
    url = f"{BASE}/v2/last/trade/{ticker.upper()}"
    with httpx.Client(timeout=10) as c:
        r = c.get(url, headers=_headers())
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and data.get("results", {}).get("price") is not None:
                return float(data["results"]["price"])
        fr,to = _today_range_utc(48)
        url2 = f"{BASE}/v2/aggs/ticker/{ticker.upper()}/range/1/minute/{fr}/{to}?adjusted=true&sort=desc&limit=1"
        r2 = c.get(url2, headers=_headers()); data2 = r2.json()
        res = (data2 or {}).get("results") or []
        if res: return float(res[0].get("c"))
    raise PolygonError(f"Не удалось получить цену для {ticker}")

def last_trade_crypto(pair: str) -> float:
    base, quote = _norm_crypto_pair(pair)
    url = f"{BASE}/v1/last/crypto/{base}/{quote}"
    with httpx.Client(timeout=10) as c:
        r = c.get(url, headers=_headers())
        if r.status_code == 200:
            d = r.json()
            price = (d.get('last',{}) or {}).get('price') or (d.get('lastTrade',{}) or {}).get('price')
            if price: return float(price)
        fr,to = _today_range_utc(72)
        xt = f"X:{base}{quote}"
        url2 = f"{BASE}/v2/aggs/ticker/{xt}/range/1/minute/{fr}/{to}?sort=desc&limit=1"
        r2 = c.get(url2, headers=_headers()); d2 = r2.json()
        res = (d2 or {}).get("results") or []
        if res: return float(res[0].get("c"))
    raise PolygonError(f"Не удалось получить цену для {pair}")

def get_last_price(asset_class: str, ticker: str) -> float:
    return last_trade_equity(ticker) if asset_class=="equity" else last_trade_crypto(ticker)
