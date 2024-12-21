import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  CircularProgress,
  Alert,
} from '@mui/material';
import axios from 'axios';

const SP100_SYMBOLS = [
  "AAPL", "MSFT", "AMZN", "GOOGL", "META",
  "NVDA", "BRK-B", "JPM", "JNJ", "V",
  "PG", "XOM", "MA", "HD", "CVX",
  "BAC", "KO", "PFE", "ABBV", "WMT",
  "AVGO", "PEP", "LLY", "MRK", "TMO"
];

const SP100View = () => {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchStockData();
  }, []);

  const fetchStockData = async () => {
    try {
      setLoading(true);
      const stockData = await Promise.all(
        SP100_SYMBOLS.map(symbol =>
          axios.get(`/api/stock/${symbol}`)
            .then(response => ({
              symbol,
              ...response.data
            }))
            .catch(() => null)
        )
      );

      setStocks(stockData.filter(s => s !== null));
    } catch (err) {
      setError('Failed to fetch stock data');
      console.error('Stock data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredStocks = stocks.filter(stock =>
    stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
        S&P 100 Stocks
      </Typography>

      <TextField
        fullWidth
        label="Search stocks"
        variant="outlined"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
      />

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="right">Change</TableCell>
              <TableCell align="right">Volume</TableCell>
              <TableCell align="right">Market Cap</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredStocks.map((stock) => (
              <TableRow key={stock.symbol}>
                <TableCell component="th" scope="row">
                  {stock.symbol}
                </TableCell>
                <TableCell>{stock.name}</TableCell>
                <TableCell align="right">${stock.price.toFixed(2)}</TableCell>
                <TableCell
                  align="right"
                  sx={{
                    color: stock.change >= 0 ? 'success.main' : 'error.main',
                  }}
                >
                  {stock.change >= 0 ? '+' : ''}
                  {stock.change.toFixed(2)}%
                </TableCell>
                <TableCell align="right">
                  {stock.volume.toLocaleString()}
                </TableCell>
                <TableCell align="right">
                  ${(stock.marketCap / 1e9).toFixed(2)}B
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default SP100View;
