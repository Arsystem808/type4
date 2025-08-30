
# CapIntel — Signals MVP (Crypto & Equities) + Polygon + Dev Toggle

- Streamlit UI с карточкой идеи. JSON скрыт по умолчанию (переключатель **Режим разработчика**).
- FastAPI: `/signal`, `/price`, `/backtest`.
- Polygon.io: подтягивание последней цены для акций и крипты.

## Запуск
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export POLYGON_API_KEY=pk_************************
uvicorn api.main:app --reload
streamlit run app/app.py
```

## Gauge-индикатор
В UI добавлен полукруглый индикатор общей оценки. Шкала -2..+2 строится из действия и confidence.

- Динамические счётчики BUY/SELL/NEUTRAL сохраняются в session_state и отображаются на приборе.
- Кнопка **Скачать PNG** сохраняет изображение индикатора.
