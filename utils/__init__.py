import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

@st.cache_data(ttl=60)
def get_stock_data(symbol, period='1d', interval='1m'):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'price': info.get('currentPrice', 0),
            'change': info.get('regularMarketChangePercent', 0),
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0)
        }
    except:
        return None

def format_number(number):
    try:
        number = float(number) if hasattr(number, 'dtype') else number
        return next(fmt for val, fmt in [
            (1e9, f"${number/1e9:.2f}B"),
            (1e6, f"${number/1e6:.2f}M"),
            (0, f"${number:,.2f}")
        ] if number >= val)
    except (TypeError, ValueError):
        return "$0.00"  # Fallback for invalid numbers

def calculate_portfolio_value(holdings):
    total_value = 0
    for holding in holdings:
        current_price = get_stock_data(holding['symbol']).iloc[-1]['Close']
        total_value += current_price * holding['quantity']
    return total_value

def format_change(change):
    color = "green" if change >= 0 else "red"
    return f"<span style='color: {color}'>{change:+.2f}%</span>"

from .company_matcher import CompanyMatcher
