# capintel/visuals_svg.py
import math

# Градиент: оранжевый → светло-жёлтый → бирюза → салатовый
STOPS = ["#FFA500", "#FFFACD", "#40E0D0", "#7CFC00"]

def _arc_path(cx, cy, r, start_deg, end_deg):
    s, e = math.radians(start_deg), math.radians(end_deg)
    x1, y1 = cx + r*math.cos(s), cy + r*math.sin(s)
    x2, y2 = cx + r*math.cos(e), cy + r*math.sin(e)
    large_arc = 1 if abs(end_deg - start_deg) > 180 else 0
    return f"M {x1:.2f},{y1:.2f} A {r:.2f},{r:.2f} 0 {large_arc} 1 {x2:.2f},{y2:.2f}"

def render_gauge_svg(
    score: float,
    prev_score: float = None,
    max_width: int = 660,            # максимум; в контейнере будет width:100%
    dark_bg: str = "#0E1117",
    animate: bool = True,
    duration_ms: int = 900,
) -> str:
    # clamp
    score = max(-2.0, min(2.0, float(score)))
    if prev_score is None:
        animate = False
        prev_score = score
    else:
        prev_score = max(-2.0, min(2.0, float(prev_score)))

    # Геометрия: больше воздуха сверху, дугу чуть ниже
    W = max_width
    H = int(W * 0.60)
    cx, cy, R = W/2, H*0.84, W*0.42

    def to_angle(s: float) -> float:
        return -180 + 180 * (s + 2.0) / 4.0

    start_ang = to_angle(prev_score)
    end_ang   = to_angle(score)

    # Подпись статуса
    status = "Нейтрально"
    if score > 1.0:   status = "Активно покупать"
    elif score > 0.15:status = "Покупать"
    elif score < -1.0:status = "Активно продавать"
    elif score < -0.15:status = "Продавать"

    # Засечки и числа — БЕЗ метки «0», чтобы не пересекаться с заголовком
    ticks = [(-180, "−2"), (-135, "−1"), (-45, "+1"), (0, "+2")]
    tick_lines, tick_texts = [], []
    tick_r_in, tick_r_out, tick_r_txt = R - 10, R + 4, R + 42  # числа дальше от дуги

    for a, lab in ticks:
        ax1, ay1 = cx + tick_r_in * math.cos(math.radians(a)), cy + tick_r_in * math.sin(math.radians(a))
        ax2, ay2 = cx + tick_r_out* math.cos(math.radians(a)), cy + tick_r_out* math.sin(math.radians(a))
        tx,  ty  = cx + tick_r_txt* math.cos(math.radians(a)), cy + tick_r_txt* math.sin(math.radians(a))
        tick_lines.append(
            f'<line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}" stroke="#FFFFFF" stroke-opacity="0.9" stroke-width="1.6" />'
        )
        tick_texts.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" class="t tick halo">{lab}</text>'
        )

    # Размеры шрифтов
    fs_title  = int(W * 0.050)   # заголовок
    fs_status = int(W * 0.038)   # статус
    fs_tick   = int(W * 0.030)   # цифры

    # Градиент + halo (ореол) для читаемости текста
    svg_defs = f"""
    <defs>
      <linearGradient id="grad" x1="0%" y1="100%" x2="100%" y2="100%">
        <stop offset="0%"   stop-color="{STOPS[0]}"/>
        <stop offset="33%"  stop-color="{STOPS[1]}"/>
        <stop offset="66%"  stop-color="{STOPS[2]}"/>
        <stop offset="100%" stop-color="{STOPS[3]}"/>
      </linearGradient>
      <filter id="halo" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="0" stdDeviation="2.6" flood-color="#000000" flood-opacity="0.55"/>
      </filter>
    </defs>
    """

    arc      = _arc_path(cx, cy, R,   -180, 0)
    outline  = _arc_path(cx, cy, R+2, -180, 0)
    needle_len = R - 8
    needle = f"""
    <g transform="rotate({start_ang:.2f} {cx:.1f} {cy:.1f})">
      <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + needle_len:.1f}" y2="{cy:.1f}"
            stroke="#FFFFFF" stroke-width="{int(W*0.015)}" stroke-linecap="round" />
      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{int(W*0.012)}" fill="#FFFFFF"/>
      {f'<animateTransform attributeName="transform" attributeType="XML" type="rotate" from="{start_ang:.2f} {cx:.1f} {cy:.1f}" to="{end_ang:.2f} {cx:.1f} {cy:.1f}" dur="{duration_ms}ms" fill="freeze"/>' if animate else ''}
    </g>
    """

    # Координаты текста
    title_y  = H * 0.12
    status_y = H * 0.95

    # Адаптивный SVG: width:100%, не обрезается
    return f"""
<div style="max-width:{W}px;width:100%;margin:0 auto;">
  <svg viewBox="0 0 {W} {H}" width="100%" height="auto" preserveAspectRatio="xMidYMid meet"
       xmlns="http://www.w3.org/2000/svg" style="background:{dark_bg}; border-radius:12px">
    <style>
      .t {{ fill:#FFFFFF; font-family:-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
      .h1 {{ font-weight:700; font-size:{fs_title}px; letter-spacing:0.3px; }}
      .h2 {{ font-weight:700; font-size:{fs_status}px; }}
      .tick {{ opacity:0.98; font-size:{fs_tick}px; }}
      .halo {{ filter:url(#halo); }}
    </style>
    {svg_defs}

    <!-- Дуга и обводка -->
    <path d="{arc}"     stroke="url(#grad)" stroke-width="{int(W*0.042)}" stroke-linecap="round" fill="none"/>
    <path d="{outline}" stroke="#FFFFFF"    stroke-opacity="0.92" stroke-width="2" fill="none"/>

    <!-- Засечки и числа -->
    {''.join(tick_lines)}
    {''.join(tick_texts)}

    <!-- Стрелка -->
    {needle}

    <!-- Заголовок и статус (поверх всего) -->
    <text x="{W/2}" y="{title_y}"  text-anchor="middle" class="t h1 halo">Общая оценка</text>
    <text x="{W/2}" y="{status_y}" text-anchor="middle" class="t h2 halo">{status}</text>
  </svg>
</div>
"""
