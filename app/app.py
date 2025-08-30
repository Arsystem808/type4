
import sys, os, json
from dotenv import load_dotenv; load_dotenv()
# Import guard: ensure project root on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path: sys.path.insert(0, ROOT_DIR)

import streamlit as st
from capintel.signal_engine import build_signal
from capintel.backtest import toy_backtest
from capintel.visuals import render_sentiment_gauge
from capintel.providers.polygon_client import get_last_price, PolygonError

st.set_page_config(page_title="CapIntel — Signals", page_icon="📈", layout="wide")

st.title("📈 CapIntel — Идеи для Crypto & Equities (MVP)")
st.caption("Формат: BUY / SHORT / CLOSE / WAIT + уровни входа/целей/стопа, confidence и сценарии.")

go = False
dev_mode = False
show_gauge = True


with st.sidebar:
    st.header("Параметры")
    dev_mode = st.toggle("Режим разработчика", value=False, help="Показать JSON и отладочные блоки")
    show_gauge = st.toggle("Показывать индикатор", value=True)
    asset_class = st.selectbox("Класс актива", ["crypto", "equity"], index=0)
    horizon = st.selectbox("Горизонт", ["intraday", "swing", "position"], index=1)
    ticker = st.text_input("Тикер", value="BTCUSDT" if asset_class=="crypto" else "AAPL")
    last_price = st.number_input("Текущая цена", min_value=0.0001, value=65000.0 if asset_class=="crypto" else 230.0, step=0.1, format="%.4f")
    if st.button("Подтянуть цену из Polygon", use_container_width=True):
        try:
            fetched = get_last_price(asset_class, ticker)
            last_price = float(fetched)
            st.success(f"Цена обновлена: {last_price:.4f}")
        except PolygonError as e:
            st.error(str(e))
    st.write("---")
    st.markdown("**Источник цен:** Polygon (если задан ключ). Можно также ввести цену вручную.")

# Храним счётчики сигналов в сессии
if st.session_state.get('stats') is None:
    st.session_state['stats'] = {'buy': 0, 'sell': 0, 'neutral': 0, 'total': 0}
if st.button("Сбросить статистику", use_container_width=True):
    st.session_state['stats'] = {'buy': 0, 'sell': 0, 'neutral': 0, 'total': 0}
    go = st.button("Сгенерировать сигнал", use_container_width=True)

if go:
    sig = build_signal(ticker, asset_class, horizon, last_price)

    # Обновим статистику по действиям
    st.session_state['stats']['total'] += 1
    if sig.action == 'BUY':
        st.session_state['stats']['buy'] += 1
    elif sig.action == 'SHORT':
        st.session_state['stats']['sell'] += 1
    else:
        st.session_state['stats']['neutral'] += 1

    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.subheader(f"{sig.ticker} · {sig.asset_class.upper()} · {sig.horizon}")
        st.markdown(f"### ➤ Действие: **{sig.action}**")
        st.markdown(
            f"""
**Вход:** `{sig.entry}`  
**Цели:** `TP1 {sig.take_profit[0]}` · `TP2 {sig.take_profit[1]}`  
**Стоп:** `{sig.stop}`  
**Уверенность:** `{int(sig.confidence*100)}%`  
**Размер позиции:** `{sig.position_size_pct_nav}% NAV`  
"""
        )
        st.info(sig.narrative_ru)

        st.markdown("**Альтернативный план**")
        alt = sig.alternatives[0]
        st.markdown(f"- {alt.if_condition}: **{alt.action}** от `{alt.entry}` → TP1 `{alt.take_profit[0]}`, TP2 `{alt.take_profit[1]}`, стоп `{alt.stop}`")

        st.caption(f"Сигнал создан: {sig.created_at.strftime('%Y-%m-%d %H:%M UTC')} · Истекает: {sig.expires_at.strftime('%Y-%m-%d %H:%M UTC')}")
        st.caption(sig.disclaimer)

    with col2:
        # Индикатор «общая оценка»
        # Переведём действие+уверенность в шкалу [-2..+2]
        score = 0.0
        if sig.action == "BUY":
            score = min(2.0, max(0.0, (sig.confidence - 0.5) / 0.4 * 2.0))
        elif sig.action == "SHORT":
            score = -min(2.0, max(0.0, (sig.confidence - 0.5) / 0.4 * 2.0))
        if show_gauge:
            sell = st.session_state['stats']['sell']
            neutral = st.session_state['stats']['neutral']
            buy = st.session_state['stats']['buy']
            fig = render_sentiment_gauge(score, sell=sell, neutral=neutral, buy=buy)
            st.pyplot(fig, use_container_width=True)
            import io
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    
        if dev_mode:
            st.markdown("#### JSON")
            st.code(json.dumps(sig.as_dict(), default=str, ensure_ascii=False, indent=2), language="json")
        st.markdown("#### «Игрушечный» бэктест")
        if sig.action in ["BUY", "SHORT"]:
            res = toy_backtest(sig)
            st.metric("Симулированный PnL (после комиссий)", f"{res['pnl']*100:.2f}%")
            st.metric("Выход по цене", f"{res['exit_price']:.4f}")
            st.metric("Шагов до выхода", res["steps"])
        else:
            st.caption("Для WAIT/CLOSE сделок нет: бэктест не запускается.")

    st.divider()
    if dev_mode:
        st.caption("Отладка: внутренние фичи скрыты; наружу — только действия и уровни.")

else:
    st.markdown("> Выбери параметры слева и нажми **Сгенерировать сигнал**.")
