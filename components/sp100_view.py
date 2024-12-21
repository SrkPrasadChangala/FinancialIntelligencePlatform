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
                'change': info['change'],
                'sector': info['sector'],
                'volume': info['volume']
            })
    return pd.DataFrame(data)

def render_sp100_view():
    st.subheader("S&P 100 Market Cap Visualization")
    st.info("Real-time visualization of top 20 S&P 100 companies by market capitalization. Click on a company for detailed view.")
    
    # Get market data
    df = get_sp100_data()
    
    # Add company selector for detailed view
    selected_symbol = st.selectbox(
        "Select company for detailed view",
        options=df['symbol'].tolist(),
        format_func=lambda x: f"{x} - {df[df['symbol'] == x]['name'].iloc[0]}"
    )
    
    if df.empty:
        st.error("Unable to fetch market data. Please try again later.")
        return
    
    # Sort by market cap
    df = df.sort_values('market_cap', ascending=True)
    
    # Create interactive treemap
    # Create hover text with detailed information
    hover_text = [
        f"<b>{symbol}</b> ({name})<br>" +
        f"Market Cap: {format_number(cap)}<br>" +
        f"Price: ${price:.2f}<br>" +
        f"Change: {change:+.2f}%<br>" +
        f"Sector: {sector}<br>" +
        f"Volume: {format_number(vol)}"
        for symbol, name, cap, price, change, sector, vol
        in zip(df['symbol'], df['name'], df['market_cap'], 
               df['price'], df['change'], df['sector'], df['volume'])
    ]

    fig = go.Figure(go.Treemap(
        labels=df['symbol'],
        parents=[''] * len(df),
        values=df['market_cap'],
        textinfo='label',
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text,
        marker=dict(
            colors=df['change'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(
                title="% Change",
                thickness=10
            )
        )
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
    
    # Show detailed view for selected company
    if selected_symbol:
        st.divider()
        st.subheader(f"Detailed View: {selected_symbol}")
        
        col1, col2, col3 = st.columns(3)
        company_data = df[df['symbol'] == selected_symbol].iloc[0]
        
        with col1:
            st.metric("Price", company_data['price_fmt'])
        with col2:
            st.metric("Market Cap", company_data['market_cap_fmt'])
        with col3:
            st.metric("24h Change", company_data['change_fmt'])
            
        # Show stock chart for selected company
        from components.charts import render_stock_chart
        st.subheader("Price History")
        render_stock_chart(selected_symbol, period='1d', interval='5m')
