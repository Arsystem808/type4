
import numpy as np
from .schemas import Signal

def toy_backtest(signal: Signal, n_steps: int = 400, step_bp: float = 15.0, fee_bp: float = 2.0):
    entry = signal.entry; action = signal.action
    rng = np.random.default_rng(42)
    steps = rng.normal(0.0, step_bp/10000.0, n_steps)
    price = entry + (steps * entry).cumsum()
    tp1, tp2 = signal.take_profit; stop = signal.stop
    exit_price = entry
    for i, p in enumerate(price):
        if action == "BUY":
            if p >= tp2: exit_price = tp2; break
            if p >= tp1: exit_price = tp1; break
            if p <= stop: exit_price = stop; break
        elif action == "SHORT":
            if p <= tp2: exit_price = tp2; break
            if p <= tp1: exit_price = tp1; break
            if p >= stop: exit_price = stop; break
        else:
            exit_price = entry; break
    pnl = 0.0 if action in ["WAIT","CLOSE"] else (exit_price-entry)/entry if action=="BUY" else (entry-exit_price)/entry
    fees = fee_bp/10000.0 * (1 if action in ["BUY","SHORT"] else 0)
    return {"steps": int(i), "exit_price": float(exit_price), "pnl": float(pnl - fees), "equity": float(1+pnl-fees)}
