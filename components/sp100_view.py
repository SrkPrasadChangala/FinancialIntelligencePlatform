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

@st.cache_data(ttl=15)  # Cache for 15 seconds for more frequent updates
def get_sp100_data(time_range='1d'):
    """Fetch S&P 100 data with specified time range"""
    data = []
    for symbol in SP100_SYMBOLS:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=time_range, interval='1m' if time_range == '1d' else '1d')
            if not hist.empty:
                info = get_stock_info(symbol)
                if info:
                    start_price = hist.iloc[0]['Close']
                    current_price = hist.iloc[-1]['Close']
                    price_change = ((current_price - start_price) / start_price) * 100
                    
                    data.append({
                        'symbol': symbol,
                        'name': info['name'],
                        'market_cap': info['market_cap'],
                        'price': info['price'],
                        'change': price_change,  # Use actual price change over selected period
                        'sector': info['sector'],
                        'volume': info['volume'],
                        'price_history': hist['Close'].tolist(),
                        'timestamp': hist.index.tolist()
                    })
        except Exception as e:
            st.warning(f"Error fetching data for {symbol}: {str(e)}")
            continue
    return pd.DataFrame(data)

def render_sp100_view():
    st.subheader("S&P 100 Market Cap Visualization")
    
    # Data source attribution
    st.info("""
    Real-time visualization of top 20 S&P 100 companies by market capitalization.
    Data provided by Yahoo Finance (yfinance). Updates every 15 seconds.
    Click on a company for detailed view.
    """)
    
    # Time range selector
    col1, col2 = st.columns([3, 1])
    with col1:
        time_range = st.select_slider(
            "Select Time Range",
            options=['1d', '5d', '1mo', '3mo', '6mo', '1y'],
            value='1d',
            help="Choose the time period for market cap changes"
        )
    with col2:
        st.write("Auto-refresh")
        auto_refresh = st.toggle("Enable", value=True)
    
    # Get market data with auto-refresh
    if auto_refresh:
        df = st.empty()
        df = get_sp100_data(time_range)
    
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

    # Identify significant changes (top/bottom 20%)
    df['significant'] = pd.qcut(df['change'], q=5, labels=['Strong Sell', 'Sell', 'Neutral', 'Buy', 'Strong Buy'])
    
    # Create treemap with enhanced visual cues
    fig = go.Figure(go.Treemap(
        labels=df['symbol'],
        parents=[''] * len(df),
        values=df['market_cap'],
        textinfo='label',
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text,
        marker=dict(
            colors=df['change'],
            colorscale=[
                [0, 'rgb(165,0,38)'],      # Strong negative
                [0.2, 'rgb(215,48,39)'],    # Negative
                [0.4, 'rgb(244,109,67)'],   # Slight negative
                [0.5, 'rgb(255,255,191)'],  # Neutral
                [0.6, 'rgb(116,173,209)'],  # Slight positive
                [0.8, 'rgb(49,130,189)'],   # Positive
                [1, 'rgb(0,104,55)']        # Strong positive
            ],
            showscale=True,
            colorbar=dict(
                title="% Change",
                thickness=10,
                tickformat='.1f',
                ticksuffix='%'
            )
        ),
        pathbar=dict(visible=False)
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
