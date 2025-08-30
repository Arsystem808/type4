import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib import patheffects

# Цветовые опорные точки (слева→право): оранжевый → светло-жёлтый → бирюзовый → салатовый
STOPS = ["#FFA500", "#FFFACD", "#40E0D0", "#7CFC00"]
BOUNDS_DEG = np.linspace(-180, 0, 401)  # 400 тонких секторов для гладкого градиента

def _interp_color(t: float):
    """Линейная интерполяция цветов между опорными остановками."""
    t = np.clip(t, 0.0, 1.0)
    j = min(2, int(t * 3))
    f = t * 3 - j
    c0 = np.array(matplotlib.colors.to_rgb(STOPS[j]))
    c1 = np.array(matplotlib.colors.to_rgb(STOPS[j + 1]))
    c = (1 - f) * c0 + f * c1
    return c

def render_sentiment_gauge(score: float, theme_bg: str = "#0E1117"):
    """Полукруг [-2..+2], тёмная тема, градиент, сглаженные края, минимум текста."""
    score = float(np.clip(score, -2.0, 2.0))

    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=300)  # Retina-чётко
    fig.patch.set_facecolor(theme_bg)
    ax.set_facecolor(theme_bg)

    # Градиентная дуга
    for i in range(len(BOUNDS_DEG) - 1):
        t = i / (len(BOUNDS_DEG) - 2)
        color = _interp_color(t)
        ax.add_patch(Wedge((0, 0), 1.0, BOUNDS_DEG[i], BOUNDS_DEG[i + 1], width=0.18,
                           facecolor=color, edgecolor="none"))

    # Внешняя белая обводка
    theta = np.linspace(-np.pi, 0, 512)
    ax.plot(np.cos(theta), np.sin(theta), color="white", lw=2.2, alpha=0.95)

    # Стрелка
    angle = (score + 2.0) / 4.0 * np.pi - np.pi
    line, = ax.plot([0, 0.86 * np.cos(angle)], [0, 0.86 * np.sin(angle)],
                    color="white", lw=5, solid_capstyle="round", zorder=5)
    line.set_path_effects([patheffects.Stroke(linewidth=7, foreground="#000000", alpha=0.25),
                           patheffects.Normal()])
    ax.scatter([0], [0], s=30, c="white", zorder=6, edgecolors="#000000", linewidths=0.3)

    # Подписи (минимум)
    ax.text(0, 1.07, "Общая оценка", ha="center", va="bottom", color="white",
            fontsize=14, weight="bold")
    label = "Нейтрально"
    if score > 1.0:   label = "Активно покупать"
    elif score > 0.15:label = "Покупать"
    elif score < -1.0:label = "Активно продавать"
    elif score < -0.15:label = "Продавать"
    ax.text(0, -0.21, label, ha="center", va="center", color="white",
            fontsize=12, weight="bold")

    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig
