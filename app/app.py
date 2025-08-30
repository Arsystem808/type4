
import sys, os, json
from dotenv import load_dotenv; load_dotenv()
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path: sys.path.insert(0, ROOT_DIR)
import streamlit as st
from streamlit.components.v1 import html as st_html
from capintel.signal_engine import build_signal
from capintel.backtest import toy_backtest
from capintel.providers.polygon_client import get_last_price, PolygonError
from capintel.visuals_svg import render_gauge_svg
st.set_page_config(page_title="CapIntel — Signals", page_icon="📈", layout="wide")
st.title("📈 CapIntel — Идеи для Crypto & Equities (MVP)")
st.caption("Формат: BUY / SHORT / CLOSE / WAIT + уровни входа/целей/стопа, confidence и сценарии.")
go=False; dev_mode=False; show_gauge=True
with st.sidebar:
    st.header("Параметры")
    dev_mode = st.toggle("Режим разработчика", value=False, help="Показать JSON и отладку")
    show_gauge = st.toggle("Показывать индикатор", value=True)
    asset_class = st.selectbox("Класс актива", ["crypto","equity"], index=0)
    horizon = st.selectbox("Горизонт", ["intraday","swing","position"], index=1)
    ticker = st.text_input("Тикер", value="BTCUSDT" if asset_class=="crypto" else "AAPL")
    if "last_price" not in st.session_state: st.session_state["last_price"] = 65000.0 if asset_class=="crypto" else 230.0
    colA, colB = st.columns(2)
    with colA:
        if st.button("Обновить цену из Polygon", use_container_width=True):
            try:
                st.session_state["last_price"] = float(get_last_price(asset_class, ticker))
                st.success(f"Цена: {st.session_state['last_price']:.4f}")
            except PolygonError as e:
                st.error(str(e))
    with colB:
        st.metric("Цена (Polygon)", f"{st.session_state['last_price']:.4f}")
    st.write("---")
    if "stats" not in st.session_state: st.session_state["stats"] = {"buy":0,"sell":0,"neutral":0,"total":0}
    if st.button("Сбросить статистику", use_container_width=True): st.session_state["stats"] = {"buy":0,"sell":0,"neutral":0,"total":0}
    go = st.button("Сгенерировать сигнал", type="primary", use_container_width=True)
if go:
    price = st.session_state["last_price"]
    try: price = float(get_last_price(asset_class, ticker)); st.session_state["last_price"] = price
    except Exception: pass
    sig = build_signal(ticker, asset_class, horizon, price)
    st.session_state["stats"]["total"] += 1
    if sig.action == "BUY": st.session_state["stats"]["buy"] += 1
    elif sig.action == "SHORT": st.session_state["stats"]["sell"] += 1
    else: st.session_state["stats"]["neutral"] += 1
    col1, col2 = st.columns([1.05,1.0])
    with col1:
        st.subheader(f"{sig.ticker} · {sig.asset_class.upper()} · {sig.horizon}")
        st.markdown(f"### ➤ Действие: **{sig.action}**")
        st.markdown(f"**Вход:** `{sig.entry}`  \n**Цели:** `TP1 {sig.take_profit[0]}` · `TP2 {sig.take_profit[1]}`  \n**Стоп:** `{sig.stop}`  \n**Уверенность:** `{int(sig.confidence*100)}%`  \n**Размер позиции:** `{sig.position_size_pct_nav}% NAV`  ")
        st.info(sig.narrative_ru)
        alt = sig.alternatives[0]
        st.markdown("**Альтернативный план**")
        st.markdown(f"- {alt.if_condition}: **{alt.action}** от `{alt.entry}` → TP1 `{alt.take_profit[0]}`, TP2 `{alt.take_profit[1]}`, стоп `{alt.stop}`")
        st.caption(f"Сигнал создан: {sig.created_at.strftime('%Y-%m-%d %H:%M UTC')} · Истекает: {sig.expires_at.strftime('%Y-%m-%d %H:%M UTC')}"); st.caption(sig.disclaimer)
    with col2:
        score = 0.0
        if sig.action == "BUY":   score = min(2.0, max(0.0, (sig.confidence - 0.5) / 0.4 * 2.0))
        elif sig.action == "SHORT": score = -min(2.0, max(0.0, (sig.confidence - 0.5) / 0.4 * 2.0))
        if show_gauge:
            prev = st.session_state.get("prev_score")
            svg = render_gauge_svg(score, prev_score=prev, width=760, animate=True, duration_ms=900)
            st_html(svg, height=400)
            st.session_state["prev_score"] = score
        if dev_mode:
            st.markdown("#### JSON"); st.code(json.dumps(sig.dict(), default=str, ensure_ascii=False, indent=2), language="json")
        st.markdown("#### «Игрушечный» бэктест")
        if sig.action in ["BUY","SHORT"]:
            res = toy_backtest(sig); st.metric("Симулированный PnL (после комиссий)", f"{res['pnl']*100:.2f}%"); st.metric("Выход по цене", f"{res['exit_price']:.4f}"); st.metric("Шагов до выхода", res["steps"])
        else: st.caption("Для WAIT/CLOSE сделок нет: бэктест не запускается.")
else:
    st.markdown("> Выбери параметры слева и нажми **Сгенерировать сигнал**.")
