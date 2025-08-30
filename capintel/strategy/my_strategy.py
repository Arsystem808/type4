# -*- coding: utf-8 -*-
"""
Стратегия: Pivot(Fibonacci) + Heikin Ashi + MACD Histogram + RSI(Wilder) + ATR
Мульти-ТФ: ST=weekly pivot, MID=monthly pivot, LT=yearly pivot
Авторские правила «перегрев у крыши» / «перепроданность у дна»
Возвращает словарь-спеку; Signal-модель собирает engine.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, List
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import httpx

# берём внутренние утилиты клиента Polygon
from capintel.providers import polygon_client as poly


# ------------------------- вспомогалки -------------------------

def _ema(series: pd.Series, span: int, wilder: bool = False) -> pd.Series:
    alpha = (1.0 / span) if wilder else (2.0 / (span + 1.0))
    return series.ewm(alpha=alpha, adjust=False).mean()

def _rsi_wilder(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0.0)
    down = (-d).clip(lower=0.0)
    au = _ema(up, n, wilder=True)
    ad = _ema(down, n, wilder=True)
    rs = au / (ad.replace(0, np.nan))
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def _atr_wilder(df: pd.DataFrame, n: int = 14) -> pd.Series:
    # ожидает колонки: o,h,l,c
    h, l, c = df["h"].astype(float), df["l"].astype(float), df["c"].astype(float)
    cshift = c.shift(1)
    tr = pd.concat(
        [h - l, (h - cshift).abs(), (l - cshift).abs()],
        axis=1
    ).max(axis=1)
    atr = _ema(tr, n, wilder=True)
    return atr

def _macd_hist(close: pd.Series) -> pd.Series:
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd = ema12 - ema26
    signal = _ema(macd, 9)
    hist = macd - signal
    return hist

def _heikin_ashi(bars: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    # bars: o,h,l,c
    o = bars["o"].astype(float).values
    h = bars["h"].astype(float).values
    l = bars["l"].astype(float).values
    c = bars["c"].astype(float).values

    ha_close = (o + h + l + c) / 4.0
    ha_open = np.zeros_like(ha_close)
    ha_open[0] = (o[0] + c[0]) / 2.0
    for i in range(1, len(ha_open)):
        ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2.0
    return pd.Series(ha_open, index=bars.index), pd.Series(ha_close, index=bars.index)

def _last_streak_length(values: pd.Series, positive: bool = True) -> int:
    """длина последней серии знаков (для MACD hist, HA цвета и т.п.)"""
    if len(values) == 0:
        return 0
    sign = 1 if positive else -1
    arr = np.sign(values.values)
    ln = 0
    for x in arr[::-1]:
        if (x > 0 and sign > 0) or (x < 0 and sign < 0):
            ln += 1
        elif x == 0:
            # считаем нули нейтральными (разрывают серию)
            break
        else:
            break
    return ln

def _deceleration_abs(values: pd.Series, lookback: int = 3) -> bool:
    """замедление: убывание |hist| последние n баров"""
    if len(values) < lookback + 3:
        return False
    v = values.dropna().values
    tail = np.abs(v[-lookback:])
    return bool(np.all(tail[1:] <= tail[:-1]))  # не растёт по модулю

def _fibo_pivots(H: float, L: float, C: float) -> Dict[str, float]:
    P = (H + L + C) / 3.0
    d = H - L
    return {
        "P": P,
        "R1": P + 0.382 * d,
        "R2": P + 0.618 * d,
        "R3": P + 1.000 * d,
        "S1": P - 0.382 * d,
        "S2": P - 0.618 * d,
        "S3": P - 1.000 * d,
    }

def _fetch_daily_bars(asset_class: str, ticker: str, days: int = 500) -> pd.DataFrame:
    """Дневные бары (для расчёта недельных/месячных/годовых пивотов)."""
    if asset_class == "crypto":
        base, quote = poly._norm_crypto_pair(ticker)  # noqa
        tkr = f"X:{base}{quote}"
    else:
        tkr = ticker.upper()

    # берем ~days последних календарных дней
    to = datetime.now(timezone.utc).date()
    fr = (to - timedelta(days=days))
    url = f"{poly.BASE}/v2/aggs/ticker/{tkr}/range/1/day/{fr}/{to}?adjusted=true&limit=50000&sort=asc"  # noqa

    with httpx.Client(timeout=20) as c:
        r = c.get(url, headers=poly._headers())  # noqa
        r.raise_for_status()
        data = r.json()
    rows = (data or {}).get("results") or []
    if not rows:
        return pd.DataFrame(columns=["t", "o", "h", "l", "c", "v"])

    df = pd.DataFrame(rows)[["t", "o", "h", "l", "c", "v"]].copy()
    # Polygon даёт мс → сек
    if df["t"].max() > 1e12:
        df["t"] = (df["t"] / 1000).astype(int)
    df["dt"] = pd.to_datetime(df["t"], unit="s", utc=True)
    df.set_index("dt", inplace=True)
    return df[["o", "h", "l", "c", "v"]]

def _last_complete_period_hlc(df_daily: pd.DataFrame, period: str) -> Tuple[float, float, float]:
    """
    period: 'W' (неделя, Mon-Sun), 'M' (месяц), 'Y' (год)
    Возвращает H,L,C для последнего *завершённого* периода.
    """
    if df_daily.empty:
        raise ValueError("Нет данных для расчёта HLC предыдущего периода")

    if period == "W":
        g = df_daily.groupby(pd.Grouper(freq="W-MON", label="right"))
    elif period == "M":
        g = df_daily.groupby(pd.Grouper(freq="M", label="right"))
    elif period == "Y":
        g = df_daily.groupby(pd.Grouper(freq="Y", label="right"))
    else:
        raise ValueError("period must be 'W', 'M' or 'Y'")

    agg = g.agg({"h": "max", "l": "min", "c": "last"}).dropna()
    if len(agg) < 2:
        # на всякий случай fallback: берём хвост по количеству торговых дней
        window = {"W": 5, "M": 22, "Y": 252}[period]
        tail = df_daily.tail(window)
        return float(tail["h"].max()), float(tail["l"].min()), float(tail["c"].iloc[-1])
    # берём предыдущий завершённый (последнюю строку исключаем как текущий незавершённый)
    H = float(agg.iloc[-2]["h"])
    L = float(agg.iloc[-2]["l"])
    C = float(agg.iloc[-2]["c"])
    return H, L, C

def _near(price: float, level: float, tol: float) -> bool:
    if level <= 0:
        return False
    return abs(price - level) / level <= tol

def _horizon_params(horizon: str) -> Dict[str, Any]:
    # thresholds & tolerances
    return {
        "intraday": dict(tag="ST", ha=4, macd=4, tol=0.0065),
        "swing":    dict(tag="MID", ha=5, macd=6, tol=0.0090),
        "position": dict(tag="LT", ha=6, macd=8, tol=0.0120),
    }[horizon]


# ------------------------- основная логика -------------------------

def generate_signal_core(
    ticker: str,
    asset_class: str,     # "crypto" | "equity"
    horizon: str,         # "intraday" | "swing" | "position"
    last_price: float,
    bars: pd.DataFrame | None = None,
) -> Dict[str, Any]:
    """
    Возвращает спеку сигнала (dict), которую обернёт движок в pydantic-модель.
    Ключи: action, entry, take_profit [tp1,tp2], stop, confidence, narrative_ru, alt
    """
    params = _horizon_params(horizon)
    tol = params["tol"]
    ha_min = params["ha"]
    macd_min = params["macd"]

    # --- 1) Пивоты текущего горизонта и старшего ТФ для подтверждения ---
    daily = _fetch_daily_bars(asset_class, ticker, days=520)

    if horizon == "intraday":         # ST → weekly
        H, L, C = _last_complete_period_hlc(daily, "W")
        high_HLC = _last_complete_period_hlc(daily, "M")  # старший ТФ для подтверждения
    elif horizon == "swing":          # MID → monthly
        H, L, C = _last_complete_period_hlc(daily, "M")
        high_HLC = _last_complete_period_hlc(daily, "Y")
    else:                              # LT → yearly
        H, L, C = _last_complete_period_hlc(daily, "Y")
        # Для LT старший ТФ отсутствует — используем тот же как «нейтральный»
        high_HLC = (H, L, C)

    piv = _fibo_pivots(H, L, C)
    piv_hi = _fibo_pivots(*high_HLC)

    # --- 2) Индикаторы по рабочему ТФ (bars приходит из движка) ---
    if bars is None or len(bars) < 50:
        # если bars нет — соберём минимальный набор с day (не идеально, но лучше, чем ничего)
        bars = daily.copy()
    # стандартизируем колонки, индекс — datetime
    b = bars.copy()
    if "dt" in b.columns:
        b = b.set_index(pd.to_datetime(b["dt"], utc=True))
    elif "t" in b.columns and not isinstance(b.index, pd.DatetimeIndex):
        b = b.set_index(pd.to_datetime(b["t"], unit="s", utc=True))
    b = b[["o", "h", "l", "c"]].astype(float).dropna()

    ha_o, ha_c = _heikin_ashi(b)
    ha_green = (ha_c > ha_o)
    ha_red   = (ha_c < ha_o)
    ha_green_streak = _last_streak_length((ha_c - ha_o), positive=True)
    ha_red_streak   = _last_streak_length((ha_c - ha_o), positive=False)
    ha_long_green = ha_green_streak >= ha_min
    ha_long_red   = ha_red_streak   >= ha_min
    # смена цвета после длинной серии
    ha_flip_down = ha_long_green and ha_red.iloc[-1]
    ha_flip_up   = ha_long_red and ha_green.iloc[-1]

    close = b["c"].astype(float)
    hist = _macd_hist(close)
    macd_pos_streak = _last_streak_length(hist, positive=True)
    macd_neg_streak = _last_streak_length(hist, positive=False)
    macd_long_pos = macd_pos_streak >= macd_min
    macd_long_neg = macd_neg_streak >= macd_min
    macd_decel_pos = _deceleration_abs(hist.clip(lower=0))
    macd_decel_neg = _deceleration_abs((-hist).clip(lower=0))

    rsi = _rsi_wilder(close, 14)
    q20, q80 = np.nanpercentile(rsi.tail(200), [20, 80]) if len(rsi) >= 50 else (30.0, 70.0)
    rsi_high = (rsi.iloc[-1] > max(70.0, q80))
    rsi_low  = (rsi.iloc[-1] < min(30.0, q20))

    atr = _atr_wilder(b, 14)
    last_atr = float(atr.iloc[-1]) if len(atr) else (abs(H - L) / 14.0)

    price = float(last_price)

    # --- 3) Композитные условия ---
    near_R2 = _near(price, piv["R2"], tol)
    near_R3 = _near(price, piv["R3"], tol)
    near_S2 = _near(price, piv["S2"], tol)
    near_S3 = _near(price, piv["S3"], tol)

    # Overheat у крыши
    overheat = ( (near_R2 or near_R3) and
                 ((ha_long_green or macd_long_pos) and (macd_decel_pos or rsi_high)) )

    # Oversold у дна
    oversold = ( (near_S2 or near_S3) and
                 ((ha_long_red or macd_long_neg) and (macd_decel_neg or rsi_low)) )

    # Старший ТФ — направление
    hi_bias_up = price > piv_hi["R1"]
    hi_bias_dn = price < piv_hi["S1"]
    hi_bias_neutral = not (hi_bias_up or hi_bias_dn)

    # --- 4) Решение, уровни, стопы/цели ---
    action = "WAIT"
    entry = price
    tp1 = tp2 = price
    stop = price
    narrative_bits: List[str] = []

    if overheat:
        narrative_bits.append("Перегрев у крыши: цена в зоне R2/R3, длинная зелёная серия HA и/или длинная положительная серия MACD с замедлением; RSI повышенный.")
        strong = near_R3 or (macd_pos_streak >= (macd_min + 2) and rsi_high)
        # базовое действие — WAIT; при сильном сигнале даём активный SHORT
        if strong:
            action = "SHORT"
        else:
            action = "WAIT"

        if near_R3:
            tp1, tp2 = piv["R2"], piv["P"]
            stop = piv["R3"] * (1.0 + tol)
        else:  # у R2
            tp1 = (piv["P"] + piv["S1"]) / 2.0
            tp2 = piv["S2"] if strong else piv["S1"]
            stop = piv["R2"] * (1.0 + tol)

    elif oversold:
        narrative_bits.append("Перепроданность у дна: цена в зоне S2/S3, длинная красная серия HA и/или отрицательная серия MACD с замедлением; RSI понижен.")
        strong = near_S3 or (macd_neg_streak >= (macd_min + 2) and rsi_low)
        action = "BUY" if strong else "WAIT"

        if near_S3:
            tp1, tp2 = piv["S2"], piv["P"]
            stop = piv["S3"] * (1.0 - tol)
        else:  # у S2
            tp1 = (piv["P"] + piv["R1"]) / 2.0
            tp2 = piv["R2"] if strong else piv["R1"]
            stop = piv["S2"] * (1.0 - tol)

    else:
        # В середине диапазона — уходим в WAIT,
        # либо можем дать аккуратные ATR-цели как ориентиры.
        narrative_bits.append("Цена не у краёв диапазона по пивотам — рациональнее подождать подтверждения.")
        action = "WAIT"
        # мягкие ориентиры по ATR (на случай, если трейдер всё же торгует)
        tp1 = entry + (0.6 * last_atr)
        tp2 = entry + (1.1 * last_atr)
        stop = entry - (0.8 * last_atr)

    # --- 5) Confidence + мульти-ТФ согласование ---
    if action in ("BUY", "SHORT"):
        conf = 0.60
        if (ha_long_green and macd_long_pos) or (ha_long_red and macd_long_neg):
            conf += 0.06
        if (rsi_high and action == "SHORT") or (rsi_low and action == "BUY"):
            conf += 0.03
        if near_R3 or near_S3:
            conf += 0.03

        if hi_bias_up and action == "SHORT":
            conf -= 0.06
            narrative_bits.append("Старший ТФ бычий — шорт агрессивный, снижаем уверенность.")
        elif hi_bias_dn and action == "BUY":
            conf -= 0.06
            narrative_bits.append("Старший ТФ медвежий — лонг контртрендовый, снижаем уверенность.")
        elif (hi_bias_up and action == "BUY") or (hi_bias_dn and action == "SHORT"):
            conf += 0.04
            narrative_bits.append("Старший ТФ в ту же сторону — усиливаем сценарий.")

        confidence = float(max(0.52, min(0.90, conf)))
    else:
        # WAIT
        confidence = 0.55
        if overheat or oversold:
            confidence = 0.58  # есть идея, но ждём триггера
        if hi_bias_neutral:
            confidence -= 0.01

    # --- 6) Альтернативный план (зеркально базовым правилам) ---
    alt: Dict[str, Any] | None = None
    if overheat:
        # альтернатива для консерватора: WAIT / подтверждение
        alt = dict(
            if_condition="если появится разворотный бар у R2/R3 (rejection) или сменится цвет HA",
            action="SHORT",
            entry=float(entry),
            take_profit=[float(tp1), float(tp2)],
            stop=float(stop),
        )
    elif oversold:
        alt = dict(
            if_condition="если появится разворотный бар у S2/S3 (rejection) или сменится цвет HA",
            action="BUY",
            entry=float(entry),
            take_profit=[float(tp1), float(tp2)],
            stop=float(stop),
        )
    else:
        alt = dict(
            if_condition="если цена подойдёт к R2/R3 или S2/S3 с признаками остановки",
            action="WAIT",
            entry=float(entry),
            take_profit=[float(tp1), float(tp2)],
            stop=float(stop),
        )

    # округления и санитация (движок ещё раз проверит)
    entry = float(entry)
    tp1, tp2, stop = float(tp1), float(tp2), float(stop)

    # текст-нарратив
    horizon_ru = {"intraday": "краткосрок (ST)", "swing": "среднесрок (MID)", "position": "долгосрок (LT)"}[horizon]
    nar = (
        f"{horizon_ru}. "
        + (" ".join(narrative_bits) or "Ситуация нейтральная.")
        + f" Пивоты(Fibo): P={piv['P']:.4f}, R2={piv['R2']:.4f}, R3={piv['R3']:.4f}, "
          f"S2={piv['S2']:.4f}, S3={piv['S3']:.4f}."
    )

    return dict(
        action=action,
        entry=entry,
        take_profit=[tp1, tp2],
        stop=stop,
        confidence=confidence,
        narrative_ru=nar,
        alt=alt,
    )

