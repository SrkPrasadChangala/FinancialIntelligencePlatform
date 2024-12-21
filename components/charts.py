import streamlit as st
import plotly.graph_objects as go
from utils import get_stock_data

def render_stock_chart(symbol, period='1d', interval='1m'):
    data = get_stock_data(symbol, period, interval)
    if data is None or data.empty:
        st.error(f"No data available for {symbol}")
        return

    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                        open=data['Open'],
                                        high=data['High'],
                                        low=data['Low'],
                                        close=data['Close'])])

    fig.update_layout(
        title=f'{symbol} Stock Price',
        yaxis_title='Price',
        template='plotly_dark',
        height=500,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Volume chart
    volume_fig = go.Figure(data=[go.Bar(x=data.index, y=data['Volume'])])
    volume_fig.update_layout(
        title='Trading Volume',
        yaxis_title='Volume',
        template='plotly_dark',
        height=200,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(volume_fig, use_container_width=True)
