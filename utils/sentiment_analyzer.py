import os
from datetime import datetime, timedelta
from textblob import TextBlob
import finnhub
import pandas as pd
import yfinance as yf
from trafilatura import fetch_url, extract
import streamlit as st


class SentimentAnalyzer:

    def __init__(self):
        self.finnhub_client = finnhub.Client(
            api_key=os.getenv('FINNHUB_API_KEY'))

    @st.cache_data(ttl=300, max_entries=100)  # Cache for 5 minutes with limit
    def get_news_sentiment(_self, symbol):
        """Analyze sentiment from news articles"""
        try:
            # Get news from Finnhub
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                news = _self.finnhub_client.company_news(
                    symbol,
                    _from=start_date.strftime('%Y-%m-%d'),
                    to=end_date.strftime('%Y-%m-%d'))

                if not news:
                    st.warning(f"No recent news found for {symbol}")
                    return 0, 0  # Neutral sentiment if no news
            except Exception as e:
                st.warning(f"Error fetching news for {symbol}: {str(e)}")
                return 0, 0  # Neutral sentiment on error

            sentiments = []
            for article in news[:10]:  # Analyze last 10 news articles
                try:
                    # Get article content
                    content = extract(fetch_url(article['url']))
                    if content:
                        analysis = TextBlob(content)
                        sentiments.append(analysis.sentiment.polarity)
                except Exception:
                    continue

            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                confidence = len(
                    sentiments
                ) / 10  # Confidence based on number of analyzed articles
                return avg_sentiment, confidence
            return 0, 0
        except Exception as e:
            st.warning(f"Error fetching news sentiment: {str(e)}")
            return 0, 0

    @st.cache_data(ttl=300)
    def get_analyst_ratings(_self, symbol):
        """Get analyst recommendations"""
        try:
            recommendation = _self.finnhub_client.recommendation_trends(symbol)
            if recommendation:
                latest = recommendation[0]
                total = sum([
                    latest.get(k, 0) for k in
                    ['buy', 'hold', 'sell', 'strongBuy', 'strongSell']
                ])
                if total > 0:
                    sentiment_score = ((latest.get('strongBuy', 0) * 1.0 +
                                        latest.get('buy', 0) * 0.5 +
                                        latest.get('hold', 0) * 0.0 +
                                        latest.get('sell', 0) * -0.5 +
                                        latest.get('strongSell', 0) * -1.0) /
                                       total)
                    return sentiment_score, latest
            return 0, None
        except Exception as e:
            st.warning(f"Error fetching analyst ratings: {str(e)}")
            return 0, None

    def get_composite_sentiment(_self, symbol):
        """Calculate composite sentiment from all sources"""
        # Get individual sentiments
        news_sentiment, news_confidence = _self.get_news_sentiment(symbol)
        analyst_sentiment, analyst_data = _self.get_analyst_ratings(symbol)

        # Weighted average of sentiments
        weights = {'news': 0.3, 'analyst': 0.4, 'fear': 0.3}

        composite_sentiment = (news_sentiment * weights['news'] +
                               analyst_sentiment * weights['analyst'])

        return {
            'composite': composite_sentiment,
            'news': news_sentiment,
            'analyst': analyst_sentiment,
            'analyst_data': analyst_data,
            'news_confidence': news_confidence
        }
