import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

// Components
import Layout from './components/Layout/Layout';

// Pages
import OldDashboard from './pages/Dashboard';
import NetworkDevices from './pages/NetworkDevices';
import NetworkScans from './pages/NetworkScans';
import NetworkTraffic from './pages/NetworkTraffic';
import SecurityEvents from './pages/SecurityEvents';
import Help from './pages/Settings';
import AIDashboard from './components/AIDashboard';

// New Comprehensive Dashboard
import Dashboard from './components/Dashboard';

// Dark theme configuration
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    secondary: {
      main: '#f50057',
      light: '#ff5983',
      dark: '#c51162',
    },
    background: {
      default: '#0a0e1a',
      paper: '#1a1a2e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3b3b3',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#1a1a2e',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          '&.MuiChip-colorSuccess': {
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            color: '#4caf50',
            border: '1px solid rgba(76, 175, 80, 0.5)',
          },
          '&.MuiChip-colorError': {
            backgroundColor: 'rgba(244, 67, 54, 0.2)',
            color: '#f44336',
            border: '1px solid rgba(244, 67, 54, 0.5)',
          },
          '&.MuiChip-colorWarning': {
            backgroundColor: 'rgba(255, 152, 0, 0.2)',
            color: '#ff9800',
            border: '1px solid rgba(255, 152, 0, 0.5)',
          },
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/old-dashboard" element={<OldDashboard />} />
            <Route path="/devices" element={<NetworkDevices />} />
            <Route path="/scans" element={<NetworkScans />} />
            <Route path="/traffic" element={<NetworkTraffic />} />
            <Route path="/security-events" element={<SecurityEvents />} />
            <Route path="/ai-dashboard" element={<AIDashboard />} />
            <Route path="/settings" element={<Help />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App; 