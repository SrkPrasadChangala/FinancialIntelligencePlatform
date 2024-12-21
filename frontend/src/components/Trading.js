import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const Trading = () => {
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [action, setAction] = useState('BUY');
  const [stockInfo, setStockInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [orderPreview, setOrderPreview] = useState(null);
  const { user } = useAuth();

  const handleSymbolChange = async (event) => {
    const newSymbol = event.target.value.toUpperCase();
    setSymbol(newSymbol);
    if (newSymbol.length >= 1) {
      try {
        setLoading(true);
        setError('');
        const response = await axios.get(`/api/stock/${newSymbol}`);
        setStockInfo(response.data);
        updateOrderPreview(newSymbol, quantity, action);
      } catch (err) {
        setError('Failed to fetch stock information');
        setStockInfo(null);
      } finally {
        setLoading(false);
      }
    }
  };

  const updateOrderPreview = (sym, qty, act) => {
    if (stockInfo) {
      const total = stockInfo.price * qty;
      setOrderPreview({
        symbol: sym,
        action: act,
        quantity: qty,
        price: stockInfo.price,
        total: total,
      });
    }
  };

  const handleQuantityChange = (event) => {
    const qty = parseInt(event.target.value, 10);
    setQuantity(qty);
    updateOrderPreview(symbol, qty, action);
  };

  const handleActionChange = (event) => {
    const act = event.target.value;
    setAction(act);
    updateOrderPreview(symbol, quantity, act);
  };

  const handleTrade = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const response = await axios.post('/api/trade', {
        userId: user.id,
        symbol,
        quantity,
        action,
      });

      setSuccess(response.data.message);
      setOrderPreview(null);
      setSymbol('');
      setQuantity(1);
    } catch (err) {
      setError(err.response?.data?.error || 'Trade failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Trade Stocks
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Symbol"
              value={symbol}
              onChange={handleSymbolChange}
              placeholder="Enter stock symbol (e.g., AAPL)"
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Action</InputLabel>
              <Select value={action} onChange={handleActionChange}>
                <MenuItem value="BUY">Buy</MenuItem>
                <MenuItem value="SELL">Sell</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              label="Quantity"
              value={quantity}
              onChange={handleQuantityChange}
              inputProps={{ min: 1 }}
            />
          </Grid>
        </Grid>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {success}
          </Alert>
        )}

        {stockInfo && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Stock Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography>Current Price:</Typography>
                <Typography variant="h6">${stockInfo.price}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography>Change:</Typography>
                <Typography
                  variant="h6"
                  sx={{
                    color: stockInfo.change >= 0 ? 'success.main' : 'error.main',
                  }}
                >
                  {stockInfo.change}%
                </Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography>Volume:</Typography>
                <Typography variant="h6">
                  {stockInfo.volume.toLocaleString()}
                </Typography>
              </Grid>
            </Grid>
          </Box>
        )}

        {orderPreview && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Order Preview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography>
                  {orderPreview.action} {orderPreview.quantity} shares of{' '}
                  {orderPreview.symbol} @ ${orderPreview.price}
                </Typography>
                <Typography variant="h6">
                  Total: ${orderPreview.total.toFixed(2)}
                </Typography>
              </Grid>
            </Grid>

            <Button
              variant="contained"
              color="primary"
              onClick={handleTrade}
              disabled={loading}
              sx={{ mt: 2 }}
            >
              Confirm {orderPreview.action}
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Trading;
