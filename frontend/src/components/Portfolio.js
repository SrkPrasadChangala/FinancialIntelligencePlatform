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
  Alert,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const Portfolio = () => {
  const [portfolio, setPortfolio] = useState([]);
  const [error, setError] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const response = await axios.get(`/api/portfolio/${user.id}`);
        setPortfolio(response.data);
      } catch (err) {
        setError('Failed to load portfolio data');
        console.error('Portfolio fetch error:', err);
      }
    };

    if (user) {
      fetchPortfolio();
    }
  }, [user]);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Portfolio
      </Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Shares</TableCell>
              <TableCell align="right">Avg Price</TableCell>
              <TableCell align="right">Current Price</TableCell>
              <TableCell align="right">Total Value</TableCell>
              <TableCell align="right">Unrealized P/L</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {portfolio.map((holding) => (
              <TableRow key={holding.symbol}>
                <TableCell component="th" scope="row">
                  {holding.symbol}
                </TableCell>
                <TableCell align="right">{holding.quantity}</TableCell>
                <TableCell align="right">
                  ${holding.average_price.toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  ${holding.current_price.toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  ${(holding.quantity * holding.current_price).toFixed(2)}
                </TableCell>
                <TableCell
                  align="right"
                  style={{
                    color:
                      holding.unrealized_pl >= 0 ? 'rgb(0, 200, 0)' : 'rgb(255, 0, 0)',
                  }}
                >
                  ${holding.unrealized_pl.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Portfolio;
