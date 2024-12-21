import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Button,
  IconButton,
} from '@mui/material';
import { ShowChart, AccountBalance, Assessment, List } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) {
    return null;
  }

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Financial Intelligence Platform
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Link to="/portfolio" style={{ textDecoration: 'none', color: 'inherit' }}>
            <IconButton color="inherit" title="Portfolio">
              <AccountBalance />
            </IconButton>
          </Link>
          <Link to="/trading" style={{ textDecoration: 'none', color: 'inherit' }}>
            <IconButton color="inherit" title="Trading">
              <ShowChart />
            </IconButton>
          </Link>
          <Link to="/market-sentiment" style={{ textDecoration: 'none', color: 'inherit' }}>
            <IconButton color="inherit" title="Market Sentiment">
              <Assessment />
            </IconButton>
          </Link>
          <Link to="/watchlist" style={{ textDecoration: 'none', color: 'inherit' }}>
            <IconButton color="inherit" title="Watchlist">
              <List />
            </IconButton>
          </Link>
          <Button color="inherit" onClick={handleLogout}>
            Logout
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
