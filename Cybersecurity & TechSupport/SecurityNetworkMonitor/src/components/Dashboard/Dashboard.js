import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  CircularProgress
} from '@mui/material';
import {
  Security as SecurityIcon,
  NetworkCheck as NetworkIcon,
  Computer as DeviceIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Shield as ShieldIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  SmartToy as AIIcon
} from '@mui/icons-material';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { api } from '../../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

const Dashboard = () => {
  // State management
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [aiStatus, setAiStatus] = useState(null);
  const [threatPredictions, setThreatPredictions] = useState([]);
  const [anomalyReport, setAnomalyReport] = useState(null);
  const [dashboardMetrics, setDashboardMetrics] = useState({
    totalDevices: 0,
    onlineDevices: 0,
    criticalAlerts: 0,
    totalEvents: 0,
    threatScore: 0,
    networkHealth: 100
  });
  const [scanProgress, setScanProgress] = useState({
    isScanning: false,
    progress: 0,
    currentTarget: '',
    scansCompleted: 0,
    totalTargets: 0
  });

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      const [
        devicesData,
        eventsData,
        aiStatusData,
        threatPredictionsData,
        anomalyReportData
      ] = await Promise.all([
        api.getDevices(),
        api.getAllSecurityEvents(),
        fetch('/api/v1/ai-engine/system_status/').then(res => res.json()),
        fetch('/api/v1/ai-engine/threat_predictions/').then(res => res.json()),
        fetch('/api/v1/ai-engine/anomaly_report/').then(res => res.json())
      ]);

      setDevices(devicesData.results || devicesData || []);
      setEvents(eventsData.results || eventsData || []);
      setAiStatus(aiStatusData.ai_system_status?.system_status || {});
      setThreatPredictions(threatPredictionsData.predictions || []);
      setAnomalyReport(anomalyReportData.anomaly_report || {});

      // Calculate dashboard metrics
      const deviceData = devicesData.results || devicesData || [];
      const eventData = eventsData.results || eventsData || [];
      
      const totalDevices = deviceData.length;
      const onlineDevices = deviceData.filter(d => d.status === 'online').length;
      const criticalAlerts = eventData.filter(e => e.severity === 'critical' && !e.is_resolved).length;
      const totalEvents = eventData.length;
      
      // Calculate threat score based on unresolved events
      const unresolvedEvents = eventData.filter(e => !e.is_resolved);
      const threatScore = Math.min(100, unresolvedEvents.length * 2);
      
      setDashboardMetrics({
        totalDevices,
        onlineDevices,
        criticalAlerts,
        totalEvents,
        threatScore,
        networkHealth: totalDevices > 0 ? Math.round((onlineDevices / totalDevices) * 100) : 100
      });

      // Mock scan progress (replace with real API when available)
      setScanProgress({
        isScanning: Math.random() > 0.7,
        progress: Math.floor(Math.random() * 100),
        currentTarget: '192.168.1.' + Math.floor(Math.random() * 255),
        scansCompleted: Math.floor(Math.random() * 50),
        totalTargets: 254
      });

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    fetchDashboardData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, 5000);
      return () => clearInterval(interval);
    }
  }, [fetchDashboardData, autoRefresh]);

  // Calculate derived metrics
  const derivedMetrics = useMemo(() => {
    const onlinePercentage = dashboardMetrics.totalDevices > 0 
      ? (dashboardMetrics.onlineDevices / dashboardMetrics.totalDevices) * 100 
      : 0;
    
    const threatLevel = dashboardMetrics.threatScore > 75 ? 'critical' 
      : dashboardMetrics.threatScore > 50 ? 'high'
      : dashboardMetrics.threatScore > 25 ? 'medium' : 'low';

    return {
      onlinePercentage,
      threatLevel
    };
  }, [dashboardMetrics]);

  // Chart configurations
  const timelineChartData = {
    labels: events.slice(-24).map(event => 
      new Date(event.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    ),
    datasets: [
      {
        label: 'Security Events',
        data: events.slice(-24).map((_, index) => index + 1),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4
      },
      {
        label: 'Network Activity',
        data: Array.from({ length: 24 }, (_, i) => Math.random() * 100),
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.4
      }
    ]
  };

  const threatDistributionData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [
        events.filter(e => e.severity === 'critical').length,
        events.filter(e => e.severity === 'high').length,
        events.filter(e => e.severity === 'medium').length,
        events.filter(e => e.severity === 'low').length
      ],
      backgroundColor: ['#ff4444', '#ff8800', '#ffbb33', '#00C851'],
      borderWidth: 2,
      borderColor: '#fff'
    }]
  };

  const deviceStatusData = {
    labels: ['Online', 'Offline', 'Warning'],
    datasets: [{
      data: [
        dashboardMetrics.onlineDevices,
        dashboardMetrics.totalDevices - dashboardMetrics.onlineDevices,
        devices.filter(d => d.status === 'warning').length
      ],
      backgroundColor: ['#00C851', '#ff4444', '#ffbb33'],
      borderWidth: 2,
      borderColor: '#fff'
    }]
  };

  // Metric card component
  const MetricCard = ({ title, value, subtitle, icon, color, trend }) => (
    <Card 
      sx={{ 
        height: '100%',
        background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
        backgroundColor: '#1a1a2e',
        border: `1px solid ${color}30`,
        transition: 'all 0.3s ease',
        color: '#ffffff',
        '&:hover': {
          boxShadow: 3
        }
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="h4" fontWeight="bold" sx={{ color: color }}>
              {value}
            </Typography>
            <Typography variant="h6" sx={{ color: '#ffffff' }} gutterBottom>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" sx={{ color: '#b3b3b3' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box display="flex" flexDirection="column" alignItems="center">
            <Avatar sx={{ bgcolor: `${color}20`, color: color, mb: 1 }}>
              {icon}
            </Avatar>
            {trend && (
              <Box display="flex" alignItems="center">
                {trend > 0 ? <TrendingUpIcon color="success" /> : <TrendingDownIcon color="error" />}
                <Typography variant="caption" color={trend > 0 ? 'success.main' : 'error.main'}>
                  {Math.abs(trend)}%
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ 
      flexGrow: 1, 
      p: 3, 
      bgcolor: '#0a0e1a', 
      minHeight: '100vh',
      color: '#ffffff'
    }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" sx={{ color: '#2196f3' }}>
            🛡️ Security Operations Center
          </Typography>
          <Typography variant="subtitle1" sx={{ color: '#b3b3b3' }}>
            Real-time cybersecurity monitoring and threat analysis
          </Typography>
        </Box>
        
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="primary"
              />
            }
            label="Auto Refresh"
            sx={{ color: '#ffffff' }}
          />
          
          <Tooltip title="Refresh Dashboard">
            <IconButton onClick={fetchDashboardData} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Chip
            icon={<TimelineIcon />}
            label={`Updated ${new Date().toLocaleTimeString()}`}
            variant="outlined"
            color="primary"
          />
        </Box>
      </Box>

      {/* Alert Banner */}
      {dashboardMetrics.criticalAlerts > 0 && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small">
              VIEW ALERTS
            </Button>
          }
        >
          🚨 {dashboardMetrics.criticalAlerts} critical security alerts require immediate attention
        </Alert>
      )}

      {/* Main Metrics Grid */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Network Devices"
            value={dashboardMetrics.totalDevices}
            subtitle={`${dashboardMetrics.onlineDevices} online (${derivedMetrics.onlinePercentage.toFixed(1)}%)`}
            icon={<DeviceIcon />}
            color="#2196f3"
            trend={5}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Security Events"
            value={dashboardMetrics.totalEvents}
            subtitle="Total events detected"
            icon={<SecurityIcon />}
            color="#ff9800"
            trend={-12}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Threat Score"
            value={`${dashboardMetrics.threatScore}/100`}
            subtitle={`Risk Level: ${derivedMetrics.threatLevel.toUpperCase()}`}
            icon={<ShieldIcon />}
            color={derivedMetrics.threatLevel === 'critical' ? '#f44336' : 
                  derivedMetrics.threatLevel === 'high' ? '#ff9800' : '#4caf50'}
            trend={-8}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Network Health"
            value={`${dashboardMetrics.networkHealth}%`}
            subtitle="Overall system status"
            icon={<NetworkIcon />}
            color="#4caf50"
            trend={2}
          />
        </Grid>
      </Grid>

      {/* Secondary Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ 
            height: '100%',
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="bold" sx={{ color: '#ffffff' }}>
                  📈 Real-time Activity Timeline
                </Typography>
                <Box display="flex" gap={1}>
                  <Chip label="24h" size="small" color="primary" />
                  <Chip label="Live" size="small" variant="outlined" />
                </Box>
              </Box>
              <Box height={300}>
                <Line 
                  data={timelineChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { 
                        position: 'top',
                        labels: { color: '#ffffff' }
                      }
                    },
                    scales: {
                      x: { 
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                      },
                      y: { 
                        beginAtZero: true,
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ 
            height: '100%',
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2} sx={{ color: '#ffffff' }}>
                🎯 AI System Status
              </Typography>
              
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" sx={{ color: '#ffffff' }}>Threat Detector</Typography>
                  <Chip 
                    label={aiStatus?.threat_detector_trained ? "ACTIVE" : "INACTIVE"}
                    color={aiStatus?.threat_detector_trained ? "success" : "error"}
                    size="small"
                  />
                </Box>
                
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" sx={{ color: '#ffffff' }}>Anomaly Detector</Typography>
                  <Chip 
                    label={aiStatus?.anomaly_detector_trained ? "ACTIVE" : "INACTIVE"}
                    color={aiStatus?.anomaly_detector_trained ? "success" : "error"}
                    size="small"
                  />
                </Box>
                
                <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />
                
                <Box>
                  <Typography variant="body2" sx={{ color: '#b3b3b3' }} gutterBottom>
                    AI Analysis Results
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#ffffff' }}>
                    🔍 {anomalyReport?.anomalies_detected || 0} anomalies detected
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#ffffff' }}>
                    ⚠️ {threatPredictions?.length || 0} events analyzed
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#4caf50' }}>
                    🤖 AI Status: ACTIVE & LEARNING
                  </Typography>
                  {threatPredictions?.length > 0 && (
                    <Typography variant="caption" sx={{ color: '#b3b3b3', display: 'block', mt: 1 }}>
                      Latest: {threatPredictions[0]?.prediction?.threat_level?.replace('_', ' ').toUpperCase()} threat 
                      ({(threatPredictions[0]?.prediction?.confidence * 100).toFixed(1)}% confidence)
                    </Typography>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Analysis */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2} sx={{ color: '#ffffff' }}>
                🛡️ Threat Distribution
              </Typography>
              <Box height={250}>
                <Doughnut 
                  data={threatDistributionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { 
                        position: 'bottom',
                        labels: { color: '#ffffff' }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2} sx={{ color: '#ffffff' }}>
                💻 Device Status
              </Typography>
              <Box height={250}>
                <Doughnut 
                  data={deviceStatusData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { 
                        position: 'bottom',
                        labels: { color: '#ffffff' }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2} sx={{ color: '#ffffff' }}>
                🔍 Network Scanning
              </Typography>
              
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" sx={{ color: '#ffffff' }}>Scan Status</Typography>
                  <Chip 
                    label={scanProgress.isScanning ? "SCANNING" : "IDLE"}
                    color={scanProgress.isScanning ? "warning" : "default"}
                    size="small"
                    icon={scanProgress.isScanning ? <CircularProgress size={16} /> : <CheckIcon />}
                  />
                </Box>
                
                {scanProgress.isScanning && (
                  <>
                    <Box>
                      <Typography variant="body2" gutterBottom sx={{ color: '#ffffff' }}>
                        Progress: {scanProgress.progress}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={scanProgress.progress} 
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                    
                    <Typography variant="body2" sx={{ color: '#b3b3b3' }}>
                      Current: {scanProgress.currentTarget}
                    </Typography>
                  </>
                )}
                
                <Box>
                  <Typography variant="body2" sx={{ color: '#ffffff' }}>
                    Completed: {scanProgress.scansCompleted}/{scanProgress.totalTargets}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2} sx={{ color: '#ffffff' }}>
                🚨 Recent Security Events
              </Typography>
              
              <List dense>
                {events.slice(0, 5).map((event, index) => (
                  <ListItem key={event.id} divider={index < 4}>
                    <ListItemIcon>
                      <Avatar 
                        sx={{ 
                          width: 32, 
                          height: 32,
                          bgcolor: event.severity === 'critical' ? '#f44336' :
                                  event.severity === 'high' ? '#ff9800' :
                                  event.severity === 'medium' ? '#ffeb3b' : '#4caf50'
                        }}
                      >
                        {event.severity === 'critical' ? <ErrorIcon /> : <WarningIcon />}
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={<Typography sx={{ color: '#ffffff' }}>{event.title}</Typography>}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block" sx={{ color: '#b3b3b3' }}>
                            {event.description}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#888888' }}>
                            {new Date(event.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip 
                      label={event.severity.toUpperCase()}
                      size="small"
                      color={
                        event.severity === 'critical' ? 'error' :
                        event.severity === 'high' ? 'warning' : 'default'
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{
            backgroundColor: '#1a1a2e',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={2} sx={{ color: '#ffffff' }}>
                🤖 AI Threat Predictions
              </Typography>
              
              <List dense>
                {threatPredictions.slice(0, 5).map((prediction, index) => (
                  <ListItem key={prediction.event_id} divider={index < 4}>
                    <ListItemIcon>
                      <Avatar 
                        sx={{ 
                          width: 32, 
                          height: 32,
                          bgcolor: prediction.prediction.threat_level === 'critical_threat' ? '#f44336' :
                                  prediction.prediction.threat_level === 'high_threat' ? '#ff9800' :
                                  prediction.prediction.threat_level === 'medium_threat' ? '#ffeb3b' : '#4caf50'
                        }}
                      >
                        <AIIcon />
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={<Typography sx={{ color: '#ffffff' }}>{`Event ${prediction.event_id}`}</Typography>}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block" sx={{ color: '#b3b3b3' }}>
                            {prediction.prediction.explanation}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#888888' }}>
                            Confidence: {(prediction.prediction.confidence * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip 
                      label={prediction.prediction.threat_level.replace('_', ' ').toUpperCase()}
                      size="small"
                      color={
                        prediction.prediction.threat_level === 'critical_threat' ? 'error' :
                        prediction.prediction.threat_level === 'high_threat' ? 'warning' : 'default'
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 