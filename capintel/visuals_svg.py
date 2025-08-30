
import math
STOPS = ["#FFA500", "#FFFACD", "#40E0D0", "#7CFC00"]
def _arc_path(cx, cy, r, start_deg, end_deg):
    s, e = math.radians(start_deg), math.radians(end_deg)
    x1, y1 = cx + r*math.cos(s), cy + r*math.sin(s)
    x2, y2 = cx + r*math.cos(e), cy + r*math.sin(e)
    large_arc = 1 if abs(end_deg - start_deg) > 180 else 0
    return f"M {x1:.2f},{y1:.2f} A {r:.2f},{r:.2f} 0 {large_arc} 1 {x2:.2f},{y2:.2f}"
def render_gauge_svg(score: float, prev_score: float = None, width: int = 760, dark_bg: str = "#0E1117", animate: bool = True, duration_ms: int = 900) -> str:
    score = max(-2.0, min(2.0, float(score)))
    if prev_score is None:
        animate = False; prev_score = score
    else:
        prev_score = max(-2.0, min(2.0, float(prev_score)))
    W, H = width, int(width * 0.52); cx, cy, R = W/2, H*0.92, W*0.40
    def to_angle(s): return -180 + 180 * (s + 2.0) / 4.0
    start_ang = to_angle(prev_score); end_ang = to_angle(score)
    status = "Нейтрально"
    if score > 1.0: status = "Активно покупать"
    elif score > 0.15: status = "Покупать"
    elif score < -1.0: status = "Активно продавать"
    elif score < -0.15: status = "Продавать"
    ticks = [(-180, "−2"), (-135, "−1"), (-90, "0"), (-45, "+1"), (0, "+2")]
    tick_lines = []; tick_texts = []
    for a, lab in ticks:
        ax1, ay1 = cx + (R-8)*math.cos(math.radians(a)), cy + (R-8)*math.sin(math.radians(a))
        ax2, ay2 = cx + (R)*math.cos(math.radians(a)),  cy + (R)*math.sin(math.radians(a))
        tx, ty   = cx + (R+18)*math.cos(math.radians(a)), cy + (R+18)*math.sin(math.radians(a))
        tick_lines.append(f'<line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}" stroke="#FFFFFF" stroke-width="2" />')
        tick_texts.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" class="t tick">{lab}</text>')
    grad = f'''
    <defs>
      <linearGradient id="grad" x1="0%" y1="100%" x2="100%" y2="100%">
        <stop offset="0%"   stop-color="{STOPS[0]}"/>
        <stop offset="33%"  stop-color="{STOPS[1]}"/>
        <stop offset="66%"  stop-color="{STOPS[2]}"/>
        <stop offset="100%" stop-color="{STOPS[3]}"/>
      </linearGradient>
      <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#000000" flood-opacity="0.5"/>
      </filter>
    </defs>
    '''
    arc = _arc_path(cx, cy, R, -180, 0); needle_len = R - 6
    needle = f'''
    <g id="needle" transform="rotate({start_ang:.2f} {cx:.1f} {cy:.1f})" filter="url(#shadow)">
      <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + needle_len:.1f}" y2="{cy:.1f}" stroke="#FFFFFF" stroke-width="{int(W*0.015)}" stroke-linecap="round"/>
      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{int(W*0.012)}" fill="#FFFFFF" />
      {f'<animateTransform attributeName="transform" attributeType="XML" type="rotate" from="{start_ang:.2f} {cx:.1f} {cy:.1f}" to="{end_ang:.2f} {cx:.1f} {cy:.1f}" dur="{duration_ms}ms" fill="freeze"/>' if animate else ''}
    </g>
    '''
    svg = f"""<div style="width:{W}px;margin:0 auto;">
<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" style="background:{dark_bg}; border-radius:12px">
  <style>
    .t {{ fill:#FFFFFF; font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
    .h1 {{ font-weight:700; font-size:{int(W*0.045)}px; }}
    .h2 {{ font-weight:700; font-size:{int(W*0.035)}px; }}
    .tick {{ fill:#FFFFFF; opacity:0.85; font-size:{int(W*0.03)}px; }}
  </style>
  {grad}
  <text x="{cx}" y="{H*0.10}" text-anchor="middle" class="t h1">Общая оценка</text>
  <path d="{_arc_path(cx, cy, R, -180, 0)}" stroke="url(#grad)" stroke-width="{int(W*0.04)}" stroke-linecap="round" fill="none"/>
  <path d="{_arc_path(cx, cy, R+2, -180, 0)}" stroke="#FFFFFF" stroke-opacity="0.85" stroke-width="2" fill="none"/>
  {''.join(tick_lines)}
  {''.join(tick_texts)}
  {needle}
  <text x="{cx}" y="{H*0.90}" text-anchor="middle" class="t h2">{status}</text>
</svg>
</div>
"""
    return svg
