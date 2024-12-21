import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_stock_data, get_stock_info, format_number
from utils.sentiment_analyzer import SentimentAnalyzer


def get_sentiment_emoji(sentiment_score):
    """Return appropriate emoji based on sentiment score"""
    if sentiment_score >= 0.6:
        return "🚀"  # Strong bullish
    elif sentiment_score >= 0.2:
        return "😊"  # Bullish
    elif sentiment_score >= -0.2:
        return "😐"  # Neutral
    elif sentiment_score >= -0.6:
        return "😟"  # Bearish
    else:
        return "😱"  # Strong bearish


def get_sentiment_color(sentiment_score):
    """Return color based on sentiment score"""
    if sentiment_score >= 0.6:
        return "rgb(0,255,0)"  # Strong positive
    elif sentiment_score >= 0.2:
        return "rgb(144,238,144)"  # Positive
    elif sentiment_score >= -0.2:
        return "rgb(255,255,191)"  # Neutral
    elif sentiment_score >= -0.6:
        return "rgb(255,160,122)"  # Negative
    else:
        return "rgb(255,0,0)"  # Strong negative


def create_gauge_chart(value, title):
    """Create a gauge chart for sentiment visualization"""
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=(value + 1) * 50,  # Convert from [-1,1] to [0,100]
            title={'text': title},
            gauge={
                'axis': {
                    'range': [0, 100]
                },
                'bar': {
                    'color': get_sentiment_color(value)
                },
                'steps': [{
                    'range': [0, 20],
                    'color': "rgb(255,0,0)"
                }, {
                    'range': [20, 40],
                    'color': "rgb(255,160,122)"
                }, {
                    'range': [40, 60],
                    'color': "rgb(255,255,191)"
                }, {
                    'range': [60, 80],
                    'color': "rgb(144,238,144)"
                }, {
                    'range': [80, 100],
                    'color': "rgb(0,255,0)"
                }],
            }))


@st.cache_data(ttl=300)  # Cache for 5 minutes
def analyze_market_sentiment(symbols):
    """Analyze market sentiment for given symbols"""
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_data = []

    for symbol in symbols:
        try:
            info = get_stock_info(symbol)
            if info:
                try:
                    data = get_stock_data(symbol, period='5d')
                    if data is not None and not data.empty:
                        # Get multi-source sentiment
                        sentiment = sentiment_analyzer.get_composite_sentiment(
                            symbol)

                        sentiment_data.append({
                            'symbol':
                            symbol,
                            'name':
                            info['name'],
                            'price':
                            info['price'],
                            'change':
                            info['change'],
                            'composite_sentiment':
                            sentiment['composite'],
                            'news_sentiment':
                            sentiment['news'],
                            'analyst_sentiment':
                            sentiment['analyst'],
                            'sentiment_emoji':
                            get_sentiment_emoji(sentiment['composite']),
                            'analyst_data':
                            sentiment['analyst_data']
                        })
                except Exception as e:
                    st.warning(f"Error processing data for {symbol}: {str(e)}")
        except Exception as e:
            st.warning(f"Error analyzing sentiment for {symbol}: {str(e)}")
            continue

    return pd.DataFrame(sentiment_data)


def render_sentiment_dashboard(symbols):
    """Render the enhanced sentiment dashboard"""
    st.title("Market Sentiment Dashboard")
    st.write(
        "Multi-source sentiment analysis including news, and analyst ratings")

    # Add auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    with col2:
        st.write("Auto-refresh")
        auto_refresh = st.toggle("Enable", value=True, key="sentiment_refresh")

    if auto_refresh:
        sentiment_df = analyze_market_sentiment(symbols)

        if not sentiment_df.empty:
            # Overall market sentiment
            st.subheader("Overall Market Sentiment")
            avg_sentiment = sentiment_df['composite_sentiment'].mean()

            # Create composite sentiment gauge
            sentiment_fig = create_gauge_chart(avg_sentiment,
                                               "Market Sentiment Score")
            st.plotly_chart(sentiment_fig, use_container_width=True)

            # Individual stock analysis
            st.subheader("Individual Stock Sentiment Analysis")

            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                sentiment_filter = st.selectbox(
                    "Filter by Sentiment",
                    ["All", "Bullish", "Bearish", "Neutral"])

            # Filter dataframe based on selection
            filtered_df = sentiment_df
            if sentiment_filter == "Bullish":
                filtered_df = sentiment_df[sentiment_df['composite_sentiment']
                                           > 0.2]
            elif sentiment_filter == "Bearish":
                filtered_df = sentiment_df[sentiment_df['composite_sentiment']
                                           < -0.2]
            elif sentiment_filter == "Neutral":
                filtered_df = sentiment_df[
                    (sentiment_df['composite_sentiment'] >= -0.2)
                    & (sentiment_df['composite_sentiment'] <= 0.2)]

            # Display individual stock sentiments
            for idx, row in filtered_df.iterrows():
                with st.expander(f"{row['symbol']} - {row['name']}"):
                    # Create three columns for different sentiment metrics
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Price", f"${row['price']:.2f}",
                                  f"{row['change']:+.2f}%")

                    with col2:
                        st.write("Sentiment Score:")
                        sentiment_fig = create_gauge_chart(
                            row['composite_sentiment'], "Overall Sentiment")
                        st.plotly_chart(sentiment_fig,
                                        use_container_width=True)

                    with col3:
                        st.write("Sentiment Breakdown:")
                        st.write(f"News Sentiment: {row['sentiment_emoji']}")
                        st.write(
                            f"Analyst Rating: {format_number(row['analyst_sentiment'])}"
                        )

                    # Show detailed analyst recommendations if available
                    if row['analyst_data'] is not None:
                        st.write("Analyst Recommendations:")
                        rec = row['analyst_data']
                        cols = st.columns(5)
                        cols[0].metric("Strong Buy",
                                       row['analyst_data'].get('strongBuy', 0))
                        cols[1].metric("Buy",
                                       row['analyst_data'].get('buy', 0))
                        cols[2].metric("Hold", rec.get('hold', 0))
                        cols[3].metric("Sell", rec.get('sell', 0))
                        cols[4].metric("Strong Sell", rec.get('strongSell', 0))
        else:
            st.error(
                "Unable to fetch sentiment data. Please check your API key and internet connection."
            )
            st.info(
                "If the error persists, try refreshing the page or selecting fewer stocks to analyze."
            )
