
from capintel.providers.polygon_client import _norm_crypto_pair
def test_norm():
    assert _norm_crypto_pair("BTCUSD")==("BTC","USD")
    assert _norm_crypto_pair("BTC/USDT")==("BTC","USDT")
    assert _norm_crypto_pair("ethusdt")==("ETH","USDT")
    assert _norm_crypto_pair("X:BTCUSD")==("BTC","USD")
