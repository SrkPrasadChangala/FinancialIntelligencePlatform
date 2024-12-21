import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [newSymbol, setNewSymbol] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    fetchWatchlist();
  }, [user]);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/watchlist/${user.id}`);
      setWatchlist(response.data);
    } catch (err) {
      setError('Failed to load watchlist');
      console.error('Watchlist fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymbol = async (e) => {
    e.preventDefault();
    if (!newSymbol) return;

    try {
      setError('');
      setSuccess('');
      const response = await axios.post(`/api/watchlist/${user.id}`, {
        symbol: newSymbol.toUpperCase(),
      });
      setSuccess(response.data.message);
      setNewSymbol('');
      fetchWatchlist();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add symbol');
    }
  };

  const handleRemoveSymbol = async (symbol) => {
    try {
      setError('');
      await axios.delete(`/api/watchlist/${user.id}/${symbol}`);
      fetchWatchlist();
    } catch (err) {
      setError('Failed to remove symbol');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Watchlist
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleAddSymbol}>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              fullWidth
              label="Add Symbol"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              placeholder="Enter stock symbol (e.g., AAPL)"
            />
            <Button
              variant="contained"
              color="primary"
              type="submit"
              disabled={!newSymbol}
            >
              Add
            </Button>
          </Box>
        </form>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <List>
          {watchlist.map((item) => (
            <ListItem
              key={item.symbol}
              divider
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleRemoveSymbol(item.symbol)}
                >
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemText
                primary={`${item.symbol} - ${item.name}`}
                secondary={
                  <Typography component="div">
                    <Box component="span" sx={{ color: 'primary.main' }}>
                      ${item.price.toFixed(2)}
                    </Box>
                    <Box
                      component="span"
                      sx={{
                        ml: 2,
                        color: item.change >= 0 ? 'success.main' : 'error.main',
                      }}
                    >
                      {item.change >= 0 ? '+' : ''}
                      {item.change.toFixed(2)}%
                    </Box>
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
};

export default Watchlist;
