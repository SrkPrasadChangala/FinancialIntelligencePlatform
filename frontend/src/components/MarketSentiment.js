import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
} from '@mui/material';
import axios from 'axios';

const SentimentGauge = ({ value, title }) => {
  const getColor = (score) => {
    if (score >= 0.6) return 'rgb(0,255,0)';
    if (score >= 0.2) return 'rgb(144,238,144)';
    if (score >= -0.2) return 'rgb(255,255,191)';
    if (score >= -0.6) return 'rgb(255,160,122)';
    return 'rgb(255,0,0)';
  };

  const getEmoji = (score) => {
    if (score >= 0.6) return '🚀';
    if (score >= 0.2) return '😊';
    if (score >= -0.2) return '😐';
    if (score >= -0.6) return '😟';
    return '😱';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>{title}</Typography>
        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
          <CircularProgress
            variant="determinate"
            value={(value + 1) * 50}
            size={80}
            sx={{ color: getColor(value) }}
          />
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="h4">{getEmoji(value)}</Typography>
          </Box>
        </Box>
        <Typography variant="body1" sx={{ mt: 1 }}>
          Score: {value.toFixed(2)}
        </Typography>
      </CardContent>
    </Card>
  );
};

const MarketSentiment = () => {
  const [sentimentData, setSentimentData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const SP100_SYMBOLS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "NVDA", "BRK-B", "JPM", "JNJ", "V",
    // Add more symbols as needed
  ];

  useEffect(() => {
    const fetchSentimentData = async () => {
      try {
        setLoading(true);
        const sentiments = await Promise.all(
          SP100_SYMBOLS.map(symbol =>
            axios.get(`/api/sentiment/${symbol}`)
              .then(response => ({
                symbol,
                ...response.data
              }))
              .catch(() => null)
          )
        );

        setSentimentData(sentiments.filter(s => s !== null));
      } catch (err) {
        setError('Failed to fetch sentiment data');
        console.error('Sentiment fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSentimentData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Market Sentiment Analysis
      </Typography>
      
      <Grid container spacing={3}>
        {sentimentData.map((data, index) => (
          <Grid item xs={12} sm={6} md={4} key={data.symbol}>
            <Paper elevation={3} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {data.symbol}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <SentimentGauge
                    value={data.composite}
                    title="Overall Sentiment"
                  />
                </Grid>
                <Grid item xs={6}>
                  <SentimentGauge
                    value={data.news}
                    title="News Sentiment"
                  />
                </Grid>
                <Grid item xs={6}>
                  <SentimentGauge
                    value={data.analyst}
                    title="Analyst Sentiment"
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default MarketSentiment;
