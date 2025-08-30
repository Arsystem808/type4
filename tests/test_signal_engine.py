
from capintel.signal_engine import build_signal

def test_levels_are_consistent():
    sig = build_signal("AAPL", "equity", "swing", 230.0)
    if sig.action == "BUY":
        assert sig.stop < sig.entry
        assert sig.take_profit[0] >= sig.entry
    elif sig.action == "SHORT":
        assert sig.stop > sig.entry
        assert sig.take_profit[0] <= sig.entry
