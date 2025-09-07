import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  ButtonGroup
} from '@mui/material';
import {
  Security as SecurityIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Block as BlockIcon,
  Visibility as InvestigateIcon,
  Done as ResolveIcon,
  GetApp as ExportIcon,
  Timeline as TimelineIcon,
  NetworkCheck as NetworkIcon,
  FullscreenExit as ExitFullscreenIcon,
  Fullscreen as FullscreenIcon,
  TrendingUp as TrendingUpIcon,
  Shield as ShieldIcon,
  Gavel as BlockedIcon,
  NotificationsActive as AlertIcon
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
  ArcElement,
  Filler,
} from 'chart.js';
import { format, subHours, subDays } from 'date-fns';
import { api } from '../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  Filler
);

const SecurityEvents = () => {
  // State management
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [filters, setFilters] = useState({
    severity: 'all',
    status: 'all',
    timeRange: '24h',
    search: '',
    eventType: 'all'
  });
  const [viewMode, setViewMode] = useState('table');
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [fullScreen, setFullScreen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [actionLoading, setActionLoading] = useState(false);

  // Real-time metrics
  const [threatScore, setThreatScore] = useState(0);
  const [activeThreats, setActiveThreats] = useState(0);
  const [blockedAttacks, setBlockedAttacks] = useState(0);
  const [unresolvedEvents, setUnresolvedEvents] = useState(0);

  // Fetch security events and stats
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch events and stats in parallel with better error handling
      const [eventsResponse, statsResponse] = await Promise.all([
        api.getAllSecurityEvents().catch(err => {
          console.error('Events API Error:', err);
          return [];
        }),
        api.getSecurityEventStats().catch(err => {
          console.error('Stats API Error:', err);
          return {};
        })
      ]);
      
      // Handle different response formats
      let eventsData = [];
      if (eventsResponse?.results) {
        eventsData = eventsResponse.results;
      } else if (eventsResponse?.data?.results) {
        eventsData = eventsResponse.data.results;
      } else if (Array.isArray(eventsResponse)) {
        eventsData = eventsResponse;
      }
      
      console.log('Fetched events:', eventsData.length, 'events');
      console.log('Events response structure:', eventsResponse);
      console.log('Stats response:', statsResponse);
      setEvents(eventsData);
      
      // Calculate real-time metrics from actual data
      const unresolved = eventsData.filter(e => !e.is_resolved).length;
      const criticalHigh = eventsData.filter(e => 
        !e.is_resolved && (e.severity === 'critical' || e.severity === 'high')
      ).length;
      
      // Count events by severity (unresolved only for active threats)
      const unresolvedCritical = eventsData.filter(e => !e.is_resolved && e.severity === 'critical').length;
      const unresolvedHigh = eventsData.filter(e => !e.is_resolved && e.severity === 'high').length;
      const unresolvedMedium = eventsData.filter(e => !e.is_resolved && e.severity === 'medium').length;
      const unresolvedLow = eventsData.filter(e => !e.is_resolved && e.severity === 'low').length;
      
      // Calculate dynamic threat score (0-100) based on unresolved events
      const score = Math.min(100, Math.round(
        unresolvedCritical * 25 + 
        unresolvedHigh * 10 + 
        unresolvedMedium * 5 +
        unresolvedLow * 1
      ));
      
      console.log('Calculated metrics:', {
        unresolved,
        criticalHigh,
        totalEvents: eventsData.length,
        unresolvedCritical,
        unresolvedHigh,
        unresolvedMedium,
        unresolvedLow,
        calculatedThreatScore: score
      });
      
      setUnresolvedEvents(unresolved);
      setActiveThreats(criticalHigh);
      setThreatScore(score);
      
      console.log('Final metrics set:', {
        threatScore: score,
        activeThreats: criticalHigh,
        unresolvedEvents: unresolved,
        blockedAttacks: 'calculating...'
      });
      
      // Count blocked/resolved attacks (events that were resolved and had blocking action)
      const blockedEvents = eventsData.filter(e => 
        e.is_resolved && 
        e.details && 
        (e.details.status === 'blocked' || e.details.action_taken === 'threat_blocked')
      ).length;
      
      // If no specific blocked events, use resolved critical/high as estimate
      const resolvedCriticalHigh = eventsData.filter(e => 
        e.is_resolved && (e.severity === 'critical' || e.severity === 'high')
      ).length;
      
      setBlockedAttacks(blockedEvents > 0 ? blockedEvents : resolvedCriticalHigh);
      
      setError(null);
    } catch (err) {
      console.error('Failed to fetch security data:', err);
      setError('Failed to load security events. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load and real-time updates
  useEffect(() => {
    fetchData();
    
    // Set up real-time monitoring with different intervals based on monitoring state
    const interval = setInterval(() => {
      fetchData();
    }, isMonitoring ? 2000 : 5000); // 2s when monitoring, 5s otherwise
    
    return () => clearInterval(interval);
  }, [fetchData, isMonitoring]);

  // Force immediate refresh when monitoring state changes
  useEffect(() => {
    if (isMonitoring) {
      console.log('Live monitoring activated - refreshing data');
      fetchData();
    }
  }, [isMonitoring, fetchData]);

  // Filter events based on current filters
  const filteredEvents = useMemo(() => {
    if (!events.length) return [];
    
    return events.filter(event => {
      // Severity filter
      if (filters.severity !== 'all' && event.severity !== filters.severity) {
        return false;
      }
      
      // Status filter
      if (filters.status === 'resolved' && !event.is_resolved) return false;
      if (filters.status === 'unresolved' && event.is_resolved) return false;
      
      // Event type filter
      if (filters.eventType !== 'all' && event.event_type !== filters.eventType) {
        return false;
      }
      
      // Time range filter
      const eventTime = new Date(event.timestamp);
      const now = new Date();
      let cutoff;
      
      switch (filters.timeRange) {
        case '1h':
          cutoff = subHours(now, 1);
          break;
        case '6h':
          cutoff = subHours(now, 6);
          break;
        case '24h':
          cutoff = subHours(now, 24);
          break;
        case '7d':
          cutoff = subDays(now, 7);
          break;
        default:
          cutoff = new Date(0); // Show all
      }
      
      if (eventTime < cutoff) return false;
      
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        return (
          event.title?.toLowerCase().includes(searchLower) ||
          event.description?.toLowerCase().includes(searchLower) ||
          event.source_device_ip?.toLowerCase().includes(searchLower) ||
          event.target_device_ip?.toLowerCase().includes(searchLower)
        );
      }
      
      return true;
    });
  }, [events, filters]);

  // Get severity color and icon
  const getSeverityInfo = (severity) => {
    switch (severity) {
      case 'critical':
        return { color: '#f44336', icon: <ErrorIcon />, bgColor: '#ffebee' };
      case 'high':
        return { color: '#ff9800', icon: <WarningIcon />, bgColor: '#fff3e0' };
      case 'medium':
        return { color: '#2196f3', icon: <InfoIcon />, bgColor: '#e3f2fd' };
      case 'low':
        return { color: '#4caf50', icon: <CheckCircleIcon />, bgColor: '#e8f5e8' };
      default:
        return { color: '#757575', icon: <InfoIcon />, bgColor: '#f5f5f5' };
    }
  };

  // Handle event actions
  const handleInvestigate = async (eventId) => {
    try {
      setActionLoading(true);
      await api.investigateSecurityEvent(eventId);
      setSnackbar({
        open: true,
        message: 'Event marked for investigation',
        severity: 'info'
      });
      fetchData(); // Refresh data
    } catch (err) {
      setSnackbar({
        open: true,
        message: 'Failed to investigate event',
        severity: 'error'
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async (eventId) => {
    try {
      setActionLoading(true);
      await api.resolveSecurityEvent(eventId);
      setSnackbar({
        open: true,
        message: 'Event resolved successfully',
        severity: 'success'
      });
      fetchData(); // Refresh data
    } catch (err) {
      setSnackbar({
        open: true,
        message: 'Failed to resolve event',
        severity: 'error'
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleBlock = async (eventId) => {
    try {
      setActionLoading(true);
      await api.blockSecurityThreat(eventId);
      setSnackbar({
        open: true,
        message: 'Threat blocked successfully',
        severity: 'success'
      });
      fetchData(); // Refresh data
    } catch (err) {
      setSnackbar({
        open: true,
        message: 'Failed to block threat',
        severity: 'error'
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Export events data
  const handleExport = (format = 'json') => {
    try {
      if (!filteredEvents.length) {
        setSnackbar({
          open: true,
          message: 'No events to export',
          severity: 'warning'
        });
        return;
      }

      const timestamp = format(new Date(), 'yyyy-MM-dd-HH-mm');
      let dataStr, mimeType, fileExtension;

      if (format === 'txt') {
        // Generate TXT format
        const header = `SECURITY EVENTS REPORT
Generated: ${new Date().toLocaleString()}
Total Events: ${filteredEvents.length}
Filters Applied: ${JSON.stringify(filters, null, 2)}

${'='.repeat(80)}

`;

        const eventsText = filteredEvents.map((event, index) => {
          return `EVENT #${index + 1}
${'─'.repeat(40)}
ID: ${event.id}
Title: ${event.title}
Severity: ${event.severity?.toUpperCase()} ${event.severity === 'critical' ? '🚨' : event.severity === 'high' ? '⚠️' : event.severity === 'medium' ? '🔶' : '🔵'}
Event Type: ${event.event_type_display || event.event_type}
Device: ${event.source_device_ip || event.target_device_ip || 'N/A'}
Timestamp: ${new Date(event.timestamp).toLocaleString()}
Status: ${event.is_resolved ? '✅ RESOLVED' : '🔴 ACTIVE'}
${event.resolved_at ? `Resolved: ${new Date(event.resolved_at).toLocaleString()}` : ''}

Description:
${event.description || 'No description available'}

${event.details ? `Additional Details:
${JSON.stringify(event.details, null, 2)}` : ''}

${'─'.repeat(40)}
`;
        }).join('\n');

        dataStr = header + eventsText + `\n${'='.repeat(80)}\nEnd of Report`;
        mimeType = 'text/plain';
        fileExtension = 'txt';
      } else {
        // Generate JSON format
        const exportData = {
          exported_at: new Date().toISOString(),
          total_events: filteredEvents.length,
          filters_applied: filters,
          events: filteredEvents.map(event => ({
            id: event.id,
            title: event.title,
            description: event.description,
            severity: event.severity,
            event_type: event.event_type,
            source_device_ip: event.source_device_ip,
            target_device_ip: event.target_device_ip,
            timestamp: event.timestamp,
            is_resolved: event.is_resolved,
            resolved_at: event.resolved_at,
            details: event.details
          }))
        };

        dataStr = JSON.stringify(exportData, null, 2);
        mimeType = 'application/json';
        fileExtension = 'json';
      }

      const dataBlob = new Blob([dataStr], { type: mimeType });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `security-events-${timestamp}.${fileExtension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setSnackbar({
        open: true,
        message: `Exported ${filteredEvents.length} security events as ${format.toUpperCase()}`,
        severity: 'success'
      });
    } catch (err) {
      console.error('Export error:', err);
      setSnackbar({
        open: true,
        message: 'Failed to export events',
        severity: 'error'
      });
    }
  };

  // Chart data for timeline - use all events, not just filtered ones for accurate timeline
  const timelineData = useMemo(() => {
    if (!events.length) return null;
    
    // Group events by hour for the last 24 hours
    const now = new Date();
    const hours = Array.from({ length: 24 }, (_, i) => {
      const hour = subHours(now, 23 - i);
      return {
        hour: format(hour, 'HH:mm'),
        timestamp: hour,
        events: 0
      };
    });
    
    // Count events in each hour bucket
    events.forEach(event => {
      const eventTime = new Date(event.timestamp);
      
      // Find the closest hour bucket
      for (let i = 0; i < hours.length; i++) {
        const hourStart = hours[i].timestamp;
        const hourEnd = new Date(hourStart.getTime() + 3600000); // Add 1 hour
        
        if (eventTime >= hourStart && eventTime < hourEnd) {
          hours[i].events++;
          break;
        }
      }
    });
    
    return {
      labels: hours.map(h => h.hour),
      datasets: [
        {
          label: 'Security Events',
          data: hours.map(h => h.events),
          borderColor: '#f44336',
          backgroundColor: 'rgba(244, 67, 54, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    };
  }, [events]); // Use all events, not filtered events

  // Chart data for severity distribution - calculate from actual events data
  const severityData = useMemo(() => {
    if (!events.length) return null;
    
    // Count events by severity from actual events data
    const severityCounts = events.reduce((acc, event) => {
      acc[event.severity] = (acc[event.severity] || 0) + 1;
      return acc;
    }, {});
    
    return {
      labels: ['Critical', 'High', 'Medium', 'Low'],
      datasets: [
        {
          data: [
            severityCounts.critical || 0,
            severityCounts.high || 0,
            severityCounts.medium || 0,
            severityCounts.low || 0
          ],
          backgroundColor: ['#f44336', '#ff9800', '#2196f3', '#4caf50'],
          borderWidth: 2,
          borderColor: '#fff'
        }
      ]
    };
  }, [events]); // Use events instead of stats for real-time updates

  if (loading && !events.length) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ ml: 2 }}>
            Loading Security Operations Center...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth={fullScreen ? false : "xl"} sx={{ mt: 2, mb: 4, px: fullScreen ? 1 : 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <SecurityIcon sx={{ fontSize: 40, color: '#f44336', mr: 2 }} />
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              Security Operations Center
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Real-time Network Security Monitoring & Threat Response
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch
                checked={isMonitoring}
                onChange={(e) => setIsMonitoring(e.target.checked)}
                color="primary"
              />
            }
            label="Live Monitoring"
          />
          <IconButton onClick={() => setFullScreen(!fullScreen)} color="primary">
            {fullScreen ? <ExitFullscreenIcon /> : <FullscreenIcon />}
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error"
          sx={{ mb: 3 }}
          onClose={() => setError(null)}
          action={
            <Button color="inherit" size="small" onClick={fetchData}>
              Retry
            </Button>
          }
        >
          <strong>Error:</strong> {error}
        </Alert>
      )}

      {/* Real-time Status Alert */}
      {isMonitoring && !error && (
        <Alert 
          severity={unresolvedEvents > 50 ? "error" : unresolvedEvents > 10 ? "warning" : "info"}
          sx={{ mb: 3 }}
          icon={<AlertIcon />}
          action={
            <Box display="flex" alignItems="center" gap={1}>
              {loading && <CircularProgress size={16} />}
              <Chip 
                label={`${unresolvedEvents} Unresolved`} 
                color={unresolvedEvents > 50 ? "error" : unresolvedEvents > 10 ? "warning" : "default"}
                size="small"
              />
            </Box>
          }
        >
          <strong>Network Status:</strong> {
            unresolvedEvents > 50 ? "🚨 CRITICAL - Multiple active threats detected requiring immediate attention" :
            unresolvedEvents > 10 ? "⚠️ WARNING - Elevated threat activity detected" :
            "✅ MONITORING - Network security systems active and operational"
          } {loading && "(Updating...)"}
        </Alert>
      )}

      {/* Metrics Dashboard */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
            color: 'white',
            height: '120px'
          }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {threatScore}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Threat Score
                  </Typography>
                </Box>
                <ShieldIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={threatScore} 
                sx={{ 
                  mt: 1, 
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  '& .MuiLinearProgress-bar': { backgroundColor: 'white' }
                }} 
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
            color: 'white',
            height: '120px'
          }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {activeThreats}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Active Threats
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Critical & High Severity
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #4caf50 0%, #388e3c 100%)',
            color: 'white',
            height: '120px'
          }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {blockedAttacks}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Blocked Attacks
                  </Typography>
                </Box>
                <BlockedIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Automatically Mitigated
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
            color: 'white',
            height: '120px'
          }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {unresolvedEvents}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Unresolved Events
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Require Attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Analytics Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                24-Hour Security Events Timeline
              </Typography>
              {timelineData && (
                <Box sx={{ height: 300 }}>
                  <Line
                    data={timelineData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          mode: 'index',
                          intersect: false,
                        }
                      },
                      scales: {
                        x: { 
                          grid: { display: false },
                          title: { display: true, text: 'Time (24h)' }
                        },
                        y: { 
                          beginAtZero: true,
                          title: { display: true, text: 'Events Count' }
                        }
                      }
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Severity Distribution
              </Typography>
              {severityData && (
                <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                  <Doughnut
                    data={severityData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'bottom' }
                      }
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters and Controls */}
      <Paper elevation={1} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filters & Controls
        </Typography>
        <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search events..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>
            
            <Grid item xs={6} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select
                  value={filters.severity}
                  label="Severity"
                  onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
                >
                  <MenuItem value="all">All Severities</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.status}
                  label="Status"
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="unresolved">Unresolved</MenuItem>
                  <MenuItem value="resolved">Resolved</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Time Range</InputLabel>
                <Select
                  value={filters.timeRange}
                  label="Time Range"
                  onChange={(e) => setFilters(prev => ({ ...prev, timeRange: e.target.value }))}
                >
                  <MenuItem value="1h">Last Hour</MenuItem>
                  <MenuItem value="6h">Last 6 Hours</MenuItem>
                  <MenuItem value="24h">Last 24 Hours</MenuItem>
                  <MenuItem value="7d">Last 7 Days</MenuItem>
                  <MenuItem value="all">All Time</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={filters.eventType}
                  label="Event Type"
                  onChange={(e) => setFilters(prev => ({ ...prev, eventType: e.target.value }))}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="device_threat_detected">Device Threats</MenuItem>
                  <MenuItem value="port_opened">Port Changes</MenuItem>
                  <MenuItem value="port_scan">Port Scans</MenuItem>
                  <MenuItem value="unauthorized_access">Unauthorized Access</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={2}>
              <Box display="flex" gap={1}>
                <ButtonGroup variant="outlined" size="small">
                  <Button
                    startIcon={<ExportIcon />}
                    onClick={() => handleExport('json')}
                    disabled={!filteredEvents.length}
                  >
                    JSON
                  </Button>
                  <Button
                    onClick={() => handleExport('txt')}
                    disabled={!filteredEvents.length}
                  >
                    TXT
                  </Button>
                </ButtonGroup>
                <Button
                  variant={viewMode === 'table' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setViewMode(viewMode === 'table' ? 'cards' : 'table')}
                >
                  {viewMode === 'table' ? 'Cards' : 'Table'}
                </Button>
              </Box>
            </Grid>
          </Grid>
      </Paper>

      {/* Events Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {filteredEvents.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <SecurityIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No security events found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {filters.search || filters.severity !== 'all' || filters.status !== 'all' 
                  ? 'Try adjusting your filters'
                  : 'Your network is secure'}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Security Events ({filteredEvents.length})
              </Typography>
              {loading && <CircularProgress size={20} />}
            </Box>

            {viewMode === 'table' ? (
              // Table View
              <TableContainer component={Paper} sx={{ maxHeight: 600, borderRadius: 2 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: '#2c3e50' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold', backgroundColor: '#2c3e50', fontSize: '0.9rem' }}>Severity</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold', backgroundColor: '#2c3e50', fontSize: '0.9rem' }}>Event</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold', backgroundColor: '#2c3e50', fontSize: '0.9rem' }}>Device</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold', backgroundColor: '#2c3e50', fontSize: '0.9rem' }}>Time</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold', backgroundColor: '#2c3e50', fontSize: '0.9rem' }}>Status</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold', backgroundColor: '#2c3e50', fontSize: '0.9rem' }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredEvents.map((event, index) => {
                      const severityInfo = getSeverityInfo(event.severity);
                      return (
                        <TableRow 
                          key={event.id}
                          sx={{ 
                            backgroundColor: event.is_resolved 
                              ? '#f0f8f0' 
                              : index % 2 === 0 
                                ? '#fafbfc' 
                                : '#f5f7fa',
                            '&:hover': { 
                              backgroundColor: '#e8f4fd',
                              transform: 'scale(1.001)',
                              transition: 'all 0.2s ease-in-out',
                              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                            },
                            borderLeft: `4px solid ${getSeverityInfo(event.severity).color}`,
                            '& td': { 
                              borderBottom: '1px solid #e1e5e9',
                              padding: '12px 16px'
                            }
                          }}
                        >
                          <TableCell>
                            <Chip
                              icon={severityInfo.icon}
                              label={event.severity_display || event.severity}
                              size="small"
                              sx={{
                                backgroundColor: severityInfo.bgColor,
                                color: severityInfo.color,
                                fontWeight: 'bold'
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium" sx={{ color: '#1a1a1a' }}>
                              {event.title}
                            </Typography>
                            <Typography variant="caption" sx={{ color: '#666666' }}>
                              {event.event_type_display || event.event_type}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ color: '#1a1a1a' }}>
                              {event.source_device_ip || event.target_device_ip || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ color: '#1a1a1a' }}>
                              {format(new Date(event.timestamp), 'MMM dd, HH:mm')}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={event.is_resolved ? 'Resolved' : 'Active'}
                              size="small"
                              color={event.is_resolved ? 'success' : 'error'}
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Box display="flex" gap={1}>
                              <Tooltip title="View Details">
                                <IconButton
                                  size="small"
                                  onClick={() => {
                                    setSelectedEvent(event);
                                    setDialogOpen(true);
                                  }}
                                  sx={{
                                    backgroundColor: '#e3f2fd',
                                    color: '#1976d2',
                                    '&:hover': {
                                      backgroundColor: '#bbdefb',
                                      transform: 'scale(1.1)'
                                    },
                                    transition: 'all 0.2s ease-in-out'
                                  }}
                                >
                                  <InfoIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              {!event.is_resolved && (
                                <>
                                  <Tooltip title="Investigate">
                                    <IconButton
                                      size="small"
                                      onClick={() => handleInvestigate(event.id)}
                                      disabled={actionLoading}
                                      sx={{
                                        backgroundColor: '#fff3e0',
                                        color: '#f57c00',
                                        '&:hover': {
                                          backgroundColor: '#ffe0b2',
                                          transform: 'scale(1.1)'
                                        },
                                        transition: 'all 0.2s ease-in-out'
                                      }}
                                    >
                                      <InvestigateIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="Resolve">
                                    <IconButton
                                      size="small"
                                      onClick={() => handleResolve(event.id)}
                                      disabled={actionLoading}
                                      sx={{
                                        backgroundColor: '#e8f5e8',
                                        color: '#2e7d32',
                                        '&:hover': {
                                          backgroundColor: '#c8e6c9',
                                          transform: 'scale(1.1)'
                                        },
                                        transition: 'all 0.2s ease-in-out'
                                      }}
                                    >
                                      <ResolveIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                  {(event.severity === 'critical' || event.severity === 'high') && (
                                    <Tooltip title="Block Threat">
                                      <IconButton
                                        size="small"
                                        onClick={() => handleBlock(event.id)}
                                        disabled={actionLoading}
                                        sx={{
                                          backgroundColor: '#ffebee',
                                          color: '#d32f2f',
                                          '&:hover': {
                                            backgroundColor: '#ffcdd2',
                                            transform: 'scale(1.1)'
                                          },
                                          transition: 'all 0.2s ease-in-out'
                                        }}
                                      >
                                        <BlockIcon fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  )}
                                </>
                              )}
                            </Box>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              // Cards View
              <Grid container spacing={3}>
                {filteredEvents.map((event) => {
                  const severityInfo = getSeverityInfo(event.severity);
                  return (
                    <Grid item xs={12} sm={6} md={4} key={event.id}>
                      <Card 
                        elevation={2}
                        sx={{ 
                          height: '100%',
                          border: `2px solid ${severityInfo.color}`,
                          opacity: event.is_resolved ? 0.8 : 1,
                          transition: 'all 0.3s ease',
                          '&:hover': { 
                            elevation: 4,
                            transform: 'translateY(-2px)',
                            boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
                          },
                          borderRadius: 2,
                          backgroundColor: event.is_resolved 
                            ? '#f8f9fa'
                            : '#ffffff',
                          '& .MuiTypography-root': {
                            color: '#1a1a1a !important'
                          },
                          '& .MuiTypography-caption': {
                            color: '#666666 !important'
                          }
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                            <Chip
                              icon={severityInfo.icon}
                              label={event.severity_display || event.severity}
                              size="small"
                              sx={{
                                backgroundColor: severityInfo.bgColor,
                                color: severityInfo.color,
                                fontWeight: 'bold',
                                fontSize: '0.75rem'
                              }}
                            />
                            <Chip
                              label={event.is_resolved ? 'Resolved' : 'Active'}
                              size="small"
                              color={event.is_resolved ? 'success' : 'error'}
                              variant="outlined"
                              sx={{ fontWeight: 'bold' }}
                            />
                          </Box>
                          
                          <Typography 
                            variant="h6" 
                            gutterBottom 
                            sx={{ 
                              color: '#1a1a1a', 
                              fontWeight: 'bold',
                              fontSize: '1.1rem',
                              lineHeight: 1.3
                            }}
                          >
                            {event.title}
                          </Typography>
                          
                          <Typography 
                            variant="body2" 
                            gutterBottom 
                            sx={{ 
                              color: '#424242', 
                              minHeight: '40px',
                              fontSize: '0.875rem',
                              lineHeight: 1.4
                            }}
                          >
                            {event.description && event.description.length > 100 
                              ? `${event.description.substring(0, 100)}...`
                              : event.description || 'No description available'
                            }
                          </Typography>
                          
                          <Box display="flex" justifyContent="space-between" alignItems="center" mt={2} mb={2}>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                color: '#666666', 
                                fontWeight: 600,
                                fontSize: '0.75rem'
                              }}
                            >
                              📅 {format(new Date(event.timestamp), 'MMM dd, HH:mm')}
                            </Typography>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                color: '#666666', 
                                fontWeight: 600,
                                fontSize: '0.75rem'
                              }}
                            >
                              🌐 {event.source_device_ip || event.target_device_ip || 'N/A'}
                            </Typography>
                          </Box>
                          
                          <Box display="flex" justifyContent="flex-end" gap={1} mt={2}>
                            <Button
                              size="small"
                              onClick={() => {
                                setSelectedEvent(event);
                                setDialogOpen(true);
                              }}
                              sx={{
                                backgroundColor: '#e3f2fd',
                                color: '#1976d2',
                                fontWeight: 'bold',
                                fontSize: '0.75rem',
                                '&:hover': {
                                  backgroundColor: '#bbdefb',
                                  transform: 'scale(1.05)'
                                },
                                transition: 'all 0.2s ease-in-out'
                              }}
                            >
                              Details
                            </Button>
                            {!event.is_resolved && (
                              <>
                                <Button
                                  size="small"
                                  onClick={() => handleInvestigate(event.id)}
                                  disabled={actionLoading}
                                  sx={{
                                    backgroundColor: '#fff3e0',
                                    color: '#f57c00',
                                    fontWeight: 'bold',
                                    fontSize: '0.75rem',
                                    '&:hover': {
                                      backgroundColor: '#ffe0b2',
                                      transform: 'scale(1.05)'
                                    },
                                    transition: 'all 0.2s ease-in-out'
                                  }}
                                >
                                  Investigate
                                </Button>
                                <Button
                                  size="small"
                                  onClick={() => handleResolve(event.id)}
                                  disabled={actionLoading}
                                  sx={{
                                    backgroundColor: '#e8f5e8',
                                    color: '#2e7d32',
                                    fontWeight: 'bold',
                                    fontSize: '0.75rem',
                                    '&:hover': {
                                      backgroundColor: '#c8e6c9',
                                      transform: 'scale(1.05)'
                                    },
                                    transition: 'all 0.2s ease-in-out'
                                  }}
                                >
                                  Resolve
                                </Button>
                              </>
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* Event Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: '#ffffff',
            '& .MuiTypography-root': {
              color: '#1a1a1a !important'
            },
            '& .MuiListItemText-primary': {
              color: '#1a1a1a !important',
              fontWeight: 'bold'
            },
            '& .MuiListItemText-secondary': {
              color: '#424242 !important'
            }
          }
        }}
      >
        {selectedEvent && (
          <>
            <DialogTitle>
              <Box display="flex" alignItems="center" gap={2}>
                {getSeverityInfo(selectedEvent.severity).icon}
                <Box>
                  <Typography variant="h6">
                    {selectedEvent.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Event ID: {selectedEvent.id} | {selectedEvent.event_type_display || selectedEvent.event_type}
                  </Typography>
                </Box>
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Event Details
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <WarningIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Severity"
                        secondary={selectedEvent.severity_display || selectedEvent.severity}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <TimelineIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Timestamp"
                        secondary={format(new Date(selectedEvent.timestamp), 'PPpp')}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Status"
                        secondary={selectedEvent.is_resolved ? 'Resolved' : 'Active'}
                      />
                    </ListItem>
                  </List>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Network Information
                  </Typography>
                  <List dense>
                    {selectedEvent.source_device_ip && (
                      <ListItem>
                        <ListItemIcon>
                          <NetworkIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Source Device"
                          secondary={selectedEvent.source_device_ip}
                        />
                      </ListItem>
                    )}
                    {selectedEvent.target_device_ip && (
                      <ListItem>
                        <ListItemIcon>
                          <NetworkIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Target Device"
                          secondary={selectedEvent.target_device_ip}
                        />
                      </ListItem>
                    )}
                  </List>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    p: 2, 
                    backgroundColor: '#f5f5f5', 
                    borderRadius: 1,
                    color: '#1a1a1a !important',
                    fontSize: '0.875rem',
                    lineHeight: 1.5
                  }}>
                    {selectedEvent.description || 'No description available'}
                  </Typography>
                </Grid>
                
                {selectedEvent.details && Object.keys(selectedEvent.details).length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Additional Details
                    </Typography>
                    <Box sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                      <pre style={{ 
                        fontSize: '0.875rem', 
                        margin: 0, 
                        whiteSpace: 'pre-wrap',
                        color: '#1a1a1a',
                        fontFamily: 'monospace'
                      }}>
                        {JSON.stringify(selectedEvent.details, null, 2)}
                      </pre>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            
            <DialogActions>
              <Button onClick={() => setDialogOpen(false)}>
                Close
              </Button>
              {!selectedEvent.is_resolved && (
                <>
                  <Button
                    onClick={() => {
                      handleInvestigate(selectedEvent.id);
                      setDialogOpen(false);
                    }}
                    disabled={actionLoading}
                  >
                    Investigate
                  </Button>
                  <Button
                    onClick={() => {
                      handleResolve(selectedEvent.id);
                      setDialogOpen(false);
                    }}
                    color="success"
                    disabled={actionLoading}
                  >
                    Resolve
                  </Button>
                  {(selectedEvent.severity === 'critical' || selectedEvent.severity === 'high') && (
                    <Button
                      onClick={() => {
                        handleBlock(selectedEvent.id);
                        setDialogOpen(false);
                      }}
                      color="error"
                      disabled={actionLoading}
                    >
                      Block Threat
                    </Button>
                  )}
                </>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default SecurityEvents;