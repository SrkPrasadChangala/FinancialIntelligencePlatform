import streamlit as st
import pandas as pd
from utils import get_stock_data, get_stock_info, format_number

def get_sentiment_emoji(change_percent):
    """Return appropriate emoji based on price change"""
    if change_percent >= 3:
        return "🚀"  # Strong bullish
    elif change_percent >= 1:
        return "😊"  # Bullish
    elif change_percent >= -1:
        return "😐"  # Neutral
    elif change_percent >= -3:
        return "😟"  # Bearish
    else:
        return "😱"  # Strong bearish

def get_volume_sentiment(current_volume, avg_volume):
    """Return volume activity emoji"""
    if current_volume >= avg_volume * 2:
        return "🔥"  # High activity
    elif current_volume >= avg_volume * 1.5:
        return "📈"  # Increased activity
    elif current_volume >= avg_volume * 0.5:
        return "➡️"  # Normal activity
    else:
        return "📉"  # Low activity

@st.cache_data(ttl=15)
def analyze_market_sentiment(symbols):
    """Analyze market sentiment for given symbols"""
    sentiment_data = []
    
    for symbol in symbols:
        try:
            info = get_stock_info(symbol)
            if info:
                data = get_stock_data(symbol, period='5d')
                if data is not None and not data.empty:
                    avg_volume = data['Volume'].mean()
                    current_volume = data['Volume'].iloc[-1]
                    
                    sentiment_data.append({
                        'symbol': symbol,
                        'name': info['name'],
                        'price': info['price'],
                        'change': info['change'],
                        'volume': current_volume,
                        'avg_volume': avg_volume,
                        'price_emoji': get_sentiment_emoji(info['change']),
                        'volume_emoji': get_volume_sentiment(current_volume, avg_volume)
                    })
        except Exception as e:
            st.warning(f"Error analyzing sentiment for {symbol}: {str(e)}")
            continue
    
    return pd.DataFrame(sentiment_data)

def render_sentiment_dashboard(symbols):
    """Render the sentiment dashboard"""
    st.subheader("Market Sentiment Dashboard")
    
    # Add auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    with col2:
        st.write("Auto-refresh")
        auto_refresh = st.toggle("Enable", value=True, key="sentiment_refresh")
    
    if auto_refresh:
        sentiment_df = analyze_market_sentiment(symbols)
        
        if not sentiment_df.empty:
            # Overall market mood
            positive_sentiment = (sentiment_df['change'] > 0).mean() * 100
            market_mood = "🐂" if positive_sentiment > 50 else "🐻"
            
            st.write(f"### Overall Market Mood: {market_mood}")
            st.progress(positive_sentiment / 100, text=f"{positive_sentiment:.1f}% Bullish")
            
            # Display sentiment cards
            st.write("### Individual Stock Sentiment")
            
            for idx, row in sentiment_df.iterrows():
                with st.container():
                    cols = st.columns([2, 2, 1, 1, 1])
                    with cols[0]:
                        st.write(f"**{row['symbol']}**")
                    with cols[1]:
                        st.write(format_number(row['price']))
                    with cols[2]:
                        st.write(f"{row['change']:+.2f}%")
                    with cols[3]:
                        st.write(f"{row['price_emoji']}")
                    with cols[4]:
                        st.write(f"{row['volume_emoji']}")
                    
                    st.divider()
        else:
            st.error("Unable to fetch sentiment data")
