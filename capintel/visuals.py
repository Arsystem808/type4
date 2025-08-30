
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

COLORS = ["#FFA500", "#FFFACD", "#40E0D0", "#7CFC00"]  # orange, light yellow, turquoise, lime green
BOUNDS_DEG = [(-180, -135), (-135, -90), (-90, -45), (-45, 0)]

def _zone_index(score: float) -> int:
    if score < -1: return 0
    if score < 0:  return 1
    if score < 1:  return 2
    return 3

def render_sentiment_gauge(score: float, sell: int = 0, neutral: int = 0, buy: int = 0, show_numbers: bool = True):
    """
    Полукруглый индикатор [-2..+2] в строгом стиле.
    — Чистая дуга без лишнего текста
    — Тёмный фон под Streamlit Dark
    — Акцентная подсветка активной зоны
    """
    score = max(-2.0, min(2.0, float(score)))

    # Геометрия
    theta = np.linspace(-np.pi, 0, 256)
    x, y = np.cos(theta), np.sin(theta)

    fig, ax = plt.subplots(figsize=(6.8, 3.6), dpi=200)
    # Под цвет темной темы Streamlit
    fig.patch.set_facecolor("#0E1117")
    ax.set_facecolor("#0E1117")

    # Сегменты дуги
    for (a0, a1), c in zip(BOUNDS_DEG, COLORS):
        ax.add_patch(Wedge((0, 0), 1.0, a0, a1, width=0.16, facecolor=c, edgecolor="none", alpha=0.95))

    # Активная зона (полупрозрачная «светящаяся» подложка)
    zi = _zone_index(score)
    a0, a1 = BOUNDS_DEG[zi]
    ax.add_patch(Wedge((0, 0), 1.02, a0, a1, width=0.20, facecolor=COLORS[zi], alpha=0.25, edgecolor="none"))

    # Внешняя обводка
    ax.plot(x, y, color="white", linewidth=2.0, solid_capstyle="round", alpha=0.9)

    # Засечки и числовая шкала
    ticks = np.linspace(-np.pi, 0, 5)  # -2, -1, 0, +1, +2
    labels = ["-2", "-1", "0", "+1", "+2"]
    for t in ticks:
        ax.plot([0.90*np.cos(t), 1.0*np.cos(t)], [0.90*np.sin(t), 1.0*np.sin(t)], color="white", linewidth=2, alpha=0.9)
    if show_numbers:
        for t, lab in zip(ticks, labels):
            ax.text(1.08*np.cos(t), 1.08*np.sin(t), lab, color="white", ha="center", va="center", fontsize=10)

    # Стрелка
    angle = (score + 2.0) / 4.0 * np.pi - np.pi
    ax.plot([0, 0.84*np.cos(angle)], [0, 0.84*np.sin(angle)], color="white", linewidth=4.5, solid_capstyle="round")
    ax.scatter([0], [0], s=28, c="white")

    # Заголовок и метка
    ax.text(0, 1.12, "Общая оценка", color="white", ha="center", va="bottom", fontsize=14, weight="bold")
    label = "Нейтрально"
    if score > 1.0: label = "Активно покупать"
    elif score > 0.15: label = "Покупать"
    elif score < -1.0: label = "Активно продавать"
    elif score < -0.15: label = "Продавать"
    ax.text(0, -0.22, label, color="white", ha="center", va="center", fontsize=12, weight="bold")

    # Итог
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig
