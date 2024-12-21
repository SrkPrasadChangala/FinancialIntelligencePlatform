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
        self.finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_news_sentiment(self, symbol):
        """Analyze sentiment from news articles"""
        try:
            # Get news from Finnhub
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            news = self.finnhub_client.company_news(
                symbol,
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            
            if not news:
                return 0, 0  # Neutral sentiment if no news
            
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
                confidence = len(sentiments) / 10  # Confidence based on number of analyzed articles
                return avg_sentiment, confidence
            return 0, 0
        except Exception as e:
            st.warning(f"Error fetching news sentiment: {str(e)}")
            return 0, 0
    
    @st.cache_data(ttl=300)
    def get_analyst_ratings(self, symbol):
        """Get analyst recommendations"""
        try:
            recommendation = self.finnhub_client.recommendation_trends(symbol)
            if recommendation:
                latest = recommendation[0]
                total = sum([latest.get(k, 0) for k in ['buy', 'hold', 'sell', 'strongBuy', 'strongSell']])
                if total > 0:
                    sentiment_score = (
                        (latest.get('strongBuy', 0) * 1.0 + 
                         latest.get('buy', 0) * 0.5 + 
                         latest.get('hold', 0) * 0.0 + 
                         latest.get('sell', 0) * -0.5 + 
                         latest.get('strongSell', 0) * -1.0) / total
                    )
                    return sentiment_score, latest
            return 0, None
        except Exception as e:
            st.warning(f"Error fetching analyst ratings: {str(e)}")
            return 0, None
    
    @st.cache_data(ttl=60)
    def get_market_fear_index(self):
        """Get VIX index data"""
        try:
            vix = yf.download('^VIX', period='5d')
            if not vix.empty:
                current_vix = vix['Close'].iloc[-1]
                vix_change = ((current_vix - vix['Close'].iloc[0]) / vix['Close'].iloc[0]) * 100
                # Convert VIX to a sentiment score (-1 to 1)
                # Higher VIX means more fear (negative sentiment)
                vix_sentiment = -min(max((current_vix - 15) / 35, -1), 1)
                return vix_sentiment, current_vix, vix_change
            return 0, 0, 0
        except Exception as e:
            st.warning(f"Error fetching VIX data: {str(e)}")
            return 0, 0, 0
    
    def get_composite_sentiment(self, symbol):
        """Calculate composite sentiment from all sources"""
        # Get individual sentiments
        news_sentiment, news_confidence = self.get_news_sentiment(symbol)
        analyst_sentiment, analyst_data = self.get_analyst_ratings(symbol)
        fear_sentiment, vix_value, vix_change = self.get_market_fear_index()
        
        # Weighted average of sentiments
        weights = {
            'news': 0.3,
            'analyst': 0.4,
            'fear': 0.3
        }
        
        composite_sentiment = (
            news_sentiment * weights['news'] +
            analyst_sentiment * weights['analyst'] +
            fear_sentiment * weights['fear']
        )
        
        return {
            'composite': composite_sentiment,
            'news': news_sentiment,
            'analyst': analyst_sentiment,
            'fear': fear_sentiment,
            'vix': vix_value,
            'vix_change': vix_change,
            'analyst_data': analyst_data,
            'news_confidence': news_confidence
        }
