
import os
from dotenv import load_dotenv; load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from capintel.signal_engine import build_signal
from capintel.schemas import Signal, AssetClass, Horizon
from capintel.backtest import toy_backtest
from capintel.providers.polygon_client import get_last_price, PolygonError

app = FastAPI(title="CapIntel Signals API", version="0.2.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class SignalRequest(BaseModel):
    ticker: str
    asset_class: AssetClass
    horizon: Horizon
    last_price: float

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/price")
def price(asset_class: AssetClass, ticker: str):
    try:
        return {"ticker": ticker.upper(), "asset_class": asset_class, "last_price": get_last_price(asset_class, ticker)}
    except PolygonError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/signal", response_model=Signal)
def signal(req: SignalRequest):
    return build_signal(req.ticker, req.asset_class, req.horizon, req.last_price)

@app.post("/backtest")
def backtest(sig: Signal):
    return toy_backtest(sig)
