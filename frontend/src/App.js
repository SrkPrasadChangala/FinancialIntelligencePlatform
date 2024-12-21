import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container } from '@mui/material';
import Navbar from './components/layout/Navbar';
import Portfolio from './components/Portfolio';
import Trading from './components/Trading';
import Watchlist from './components/Watchlist';
import MarketSentiment from './components/MarketSentiment';
import SP100View from './components/SP100View';
import Login from './components/auth/Login';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <Container component="main" sx={{ mt: 4, mb: 4, flex: 1 }}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/watchlist" element={<Watchlist />} />
            <Route path="/market-sentiment" element={<MarketSentiment />} />
            <Route path="/sp100" element={<SP100View />} />
            <Route path="/" element={<Portfolio />} />
          </Routes>
        </Container>
      </Box>
    </AuthProvider>
  );
}

export default App;
