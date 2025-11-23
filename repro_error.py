import yfinance as yf

try:
    ticker = yf.Ticker("AAPL")
    print(f"Fast Info Last Price: {ticker.fast_info.last_price}")
except Exception as e:
    print(f"Fast Info Error: {e}")

try:
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(period="1d")
    print(f"History Last Price: {hist['Close'].iloc[-1]}")
except Exception as e:
    print(f"History Error: {e}")
