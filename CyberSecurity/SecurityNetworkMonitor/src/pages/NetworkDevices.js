import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Button,
  IconButton,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
  Badge,
  Tooltip,
  LinearProgress,
  Alert,
  Snackbar,
  Paper,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Search,
  Computer,
  Router,
  Smartphone,
  Print,
  DevicesOther,
  Storage,
  Wifi,
  Refresh,
  PlayArrow,
  Stop,
  Scanner,
  NetworkCheck,
  Circle,
  Speed,
  Info,
  ContentCopy,
  Security,
  NetworkWifi,
  Schedule,
  Memory
} from '@mui/icons-material';
import useRealTimeDevices from '../hooks/useRealTimeDevices';

const NetworkDevices = () => {
  const {
    devices,
    networkStats,
    connectionStatus,
    notifications,
    onlineDevices,
    offlineDevices,
    devicesByType,
    monitoringStatus,
    toggleDeviceMonitoring,
    pingDevice,
    scanDevicePorts,
    startNetworkDiscovery,
    clearAllDevices,
    startGlobalMonitoring,
    stopGlobalMonitoring,
    reconnect
  } = useRealTimeDevices();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('last_seen');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [deviceInfoOpen, setDeviceInfoOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [clearConfirmOpen, setClearConfirmOpen] = useState(false);

  // Device type icons
  const getDeviceIcon = (deviceType) => {
    const iconMap = {
      computer: Computer,
      router: Router,
      mobile: Smartphone,
      printer: Print,
      server: Storage,
      iot: DevicesOther,
      switch: Router,
      unknown: DevicesOther
    };
    const IconComponent = iconMap[deviceType] || DevicesOther;
    return <IconComponent />;
  };

  // Status colors
  const getStatusColor = (status) => {
    const colorMap = {
      online: '#4caf50',
      offline: '#f44336',
      unknown: '#ff9800'
    };
    return colorMap[status] || '#9e9e9e';
  };

  // Filter and sort devices
  const filteredDevices = useMemo(() => {
    let filtered = devices;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(device =>
        device.ip_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.mac_address.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(device => device.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(device => device.device_type === typeFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'ip_address':
          return a.ip_address.localeCompare(b.ip_address);
        case 'hostname':
          return a.hostname.localeCompare(b.hostname);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'device_type':
          return a.device_type.localeCompare(b.device_type);
        case 'last_seen':
        default:
          return new Date(b.last_seen) - new Date(a.last_seen);
      }
    });

    return filtered;
  }, [devices, searchTerm, statusFilter, typeFilter, sortBy]);

  const handlePingDevice = async (deviceId) => {
    try {
      await pingDevice(deviceId);
    } catch (error) {
      console.error('Ping failed:', error);
    }
  };

  const handleScanPorts = async (deviceId) => {
    try {
      await scanDevicePorts(deviceId);
    } catch (error) {
      console.error('Port scan failed:', error);
    }
  };

  const handleDeviceInfo = (device) => {
    setSelectedDevice(device);
    setDeviceInfoOpen(true);
  };

  const handleCloseDeviceInfo = () => {
    setDeviceInfoOpen(false);
    setSelectedDevice(null);
  };

  const handleClearDevices = async () => {
    try {
      await clearAllDevices();
      setClearConfirmOpen(false);
    } catch (error) {
      console.error('Clear devices failed:', error);
    }
  };

  const copyDeviceInfo = () => {
    if (!selectedDevice) return;

    const deviceInfo = {
      'Basic Information': {
        'IP Address': selectedDevice.ip_address,
        'MAC Address': selectedDevice.mac_address || 'Unknown',
        'Hostname': selectedDevice.hostname || 'Unknown',
        'Device Type': selectedDevice.device_type,
        'Manufacturer': selectedDevice.manufacturer || 'Unknown',
        'Status': selectedDevice.status,
        'Response Time': selectedDevice.response_time ? `${selectedDevice.response_time}ms` : 'N/A'
      },
      'Network Statistics': {
        'Uptime': selectedDevice.uptime_percentage != null ? `${Math.round(selectedDevice.uptime_percentage)}%` : '0%',
        'Packet Loss': selectedDevice.packet_loss_rate != null ? `${selectedDevice.packet_loss_rate.toFixed(2)}%` : '0%',
        'Average Response Time': selectedDevice.avg_response_time ? `${selectedDevice.avg_response_time.toFixed(2)}ms` : 'N/A',
        'Ping Success Count': selectedDevice.ping_success_count || 0,
        'Ping Failure Count': selectedDevice.ping_failure_count || 0,
        'Last Ping': selectedDevice.last_ping_time ? new Date(selectedDevice.last_ping_time).toLocaleString() : 'Never'
      },
      'Port Information': {
        'Open Ports Count': selectedDevice.open_ports?.length || 0,
        'Open Ports': selectedDevice.open_ports?.map(p => `${p.port}/${p.protocol} (${p.service})`).join(', ') || 'None detected'
      },
      'Monitoring': {
        'First Seen': new Date(selectedDevice.first_seen).toLocaleString(),
        'Last Seen': new Date(selectedDevice.last_seen).toLocaleString(),
        'Is Monitored': selectedDevice.is_monitored ? 'Yes' : 'No'
      }
    };

    let textOutput = `=== DEVICE INFORMATION REPORT ===\n`;
    textOutput += `Generated: ${new Date().toLocaleString()}\n\n`;

    Object.entries(deviceInfo).forEach(([section, data]) => {
      textOutput += `${section.toUpperCase()}\n`;
      textOutput += '='.repeat(section.length) + '\n';
      Object.entries(data).forEach(([key, value]) => {
        textOutput += `${key}: ${value}\n`;
      });
      textOutput += '\n';
    });

    navigator.clipboard.writeText(textOutput).then(() => {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 3000);
    }).catch(err => {
      console.error('Failed to copy to clipboard:', err);
    });
  };

  const formatLastSeen = (lastSeen) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const DeviceCard = ({ device }) => (
    <Card 
      elevation={2}
      sx={{ 
        height: '100%',
        border: device.status === 'online' ? '2px solid #4caf50' : 
               device.status === 'offline' ? '2px solid #f44336' : '2px solid #ff9800',
        transition: 'all 0.3s ease',
        '&:hover': {
          elevation: 4,
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent>
        {/* Status indicator and device icon */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Badge
            badgeContent={
              <Circle 
                sx={{ 
                  color: getStatusColor(device.status),
                  fontSize: '12px'
                }} 
              />
            }
            anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {getDeviceIcon(device.device_type)}
            </Avatar>
          </Badge>
          
          {device.is_scanning && (
            <Box sx={{ width: '100%', ml: 2 }}>
              <LinearProgress 
                variant="determinate" 
                value={device.scan_progress} 
                size="small"
              />
              <Typography variant="caption" color="text.secondary">
                Scanning... {device.scan_progress}%
              </Typography>
            </Box>
          )}
        </Box>

        {/* Device information */}
        <Typography variant="h6" component="h3" gutterBottom>
          {device.hostname || 'Unknown Device'}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {device.ip_address}
        </Typography>
        
        {device.mac_address && (
          <Typography variant="caption" color="text.secondary" display="block">
            MAC: {device.mac_address}
          </Typography>
        )}

        {/* Status and metrics */}
        <Box mt={2} mb={2}>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip 
              label={device.status}
              color={device.status === 'online' ? 'success' : device.status === 'offline' ? 'error' : 'warning'}
              size="small"
            />
            <Chip 
              label={device.device_type}
              variant="outlined"
              size="small"
            />
            {device.response_time && (
              <Chip 
                label={`${Math.round(device.response_time)}ms`}
                icon={<Speed />}
                size="small"
                variant="outlined"
              />
            )}
          </Stack>
        </Box>

        {/* Additional metrics */}
        <Box mt={2}>
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Last Seen
              </Typography>
              <Typography variant="body2">
                {formatLastSeen(device.last_seen)}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Uptime
              </Typography>
              <Typography variant="body2">
                {device.uptime_percentage != null ? Math.round(device.uptime_percentage) : 0}%
              </Typography>
            </Grid>
            {device.open_ports && device.open_ports.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Open Ports ({device.open_ports.length})
                </Typography>
                <Typography variant="body2">
                  {device.open_ports.slice(0, 3).map(p => p.port).join(', ')}
                  {device.open_ports.length > 3 && '...'}
                </Typography>
              </Grid>
            )}
          </Grid>
        </Box>
      </CardContent>

      <CardActions>
        <Tooltip title="Device Information">
          <IconButton onClick={() => handleDeviceInfo(device)} size="small">
            <Info />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Ping Device">
          <IconButton onClick={() => handlePingDevice(device.id)} size="small">
            <NetworkCheck />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Scan Ports">
          <IconButton 
            onClick={() => handleScanPorts(device.id)} 
            size="small"
            disabled={device.is_scanning}
          >
            <Scanner />
          </IconButton>
        </Tooltip>
        
        <Tooltip title={device.monitor_enabled ? 'Disable Monitoring' : 'Enable Monitoring'}>
          <IconButton 
            onClick={() => toggleDeviceMonitoring(device.id)} 
            size="small"
            color={device.monitor_enabled ? 'primary' : 'default'}
          >
            {device.monitor_enabled ? <Stop /> : <PlayArrow />}
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Network Devices
        </Typography>
        
        <Box display="flex" gap={2}>
          <Chip 
            label={`Connected: ${connectionStatus}`}
            color={connectionStatus === 'connected' ? 'success' : 'error'}
            icon={<Circle />}
          />
          <Chip 
            label={`Monitoring: ${monitoringStatus === 'active' ? 'Active' : monitoringStatus === 'inactive' ? 'Stopped' : 'Unknown'}`}
            color={monitoringStatus === 'active' ? 'success' : monitoringStatus === 'inactive' ? 'warning' : 'default'}
            icon={monitoringStatus === 'active' ? <PlayArrow /> : <Stop />}
          />
          {connectionStatus !== 'connected' && (
            <Button onClick={reconnect} startIcon={<Refresh />}>
              Reconnect
            </Button>
          )}
          {monitoringStatus === 'active' ? (
            <Button 
              onClick={stopGlobalMonitoring}
              startIcon={<Stop />}
              variant="outlined"
              color="warning"
            >
              Stop Monitoring
            </Button>
          ) : (
            <Button 
              onClick={startGlobalMonitoring}
              startIcon={<PlayArrow />}
              variant="outlined"
              color="success"
            >
              Start Monitoring
            </Button>
          )}
          <Button 
            onClick={() => setClearConfirmOpen(true)}
            startIcon={<Stop />}
            variant="outlined"
            color="error"
            disabled={devices.length === 0}
          >
            Clear Devices
          </Button>
          <Button 
            onClick={startNetworkDiscovery}
            startIcon={<Wifi />}
            variant="contained"
          >
            Start Discovery
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {devices.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Devices
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">
              {onlineDevices.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Online
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="error.main">
              {offlineDevices.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Offline
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main">
              {networkStats.new_devices_today}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              New Today
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              placeholder="Search devices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              size="small"
            />
          </Grid>
          
          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="online">Online</MenuItem>
                <MenuItem value="offline">Offline</MenuItem>
                <MenuItem value="unknown">Unknown</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                label="Type"
              >
                <MenuItem value="all">All Types</MenuItem>
                {Object.keys(devicesByType).map(type => (
                  <MenuItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)} ({devicesByType[type]})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                label="Sort By"
              >
                <MenuItem value="last_seen">Last Seen</MenuItem>
                <MenuItem value="ip_address">IP Address</MenuItem>
                <MenuItem value="hostname">Hostname</MenuItem>
                <MenuItem value="status">Status</MenuItem>
                <MenuItem value="device_type">Type</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Typography variant="body2" color="text.secondary">
              Showing {filteredDevices.length} of {devices.length} devices
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Device Grid */}
      {filteredDevices.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No devices found
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Try adjusting your filters or start a network discovery
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {filteredDevices.map((device) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={device.id}>
              <DeviceCard device={device} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Notifications */}
      {notifications.map((notification) => (
        <Snackbar
          key={notification.id}
          open={true}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert 
            severity={notification.type === 'error' ? 'error' : 
                    notification.type === 'warning' ? 'warning' :
                    notification.type === 'success' ? 'success' : 'info'}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}

      {/* Device Information Dialog */}
      <Dialog 
        open={deviceInfoOpen} 
        onClose={handleCloseDeviceInfo}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            {selectedDevice && getDeviceIcon(selectedDevice.device_type)}
            <Box>
              <Typography variant="h6">
                Device Information
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedDevice?.ip_address} - {selectedDevice?.hostname || 'Unknown'}
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedDevice && (
            <Box>
              {/* Basic Information */}
              <Typography variant="h6" gutterBottom sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Computer /> Basic Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><NetworkWifi /></ListItemIcon>
                  <ListItemText primary="IP Address" secondary={selectedDevice.ip_address} />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Memory /></ListItemIcon>
                  <ListItemText primary="MAC Address" secondary={selectedDevice.mac_address || 'Unknown'} />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Computer /></ListItemIcon>
                  <ListItemText primary="Hostname" secondary={selectedDevice.hostname || 'Unknown'} />
                </ListItem>
                <ListItem>
                  <ListItemIcon><DevicesOther /></ListItemIcon>
                  <ListItemText primary="Device Type" secondary={selectedDevice.device_type} />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Circle sx={{ color: getStatusColor(selectedDevice.status) }} /></ListItemIcon>
                  <ListItemText 
                    primary="Status" 
                    secondary={
                      <Chip 
                        label={selectedDevice.status}
                        color={selectedDevice.status === 'online' ? 'success' : selectedDevice.status === 'offline' ? 'error' : 'warning'}
                        size="small"
                      />
                    } 
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              {/* Network Statistics */}
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Speed /> Network Statistics
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><Schedule /></ListItemIcon>
                  <ListItemText 
                    primary="Uptime" 
                    secondary={`${selectedDevice.uptime_percentage != null ? Math.round(selectedDevice.uptime_percentage) : 0}%`} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><NetworkCheck /></ListItemIcon>
                  <ListItemText 
                    primary="Response Time" 
                    secondary={selectedDevice.response_time ? `${selectedDevice.response_time}ms` : 'N/A'} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Speed /></ListItemIcon>
                  <ListItemText 
                    primary="Average Response Time" 
                    secondary={selectedDevice.avg_response_time ? `${selectedDevice.avg_response_time.toFixed(2)}ms` : 'N/A'} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Security /></ListItemIcon>
                  <ListItemText 
                    primary="Packet Loss" 
                    secondary={`${selectedDevice.packet_loss_rate != null ? selectedDevice.packet_loss_rate.toFixed(2) : 0}%`} 
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              {/* Port Information */}
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Scanner /> Port Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><Scanner /></ListItemIcon>
                  <ListItemText 
                    primary="Open Ports" 
                    secondary={`${selectedDevice.open_ports?.length || 0} ports detected`} 
                  />
                </ListItem>
                {selectedDevice.open_ports && selectedDevice.open_ports.length > 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="Port Details" 
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {selectedDevice.open_ports.map((port, index) => (
                            <Chip
                              key={index}
                              label={`${port.port}/${port.protocol} (${port.service})`}
                              size="small"
                              variant="outlined"
                              sx={{ mr: 1, mb: 1 }}
                              color={port.risk_level === 'critical' ? 'error' : 
                                     port.risk_level === 'high' ? 'warning' : 'default'}
                            />
                          ))}
                        </Box>
                      } 
                    />
                  </ListItem>
                )}
              </List>

              <Divider sx={{ my: 2 }} />

              {/* Monitoring Information */}
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Schedule /> Monitoring Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><Schedule /></ListItemIcon>
                  <ListItemText 
                    primary="First Seen" 
                    secondary={new Date(selectedDevice.first_seen).toLocaleString()} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Schedule /></ListItemIcon>
                  <ListItemText 
                    primary="Last Seen" 
                    secondary={new Date(selectedDevice.last_seen).toLocaleString()} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><NetworkCheck /></ListItemIcon>
                  <ListItemText 
                    primary="Ping Statistics" 
                    secondary={`Success: ${selectedDevice.ping_success_count || 0}, Failed: ${selectedDevice.ping_failure_count || 0}`} 
                  />
                </ListItem>
              </List>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={copyDeviceInfo} startIcon={<ContentCopy />}>
            Copy to Clipboard
          </Button>
          <Button onClick={handleCloseDeviceInfo}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Copy Success Notification */}
      <Snackbar
        open={copySuccess}
        autoHideDuration={3000}
        onClose={() => setCopySuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success">
          Device information copied to clipboard!
        </Alert>
      </Snackbar>

      {/* Clear Devices Confirmation Dialog */}
      <Dialog
        open={clearConfirmOpen}
        onClose={() => setClearConfirmOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <Stop color="error" />
            <Typography variant="h6">
              Clear All Devices
            </Typography>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action cannot be undone!
          </Alert>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to clear all devices from the list?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This will remove all {devices.length} devices and their associated data including:
          </Typography>
          <List dense sx={{ mt: 1 }}>
            <ListItem>
              <ListItemText primary="• Device information and status history" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Port scan results" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Security events and alerts" />
            </ListItem>
          </List>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            You can start fresh by running a new network discovery after clearing.
          </Typography>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setClearConfirmOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleClearDevices}
            color="error"
            variant="contained"
            startIcon={<Stop />}
          >
            Clear All Devices
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NetworkDevices; 