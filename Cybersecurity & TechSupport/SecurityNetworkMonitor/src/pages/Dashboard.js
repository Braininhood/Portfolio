import React from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Devices as DevicesIcon,
  Security as SecurityIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material';
import useRealTimeDevices from '../hooks/useRealTimeDevices';

const MetricCard = ({ title, value, icon: Icon, color, subtitle, onClick }) => {
  return (
    <Card 
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        '&:hover': onClick ? {
          transform: 'translateY(-2px)',
          boxShadow: 6,
        } : {},
        background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.05) 100%)',
        border: '1px solid rgba(33, 150, 243, 0.2)',
      }}
      onClick={onClick}
    >
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            bgcolor: `${color}.light`,
            color: `${color}.contrastText`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Icon sx={{ fontSize: 28 }} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 0.5 }}>
            {value}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

const QuickActionCard = ({ title, description, icon: Icon, color, onClick, loading = false }) => {
  return (
    <Card 
      sx={{ 
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 6,
        },
        background: `linear-gradient(135deg, rgba(${color === 'primary' ? '33, 150, 243' : '76, 175, 80'}, 0.1) 0%, rgba(${color === 'primary' ? '33, 150, 243' : '76, 175, 80'}, 0.05) 100%)`,
        border: `1px solid rgba(${color === 'primary' ? '33, 150, 243' : '76, 175, 80'}, 0.2)`,
      }}
      onClick={!loading ? onClick : undefined}
    >
      <CardContent sx={{ textAlign: 'center', py: 3 }}>
        <Box
          sx={{
            p: 2,
            borderRadius: 3,
            bgcolor: `${color}.light`,
            color: `${color}.contrastText`,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
          }}
        >
          <Icon sx={{ fontSize: 32 }} />
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {description}
        </Typography>
        {loading && <LinearProgress />}
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const {
    devices,
    networkStats,
    onlineDevices,
    offlineDevices,
    connectionInfo,
    startNetworkDiscovery,
  } = useRealTimeDevices();

  const handleStartDiscovery = async () => {
    try {
      await startNetworkDiscovery();
    } catch (error) {
      console.error('Error starting discovery:', error);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            Network Security Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              icon={connectionInfo.status === 'connected' ? <PlayIcon /> : <RefreshIcon />}
              label={connectionInfo.text}
              color={connectionInfo.color}
              variant="outlined"
              size="small"
            />
            {networkStats.last_updated && (
              <Typography variant="caption" color="text.secondary">
                Last updated: {new Date(networkStats.last_updated).toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        </Box>
        <Tooltip title="Refresh Data">
          <IconButton 
            onClick={() => window.location.reload()} 
            sx={{ 
              bgcolor: 'primary.main', 
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' }
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Devices"
            value={devices.length}
            icon={DevicesIcon}
            color="primary"
            subtitle={`${onlineDevices.length} online, ${offlineDevices.length} offline`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Online Devices"
            value={onlineDevices.length}
            icon={TrendingUpIcon}
            color="success"
            subtitle="Currently responding"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Security Events"
            value={networkStats.unresolved_alerts || 0}
            icon={SecurityIcon}
            color="warning"
            subtitle="Requires attention"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Scans"
            value={networkStats.active_scans || 0}
            icon={TimelineIcon}
            color="info"
            subtitle="Currently running"
          />
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
          Quick Actions
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={4}>
            <QuickActionCard
              title="Network Discovery"
              description="Scan your network for new devices and update device statuses"
              icon={DevicesIcon}
              color="primary"
              onClick={handleStartDiscovery}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <QuickActionCard
              title="Security Scan"
              description="Run comprehensive security analysis on all network devices"
              icon={SecurityIcon}
              color="success"
              onClick={() => console.log('Security scan clicked')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <QuickActionCard
              title="Generate Report"
              description="Create detailed network status and security report"
              icon={TimelineIcon}
              color="primary"
              onClick={() => console.log('Generate report clicked')}
            />
          </Grid>
        </Grid>
      </Box>

      {/* Network Overview */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
            Network Overview
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Device Distribution
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Chip label={`${onlineDevices.length} Online`} color="success" size="small" />
                  <Chip label={`${offlineDevices.length} Offline`} color="error" size="small" />
                  <Chip 
                    label={`${devices.filter(d => d.status === 'unknown').length} Unknown`} 
                    color="default" 
                    size="small" 
                  />
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Connection Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip 
                    label={connectionInfo.text}
                    color={connectionInfo.color}
                    size="small"
                    variant="outlined"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Updates every 10 seconds
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Dashboard; 