import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from utils import get_stock_data, format_number

def calculate_prediction(historical_data, days_to_predict=30):
    """Calculate linear regression prediction with confidence intervals"""
    # Prepare data for prediction
    df = historical_data.copy()
    df['Days'] = range(len(df))
    
    # Fit linear regression
    model = LinearRegression()
    X = df['Days'].values.reshape(-1, 1)
    y = df['Close'].values
    
    model.fit(X, y)
    
    # Generate future dates for prediction
    future_days = range(len(df), len(df) + days_to_predict)
    future_X = np.array(future_days).reshape(-1, 1)
    
    # Calculate prediction
    prediction = model.predict(future_X)
    
    # Calculate confidence intervals (95%)
    MSE = np.sum((y - model.predict(X)) ** 2) / (len(X) - 2)
    std_err = np.sqrt(MSE * (1 + 1/len(X) + (future_X - np.mean(X))**2 / np.sum((X - np.mean(X))**2)))
    confidence_interval = 1.96 * std_err
    
    return prediction, confidence_interval

def render_prediction(symbol):
    """Render stock prediction visualization"""
    st.subheader(f"Performance Prediction for {symbol}")
    
    # Get historical data
    hist_data = get_stock_data(symbol, period='6mo', interval='1d')
    if hist_data is None or hist_data.empty:
        st.error(f"No data available for {symbol}")
        return
    
    # Calculate predictions
    prediction, confidence = calculate_prediction(hist_data)
    
    # Create future dates
    last_date = hist_data.index[-1]
    future_dates = [last_date + timedelta(days=x) for x in range(1, len(prediction) + 1)]
    
    # Create visualization
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=hist_data.index,
        y=hist_data['Close'],
        name='Historical',
        line=dict(color='blue')
    ))
    
    # Prediction line
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=prediction,
        name='Prediction',
        line=dict(color='red', dash='dash')
    ))
    
    # Confidence intervals
    fig.add_trace(go.Scatter(
        x=future_dates + future_dates[::-1],
        y=np.concatenate([prediction + confidence, (prediction - confidence)[::-1]]),
        fill='toself',
        fillcolor='rgba(255,0,0,0.1)',
        line=dict(color='rgba(255,0,0,0)'),
        name='95% Confidence Interval'
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} Price Prediction (30 Days)',
        yaxis_title='Price',
        template='plotly_dark',
        height=600,
        showlegend=True,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    # Add prediction metrics
    current_price = hist_data['Close'].iloc[-1]
    predicted_price = prediction[-1]
    price_change = ((predicted_price - current_price) / current_price) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", format_number(current_price))
    with col2:
        st.metric("Predicted Price (30d)", format_number(predicted_price))
    with col3:
        st.metric("Predicted Change", f"{price_change:+.2f}%")
    
    # Display confidence range
    st.write(f"Prediction Range (95% Confidence):")
    st.write(f"Upper: {format_number(predicted_price + confidence[-1])}")
    st.write(f"Lower: {format_number(predicted_price - confidence[-1])}")
    
    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
    
    # Add disclaimer
    st.warning("""
    **Disclaimer:** This prediction is based on historical data and linear regression analysis. 
    It should not be used as the sole basis for investment decisions. Past performance does not 
    guarantee future results.
    """)
