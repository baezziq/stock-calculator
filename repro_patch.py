import yfinance as yf
from curl_cffi import requests

# Monkeypatch curl_cffi to disable SSL verification
original_request = requests.Session.request

def patched_request(self, method, url, *args, **kwargs):
    print(f"Patched request called for {url}")
    kwargs['verify'] = False
    return original_request(self, method, url, *args, **kwargs)

requests.Session.request = patched_request

print("Patched curl_cffi.requests.Session.request")

try:
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(period="1d")
    print(f"History Last Price: {hist['Close'].iloc[-1]}")
except Exception as e:
    print(f"History Error: {e}")
