
import hashlib, random
from datetime import datetime, timedelta
from typing import Tuple, List
from .schemas import Signal, SignalAlternative, AssetClass, Horizon
from .risk import target_vol_position_size, sanitize_levels
from .narrator import trader_tone_narrative_ru

def _daily_seed(key: str) -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    s = hashlib.sha256((key + today).encode()).hexdigest()
    return int(s[:8], 16)

def _horizon_params(h: Horizon):
    return {"intraday": (25, 8), "swing": (60, 48), "position": (200, 7*24)}[h]

def choose_action(seed: int) -> str:
    random.seed(seed)
    return random.choices(["WAIT","BUY","SHORT","CLOSE"], weights=[0.35,0.30,0.30,0.05], k=1)[0]

def gen_levels(action: str, price: float, buffer_bp: int):
    bp = buffer_bp/10000.0
    if action == "BUY":
        entry = round(price * (1 - 0.3*bp), 4)
        tp1   = round(entry * (1 + 0.8*bp), 4)
        tp2   = round(entry * (1 + 1.8*bp), 4)
        stop  = round(entry * (1 - 0.9*bp), 4)
    elif action == "SHORT":
        entry = round(price * (1 + 0.3*bp), 4)
        tp1   = round(entry * (1 - 0.8*bp), 4)
        tp2   = round(entry * (1 - 1.8*bp), 4)
        stop  = round(entry * (1 + 0.9*bp), 4)
    else:
        entry=tp1=tp2=stop=price
    tp1,tp2,stop = sanitize_levels(action, entry, tp1, tp2, stop)
    return entry, [tp1,tp2], stop

def gen_confidence(seed: int, action: str) -> float:
    random.seed(seed + 1337)
    base = dict(WAIT=0.52, BUY=0.60, SHORT=0.60, CLOSE=0.55)[action]
    conf = max(0.50, min(0.90, base + random.uniform(-0.05, 0.08)))
    return round(conf, 2)

def alternative_scenario(action: str, entry: float, buffer_bp: int) -> SignalAlternative:
    bp = buffer_bp/10000.0
    if action == "BUY":
        alt_action="BUY"; alt_entry=round(entry*(1+0.6*bp),4)
        tp1=round(alt_entry*(1+0.9*bp),4); tp2=round(alt_entry*(1+1.9*bp),4); stop=round(alt_entry*(1-0.9*bp),4)
        cond=f"если цена закрепится выше ~{round(entry*(1+0.5*bp),4)}"
    elif action == "SHORT":
        alt_action="SHORT"; alt_entry=round(entry*(1-0.6*bp),4)
        tp1=round(alt_entry*(1-0.9*bp),4); tp2=round(alt_entry*(1-1.9*bp),4); stop=round(alt_entry*(1+0.9*bp),4)
        cond=f"если цена закрепится ниже ~{round(entry*(1-0.5*bp),4)}"
    else:
        alt_action="BUY"; alt_entry=round(entry*(1+0.8*bp),4)
        tp1=round(alt_entry*(1+1.0*bp),4); tp2=round(alt_entry*(1+2.0*bp),4); stop=round(alt_entry*(1-1.0*bp),4)
        cond=f"если цена вырвется выше ~{round(entry*(1+0.7*bp),4)}"
    tp1,tp2,stop = sanitize_levels(alt_action, alt_entry, tp1, tp2, stop)
    return SignalAlternative(if_condition=cond, action=alt_action, entry=alt_entry, take_profit=[tp1,tp2], stop=stop)

def build_signal(ticker: str, asset_class: AssetClass, horizon: Horizon, last_price: float) -> Signal:
    buffer_bp, expire_h = _horizon_params(horizon)
    seed = _daily_seed(f"{ticker}-{asset_class}-{horizon}")
    action = choose_action(seed)
    entry, tps, stop = gen_levels(action, last_price, buffer_bp)
    confidence = gen_confidence(seed, action)
    size_pct = target_vol_position_size(confidence, asset_class, horizon)
    now = datetime.utcnow(); exp = now + timedelta(hours=expire_h)
    narrative = trader_tone_narrative_ru(action, horizon, last_price)
    alt = alternative_scenario(action, entry, buffer_bp)
    return Signal(
        id=f"{ticker}-{now.strftime('%Y%m%d%H%M%S')}-{horizon}",
        ticker=ticker.upper(), asset_class=asset_class, horizon=horizon,
        action=action, entry=entry, take_profit=tps, stop=stop,
        confidence=confidence, position_size_pct_nav=size_pct,
        created_at=now, expires_at=exp, narrative_ru=narrative,
        alternatives=[alt],
    )
