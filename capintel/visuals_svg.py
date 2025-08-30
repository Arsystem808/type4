# capintel/visuals_svg.py
import math

# цвета слева → вправо
COLORS = ["#FFA500", "#FFFACD", "#40E0D0", "#7CFC00"]  # оранж, светло-жёлт, бирюз, салат
LABEL = {
    "very_neg": "Активно продавать",
    "neg": "Продавать",
    "neu": "Нейтрально",
    "pos": "Покупать",
    "very_pos": "Активно покупать",
}

def _arc_path(cx, cy, r, start_deg, end_deg):
    """SVG path для дуги (полукруга) со скруглёнными краями."""
    s, e = math.radians(start_deg), math.radians(end_deg)
    x1, y1 = cx + r*math.cos(s), cy + r*math.sin(s)
    x2, y2 = cx + r*math.cos(e), cy + r*math.sin(e)
    large_arc = 1 if (end_deg - start_deg) % 360 > 180 else 0
    # sweep=1 — по часовой, у нас слева(-180) → вправо(0)
    return f"M {x1:.2f},{y1:.2f} A {r:.2f},{r:.2f} 0 {large_arc} 1 {x2:.2f},{y2:.2f}"

def render_gauge_svg(score: float, width: int = 640, dark_bg: str = "#0E1117") -> str:
    """
    Возвращает HTML со встроенным SVG-прибором.
    score в диапазоне [-2..+2]; 0 — нейтрально.
    """
    score = max(-2.0, min(2.0, float(score)))
    # Геометрия
    W, H = width, int(width * 0.52)
    cx, cy, R = W/2, H*0.92, W*0.40
    # Угол стрелки: -180..0
    angle = -180 + 180 * (score + 2.0) / 4.0
    ax, ay = cx + (R-6) * math.cos(math.radians(angle)), cy + (R-6) * math.sin(math.radians(angle))

    # Текст статуса
    status = "Нейтрально"
    if score > 1.0:   status = LABEL["very_pos"]
    elif score > 0.15:status = LABEL["pos"]
    elif score < -1.0:status = LABEL["very_neg"]
    elif score < -0.15:status = LABEL["neg"]

    # Четыре цветных сегмента
    segs = [
        (-180, -135, COLORS[0]),
        (-135,  -90, COLORS[1]),
        ( -90,  -45, COLORS[2]),
        ( -45,    0, COLORS[3]),
    ]

    # Шкала
    ticks = [(-180, "−2"), (-135, "−1"), (-90, "0"), (-45, "+1"), (0, "+2")]

    svg = f"""
<div style="width:{W}px;margin:0 auto;">
<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     xmlns="http://www.w3.org/2000/svg" style="background:{dark_bg}; border-radius:12px">
  <style>
    .t {{ fill:#FFFFFF; font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
    .h1 {{ font-weight:700; font-size:{int(W*0.045)}px; }}
    .h2 {{ font-weight:700; font-size:{int(W*0.035)}px; }}
    .tick {{ fill:#FFFFFF; opacity:0.85; font-size:{int(W*0.03)}px; }}
  </style>

  <!-- Заголовок -->
  <text x="{cx}" y="{H*0.08}" text-anchor="middle" class="t h1">Общая оценка</text>

  <!-- Сегменты дуги -->
  {"".join([f'<path d="{_arc_path(cx, cy, R, a0, a1)}" stroke="{c}" stroke-width="{int(W*0.04)}" stroke-linecap="round" fill="none"/>' for a0,a1,c in segs])}

  <!-- Внешняя тонкая обводка -->
  <path d="{_arc_path(cx, cy, R+2, -180, 0)}" stroke="#FFFFFF" stroke-opacity="0.85" stroke-width="2" fill="none"/>

  <!-- Засечки и числа -->
  {"".join([f'<line x1="{cx+(R-8)*math.cos(math.radians(a)):.1f}" y1="{cy+(R-8)*math.sin(math.radians(a)):.1f}" x2="{cx+R*math.cos(math.radians(a)):.1f}" y2="{cy+R*math.sin(math.radians(a)):.1f}" stroke="#FFFFFF" stroke-width="2" />' for a,_ in ticks])}
  {"".join([f'<text x="{cx+ (R+18)*math.cos(math.radians(a)):.1f}" y="{cy+ (R+18)*math.sin(math.radians(a)):.1f}" text-anchor="middle" dominant-baseline="middle" class="t tick">{lab}</text>' for a,lab in ticks])}

  <!-- Стрелка -->
  <line x1="{cx}" y1="{cy}" x2="{ax:.1f}" y2="{ay:.1f}" stroke="#FFFFFF" stroke-width="{int(W*0.015)}" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="{int(W*0.012)}" fill="#FFFFFF"/>

  <!-- Подпись статуса -->
  <text x="{cx}" y="{H*0.90}" text-anchor="middle" class="t h2">{status}</text>
</svg>
</div>
"""
    return svg
