import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from utils import format_number, get_stock_info

# S&P 100 companies (top 20 for MVP)
SP100_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
    'NVDA', 'BRK-B', 'LLY', 'V', 'UNH',
    'JPM', 'XOM', 'MA', 'JNJ', 'PG',
    'HD', 'AVGO', 'CVX', 'MRK', 'KO'
]

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_sp100_data():
    data = []
    for symbol in SP100_SYMBOLS:
        info = get_stock_info(symbol)
        if info:
            data.append({
                'symbol': symbol,
                'name': info['name'],
                'market_cap': info['market_cap'],
                'price': info['price'],
                'change': info['change']
            })
    return pd.DataFrame(data)

def render_sp100_view():
    st.subheader("S&P 100 Market Cap Visualization")
    st.info("Real-time visualization of top 20 S&P 100 companies by market capitalization")
    
    # Get market data
    df = get_sp100_data()
    
    if df.empty:
        st.error("Unable to fetch market data. Please try again later.")
        return
    
    # Sort by market cap
    df = df.sort_values('market_cap', ascending=True)
    
    # Create interactive treemap
    fig = go.Figure(go.Treemap(
        labels=df['symbol'],
        parents=[''] * len(df),
        values=df['market_cap'],
        textinfo='label+value',
        hovertemplate='<b>%{label}</b><br>Market Cap: %{value:$.2f}B<br>Price: $%{customdata[0]:.2f}<br>Change: %{customdata[1]:.2f}%',
        customdata=df[['price', 'change']].values
    ))
    
    fig.update_layout(
        title='Market Capitalization Treemap',
        width=800,
        height=600,
        template='plotly_dark'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show tabular data
    st.subheader("Market Details")
    
    # Format market cap for display
    df['market_cap_fmt'] = df['market_cap'].apply(lambda x: format_number(x))
    df['price_fmt'] = df['price'].apply(lambda x: f"${x:.2f}")
    df['change_fmt'] = df['change'].apply(lambda x: f"{x:+.2f}%")
    
    # Display table
    st.dataframe(
        df[['symbol', 'name', 'market_cap_fmt', 'price_fmt', 'change_fmt']]
        .rename(columns={
            'symbol': 'Symbol',
            'name': 'Name',
            'market_cap_fmt': 'Market Cap',
            'price_fmt': 'Price',
            'change_fmt': 'Change'
        }),
        hide_index=True
    )
