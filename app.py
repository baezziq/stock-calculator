import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from curl_cffi import requests

# Monkeypatch curl_cffi to disable SSL verification (Fix for curl 77 error)
original_request = requests.Session.request

def patched_request(self, method, url, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, method, url, *args, **kwargs)

requests.Session.request = patched_request


# 2. Page Config
st.set_page_config(page_title="💰 Global Stock Calculator", layout="wide")

# 3. Sidebar (Inputs)
st.sidebar.title("Settings")

# Input 1: Stock Ticker Symbol
ticker_symbol = st.sidebar.text_input("Stock Ticker Symbol", value="AAPL").upper()

# Input 2: Buy Date
# Default buy date to 1 year ago for convenience
default_buy_date = datetime.now() - timedelta(days=365)
buy_date = st.sidebar.date_input("Buy Date", value=default_buy_date)

# Input 3: Sell Date
sell_date = st.sidebar.date_input("Sell Date", value=datetime.now())

# Button: Calculate Returns
calculate_btn = st.sidebar.button("Calculate Returns")

# 4. Main Area (Outputs)
st.title("💰 Global Stock Calculator(초댕이바보)")

def get_adjusted_close(ticker, date):
    """
    Fetches the Close price for a specific date.
    If data is missing (e.g., weekend/holiday), looks for the nearest previous trading day.
    """
    # Fetch data for a small window around the date to ensure we catch a trading day
    # We look back up to 7 days to find a valid trading day
    start_date = date - timedelta(days=7)
    end_date = date + timedelta(days=1) # yfinance end_date is exclusive
    
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        return None, None

    # Filter for data up to the specific date
    # Ensure index is datetime
    df.index = pd.to_datetime(df.index)
    mask = df.index <= pd.Timestamp(date)
    df_filtered = df.loc[mask]
    
    if df_filtered.empty:
        return None, None
        
    # Get the last available row (nearest previous trading day)
    last_row = df_filtered.iloc[-1]
    # Handle MultiIndex columns if present (yfinance update)
    if isinstance(last_row['Close'], pd.Series):
         price = last_row['Close'].iloc[0]
    else:
         price = last_row['Close']
         
    actual_date = df_filtered.index[-1]
    
    return float(price), actual_date

if calculate_btn:
    if not ticker_symbol:
        st.error("Please enter a valid stock ticker.")
    elif buy_date > sell_date:
        st.error("Buy Date cannot be after Sell Date.")
    else:
        with st.spinner(f"Fetching data for {ticker_symbol}..."):
            try:
                # Get Buy Price
                buy_price, actual_buy_date = get_adjusted_close(ticker_symbol, buy_date)
                
                # Get Sell Price
                sell_price, actual_sell_date = get_adjusted_close(ticker_symbol, sell_date)
                
                # Get Current Price
                ticker_data = yf.Ticker(ticker_symbol)
                # fast_info can sometimes cause 'currentTradingPeriod' error
                # Using history(period='1d') is more robust
                current_data = ticker_data.history(period='1d')
                
                if not current_data.empty:
                    current_price = current_data['Close'].iloc[-1]
                else:
                    current_price = None
                
                if buy_price is None:
                    st.error(f"Could not find data for {ticker_symbol} around {buy_date}.")
                elif sell_price is None:
                    st.error(f"Could not find data for {ticker_symbol} around {sell_date}.")
                elif current_price is None:
                     st.error(f"Could not fetch current price for {ticker_symbol}.")
                else:
                    # Calculation
                    # Profit/Loss % between Buy Date and Sell Date
                    total_return_pct = ((sell_price - buy_price) / buy_price) * 100
                    
                    # Profit/Loss % between Buy Date and Current Date
                    current_return_pct = ((current_price - buy_price) / buy_price) * 100
                    
                    # Annualized Return (CAGR)
                    days_held = (sell_date - buy_date).days
                    if days_held > 0:
                        cagr = (pow((sell_price / buy_price), (365 / days_held)) - 1) * 100
                    else:
                        cagr = 0.0 # Avoid division by zero for same day

                    # Display
                    st.markdown("### Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(label="Buy Price", value=f"${buy_price:,.2f}", delta=f"{actual_buy_date.strftime('%Y-%m-%d')}", delta_color="off")
                    
                    with col2:
                        st.metric(label="Sell Price", value=f"${sell_price:,.2f}", delta=f"{actual_sell_date.strftime('%Y-%m-%d')}", delta_color="off")
                        
                    with col3:
                        st.metric(label="Current Price", value=f"${current_price:,.2f}", delta="Latest")

                    st.divider()
                    
                    col4, col5, col6 = st.columns(3)
                    
                    with col4:
                        st.metric(label="Return (Sell vs Buy)", value=f"{total_return_pct:,.2f}%", delta=f"{total_return_pct:,.2f}%")
                        
                    with col5:
                        st.metric(label="Return (Current vs Buy)", value=f"{current_return_pct:,.2f}%", delta=f"{current_return_pct:,.2f}%")
                        
                    with col6:
                        st.metric(label="Annualized Return (CAGR)", value=f"{cagr:,.2f}%", delta=f"{cagr:,.2f}%")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                # For debugging
                # st.exception(e)
