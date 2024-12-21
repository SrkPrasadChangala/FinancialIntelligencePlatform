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


@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce API calls
def analyze_market_sentiment(symbols):
    """Analyze market sentiment for given symbols with improved error handling and performance"""
    if not symbols:
        return pd.DataFrame()  # Return empty DataFrame if no symbols provided

    sentiment_analyzer = SentimentAnalyzer()
    sentiment_data = []

    # Add progress bar for better UX
    progress_bar = st.progress(0)
    total_symbols = len(symbols)

    # Process symbols in batches of 10 for better performance
    batch_size = 10
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        for idx, symbol in enumerate(batch, start=i):
            try:
                # Update progress
                progress_bar.progress((idx + 1) / total_symbols)

                # Validate symbol format
                if not isinstance(symbol, str) or not symbol.strip():
                    st.warning(f"Invalid symbol format: {symbol}")
                    continue

                info = get_stock_info(symbol)
                if not info:
                    st.warning(f"Could not fetch info for {symbol}")
                    continue

                data = get_stock_data(symbol, period='5d')
                if data is None or data.empty:
                    st.warning(f"No historical data available for {symbol}")
                    continue
            except Exception as generic_exception:
                st.error(f"Unexpected processing error for {symbol}: {str(generic_exception)}")
                continue

            # Get multi-source sentiment with timeout handling
            try:
                sentiment = sentiment_analyzer.get_composite_sentiment(symbol)
                if not sentiment:
                    st.warning(f"Could not analyze sentiment for {symbol}")
                    continue

                sentiment_data.append({
                    'symbol': symbol,
                    'name': info.get('name', 'N/A'),
                    'price': info.get('price', 0.0),
                    'change': info.get('change', 0.0),
                    'composite_sentiment': sentiment.get('composite', 0),
                    'news_sentiment': sentiment.get('news', 0),
                    'analyst_sentiment': sentiment.get('analyst', 0),
                    'sentiment_emoji': get_sentiment_emoji(sentiment.get('composite', 0)),
                    'analyst_data': sentiment.get('analyst_data', None)
                })
            except Exception as e:
                st.warning(f"Error analyzing sentiment for {symbol}: {str(e)}")
                continue

        except Exception as e:
            st.error(f"Unexpected error processing {symbol}: {str(e)}")
            continue

    # Clear progress bar
    progress_bar.empty()

    # Return empty DataFrame if no data collected
    if not sentiment_data:
        st.warning("No sentiment data could be collected for any symbols")
        return pd.DataFrame()

    return pd.DataFrame(sentiment_data)


def render_sentiment_dashboard(symbols):
    """Render the enhanced sentiment dashboard with improved error handling"""
    st.title("Market Sentiment Dashboard")
    st.write(
        "Multi-source sentiment analysis including news and analyst ratings")

    # Validate input
    if not symbols:
        st.warning("Please add some symbols to analyze")
        return

    # Add auto-refresh toggle with error handling
    try:
        col1, col2 = st.columns([3, 1])
        with col2:
            st.write("Auto-refresh")
            auto_refresh = st.toggle("Enable", value=True, key="sentiment_refresh")
    except Exception as e:
        st.error(f"Error setting up dashboard controls: {str(e)}")
        return

    try:
        if auto_refresh:
            with st.spinner('Fetching market sentiment data...'):
                sentiment_df = analyze_market_sentiment(symbols)

            if not sentiment_df.empty:
                # Overall market sentiment
                st.subheader("Overall Market Sentiment")
                avg_sentiment = sentiment_df['composite_sentiment'].mean()

                # Create composite sentiment gauge with error handling
                try:
                    sentiment_fig = create_gauge_chart(avg_sentiment,
                                                       "Market Sentiment Score")
                    st.plotly_chart(sentiment_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating sentiment chart: {str(e)}")

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
    except Exception as e:
        st.exception(f"An unexpected error occurred: {str(e)}")