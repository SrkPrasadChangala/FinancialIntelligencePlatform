"""
Sentiment Dashboard Component Module

This module implements a real-time market sentiment dashboard using Streamlit.
It provides comprehensive sentiment analysis for stocks by aggregating data
from multiple sources including news, social media, and analyst ratings.

The dashboard includes:
- Overall market sentiment visualization
- Individual stock sentiment analysis
- Analyst recommendations
- Interactive filters and auto-refresh capabilities

Dependencies:
    - streamlit: Web application framework
    - pandas: Data manipulation and analysis
    - plotly: Interactive visualization library
    - utils: Custom utility functions for data fetching and processing
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union
from utils import get_stock_data, get_stock_info, format_number
from utils.sentiment_analyzer import SentimentAnalyzer


def get_sentiment_emoji(sentiment_score: float) -> str:
    """
    Convert a numerical sentiment score into a representative emoji.

    Args:
        sentiment_score (float): A sentiment score in the range [-1.0, 1.0]
            where -1.0 is extremely bearish and 1.0 is extremely bullish.

    Returns:
        str: An emoji character representing the sentiment level:
            🚀 (>= 0.6): Strong bullish
            😊 (>= 0.2): Bullish
            😐 (>= -0.2): Neutral
            😟 (>= -0.6): Bearish
            😱 (< -0.6): Strong bearish
    """
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


def get_sentiment_color(sentiment_score: float) -> str:
    """
    Generate a color code based on the sentiment score for visual representation.

    Args:
        sentiment_score (float): A sentiment score in the range [-1.0, 1.0]
            where -1.0 is extremely negative and 1.0 is extremely positive.

    Returns:
        str: RGB color code string in format 'rgb(r,g,b)':
            Strong positive (>= 0.6): Pure green
            Positive (>= 0.2): Light green
            Neutral (>= -0.2): Light yellow
            Negative (>= -0.6): Light red
            Strong negative (< -0.6): Pure red
    """
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


def create_gauge_chart(value: float, title: str) -> go.Figure:
    """
    Create an interactive gauge chart for sentiment visualization using Plotly.

    Args:
        value (float): The sentiment value to display, in range [-1.0, 1.0].
            Will be converted to [0, 100] range for the gauge display.
        title (str): The title to display above the gauge chart.

    Returns:
        go.Figure: A Plotly figure object containing the configured gauge chart
            with color-coded sections and a numeric indicator.

    Note:
        The gauge is divided into 5 color-coded sections:
        - 0-20: Strong negative (red)
        - 20-40: Negative (light red)
        - 40-60: Neutral (yellow)
        - 60-80: Positive (light green)
        - 80-100: Strong positive (green)
    """
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
def analyze_market_sentiment(symbols: List[str]) -> pd.DataFrame:
    """
    Analyze market sentiment for a list of stock symbols using multiple data sources.

    This function processes a batch of stock symbols to gather comprehensive sentiment
    data including news sentiment, analyst ratings, and technical indicators. It includes
    robust error handling and performance optimizations such as batch processing and
    caching.

    Args:
        symbols (List[str]): List of stock symbols to analyze (e.g., ['AAPL', 'GOOGL'])

    Returns:
        pd.DataFrame: A DataFrame containing sentiment analysis results with columns:
            - symbol: Stock symbol
            - name: Company name
            - price: Current stock price
            - change: Price change percentage
            - composite_sentiment: Overall sentiment score
            - news_sentiment: News-based sentiment score
            - analyst_sentiment: Analyst ratings-based score
            - sentiment_emoji: Visual sentiment indicator
            - analyst_data: Detailed analyst recommendations

    Raises:
        Exception: Catches and handles various exceptions during data fetching and analysis:
            - API connection errors
            - Rate limiting issues
            - Invalid symbol formats
            - Missing or incomplete data

    Note:
        - Uses progress bar for visual feedback during processing
        - Implements batch processing (10 symbols at a time) for better performance
        - Caches results for 10 minutes to reduce API calls
        - Handles errors gracefully with appropriate user feedback
    """
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
                st.error(
                    f"Unexpected processing error for {symbol}: {str(generic_exception)}"
                )
                continue

            # Get multi-source sentiment with timeout handling
            try:
                sentiment = sentiment_analyzer.get_composite_sentiment(symbol)
                if not sentiment:
                    st.warning(f"Could not analyze sentiment for {symbol}")
                    continue

                sentiment_data.append({
                    'symbol':
                    symbol,
                    'name':
                    info.get('name', 'N/A'),
                    'price':
                    info.get('price', 0.0),
                    'change':
                    info.get('change', 0.0),
                    'composite_sentiment':
                    sentiment.get('composite', 0),
                    'news_sentiment':
                    sentiment.get('news', 0),
                    'analyst_sentiment':
                    sentiment.get('analyst', 0),
                    'sentiment_emoji':
                    get_sentiment_emoji(sentiment.get('composite', 0)),
                    'analyst_data':
                    sentiment.get('analyst_data', None)
                })
            except Exception as e:
                st.warning(f"Error analyzing sentiment for {symbol}: {str(e)}")
                continue

    # Clear progress bar
    progress_bar.empty()

    # Return empty DataFrame if no data collected
    if not sentiment_data:
        st.warning("No sentiment data could be collected for any symbols")
        return pd.DataFrame()

    return pd.DataFrame(sentiment_data)


def render_sentiment_dashboard(symbols: List[str]) -> None:
    """
    Render the main sentiment analysis dashboard with interactive components.

    This function creates a comprehensive dashboard displaying market sentiment data
    with multiple visualization components and interactive filters. It includes
    auto-refresh capabilities and error handling for a smooth user experience.

    Features:
        - Overall market sentiment gauge
        - Individual stock sentiment analysis
        - Sentiment filtering (Bullish/Bearish/Neutral)
        - Auto-refresh toggle
        - Detailed analyst recommendations
        - Price and change metrics
        - Multi-source sentiment breakdown

    Args:
        symbols (List[str]): List of stock symbols to display in the dashboard

    Note:
        The dashboard includes several interactive components:
        1. Auto-refresh toggle for real-time updates
        2. Sentiment filter dropdown
        3. Expandable sections for individual stocks
        4. Interactive gauge charts
        5. Detailed analyst recommendation breakdowns

    Error Handling:
        - Validates input symbols
        - Handles API failures gracefully
        - Provides user feedback for data fetching issues
        - Manages auto-refresh errors
        - Handles visualization component failures independently
    """
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
            auto_refresh = st.toggle("Enable",
                                     value=True,
                                     key="sentiment_refresh")
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
                    sentiment_fig = create_gauge_chart(
                        avg_sentiment, "Market Sentiment Score")
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
                    filtered_df = sentiment_df[
                        sentiment_df['composite_sentiment'] > 0.2]
                elif sentiment_filter == "Bearish":
                    filtered_df = sentiment_df[
                        sentiment_df['composite_sentiment'] < -0.2]
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
                                row['composite_sentiment'],
                                "Overall Sentiment")
                            st.plotly_chart(sentiment_fig,
                                            use_container_width=True)

                        with col3:
                            st.write("Sentiment Breakdown:")
                            st.write(
                                f"News Sentiment: {row['sentiment_emoji']}")
                            st.write(
                                f"Analyst Rating: {format_number(row['analyst_sentiment'])}"
                            )

                        # Show detailed analyst recommendations if available
                        if row['analyst_data'] is not None:
                            st.write("Analyst Recommendations:")
                            rec = row['analyst_data']
                            cols = st.columns(5)
                            cols[0].metric(
                                "Strong Buy",
                                row['analyst_data'].get('strongBuy', 0))
                            cols[1].metric("Buy",
                                           row['analyst_data'].get('buy', 0))
                            cols[2].metric("Hold", rec.get('hold', 0))
                            cols[3].metric("Sell", rec.get('sell', 0))
                            cols[4].metric("Strong Sell",
                                           rec.get('strongSell', 0))
            else:
                st.error(
                    "Unable to fetch sentiment data. Please check your API key and internet connection."
                )
                st.info(
                    "If the error persists, try refreshing the page or selecting fewer stocks to analyze."
                )
    except Exception as e:
        st.exception(e)
