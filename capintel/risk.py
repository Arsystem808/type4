
from typing import Literal, Tuple

def target_vol_position_size(confidence: float, asset_class: str, horizon: str) -> float:
    caps = {
        ("crypto", "intraday"): 1.2,
        ("crypto", "swing"): 1.6,
        ("crypto", "position"): 2.0,
        ("equity", "intraday"): 0.8,
        ("equity", "swing"): 1.2,
        ("equity", "position"): 1.5,
    }
    cap = caps.get((asset_class, horizon), 1.0)
    size = 0.3 + confidence * (cap - 0.3)
    return round(size, 2)

def sanitize_levels(action: str, entry: float, tp1: float, tp2: float, stop: float) -> Tuple[float,float,float]:
    if action == "BUY":
        tp1 = max(tp1, entry * 1.001)
        tp2 = max(tp2, tp1 * 1.001)
        stop = min(stop, entry * 0.999)
    elif action == "SHORT":
        tp1 = min(tp1, entry * 0.999)
        tp2 = min(tp2, tp1 * 0.999)
        stop = max(stop, entry * 1.001)
    return tp1, tp2, stop
