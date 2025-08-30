
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

# Цвета зон слева направо
COLORS = ["#FFA500", "#FFFACD", "#40E0D0", "#7CFC00"]  # orange, light yellow, turquoise, lime green
BOUNDS_DEG = [(-180, -135), (-135, -90), (-90, -45), (-45, 0)]

def _zone_index(score: float) -> int:
    """Определяет активную зону по шкале [-2..+2]."""
    if score < -1: return 0
    if score < 0:  return 1
    if score < 1:  return 2
    return 3

def render_sentiment_gauge(score: float, sell: int = 8, neutral: int = 10, buy: int = 8, show_numbers: bool = True):
    """
    Полукруглый индикатор (-2 .. +2).
    + Числовая шкала: -2, -1, 0, +1, +2
    + Подсветка активной зоны (по score)
    """
    score = max(-2.0, min(2.0, float(score)))

    theta = np.linspace(-np.pi, 0, 128)
    x = np.cos(theta); y = np.sin(theta)

    fig, ax = plt.subplots(figsize=(6, 3.5))  # один график

    # Сегменты дуги
    for (a0, a1), c in zip(BOUNDS_DEG, COLORS):
        wedge = Wedge(center=(0,0), r=1.02, theta1=a0, theta2=a1, width=0.12, facecolor=c, edgecolor="none", alpha=1.0)
        ax.add_patch(wedge)

    # Подсветка активной зоны (поверх — тем же цветом, но чуть шире/толще)
    zi = _zone_index(score)
    a0, a1 = BOUNDS_DEG[zi]
    highlight = Wedge(center=(0,0), r=1.04, theta1=a0, theta2=a1, width=0.14, facecolor=COLORS[zi], edgecolor="black", alpha=0.35)
    ax.add_patch(highlight)

    # Внешняя дуга и засечки
    ax.plot(x, y, linewidth=1.8, color="black")
    ticks = np.linspace(-np.pi, 0, 5)  # -2, -1, 0, +1, +2
    for t in ticks:
        ax.plot([0.92*np.cos(t), 1.0*np.cos(t)], [0.92*np.sin(t), 1.0*np.sin(t)], linewidth=1.8, color="black")

    # Числовые подписи шкалы
    if show_numbers:
        labels = ["-2", "-1", "0", "+1", "+2"]
        for t, lab in zip(ticks, labels):
            ax.text(1.08*np.cos(t), 1.08*np.sin(t), lab, ha="center", va="center", fontsize=9)

    # Стрелка
    angle = (score + 2.0) / 4.0 * np.pi - np.pi
    ax.plot([0, 0.85*np.cos(angle)], [0, 0.85*np.sin(angle)], linewidth=4, color="black")
    ax.scatter([0], [0], s=30, color="black")

    # Подписи
    ax.text(0, 1.1, "Общая оценка", ha="center", va="bottom", fontsize=12, weight="bold")
    ax.text(-1.02, 0.05, "Активно\nпродавать", ha="left", va="center", fontsize=9)
    ax.text(-0.82, -0.55, "Продавать", ha="center", va="center", fontsize=10)
    ax.text(0.0, 0.05, "Нейтрально", ha="center", va="center", fontsize=10)
    ax.text(0.82, -0.55, "Покупать", ha="center", va="center", fontsize=10)
    ax.text(1.02, 0.05, "Активно\nпокупать", ha="right", va="center", fontsize=9)

    # Итоговая метка внизу
    label = "Нейтрально"
    if score > 1.0: label = "Активно покупать"
    elif score > 0.15: label = "Покупать"
    elif score < -1.0: label = "Активно продавать"
    elif score < -0.15: label = "Продавать"
    ax.text(0, -0.25, label, ha="center", va="center", fontsize=12, weight="bold")

    # Цифры по зонам
    ax.text(-0.85, -0.85, f"Продавать\n{sell}", ha="center", va="center", fontsize=10)
    ax.text(0, -0.95, f"Нейтрально\n{neutral}", ha="center", va="center", fontsize=10)
    ax.text(0.85, -0.85, f"Покупать\n{buy}", ha="center", va="center", fontsize=10)

    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig
