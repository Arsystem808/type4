
from typing import Literal

Action = Literal["BUY", "SHORT", "CLOSE", "WAIT"]

def trader_tone_narrative_ru(action: Action, horizon: str, last_price: float) -> str:
    base = {
        "intraday": "Действуем осторожно, ориентируясь на цену здесь и сейчас.",
        "swing": "Смотрим на 1–3 дня вперёд.",
        "position": "Фокус на устойчивости уровней и движении на недели."
    }[horizon]
    return {
        "BUY":   f"Покупатели удерживают инициативу — берём вход с контролем риска. {base}",
        "SHORT": f"Рынок теряет импульс — ищем отбой для короткой позиции. {base}",
        "CLOSE": f"Движение выработано — фиксируем результат и выходим. {base}",
        "WAIT":  f"Сигнал неочевиден — ждём подтверждения и бережём капитал. {base}",
    }[action]
