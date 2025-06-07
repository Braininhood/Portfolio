import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  LinearProgress,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Add,
  Delete,
  Visibility,
  Download,
  Schedule,
  Security,
  NetworkCheck,
  Assessment,
  Settings,
  Search,
  CheckCircle,
  Error,
  Computer,
  Router,
  Shield,
} from '@mui/icons-material';
import { api } from '../services/api';

// Validation function for target range
const isValidTargetRange = (value) => {
  if (!value || value.trim() === '') return false;
  
  const cidrPattern = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
  const rangeWithSpacesPattern = /^(\d{1,3}\.){3}\d{1,3}\s*-\s*(\d{1,3}\.){3}\d{1,3}$/;
  const shortRangePattern = /^(\d{1,3}\.){3}\d{1,3}\s*-\s*\d{1,3}$/;
  const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
  
  return cidrPattern.test(value.trim()) || 
         rangeWithSpacesPattern.test(value.trim()) || 
         shortRangePattern.test(value.trim()) || 
         ipPattern.test(value.trim()) ||
         (value.includes(',') && value.split(',').every(ip => ipPattern.test(ip.trim())));
};

const NetworkScans = () => {
  // State management
  const [scans, setScans] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedScan, setSelectedScan] = useState(null);
  const [selectedScanTab, setSelectedScanTab] = useState(0);
  const [activeStep, setActiveStep] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  
  // Notification state
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  
  // Form states
  const [scanForm, setScanForm] = useState({
    name: '',
    description: '',
    scan_type: 'discovery',
    priority: 'normal',
    target_range: '192.168.1.0/24',
    target_ports: '',
    exclude_hosts: '',
    scan_techniques: ['tcp_connect'],
    timing_template: 'normal',
    max_retries: 3,
    timeout_per_host: 30,
    max_parallel_hosts: 50,
    max_parallel_ports: 100,
    randomize_hosts: true,
    fragment_packets: false,
    spoof_source_ip: '',
    service_detection: true,
    version_detection: false,
    os_detection: false,
    script_scanning: false,
    aggressive_scan: false,
    is_scheduled: false,
    schedule_cron: '',
    auto_retry_on_failure: false,
    max_auto_retries: 3,
    generate_report: true,
    report_format: 'json',
    tags: [],
    metadata: {},
  });

  // Load data
  const loadScans = useCallback(async () => {
    try {
      const response = await api.getNetworkScans();
      setScans(response.results || response);
    } catch (error) {
      console.error('Error loading scans:', error);
      showNotification('Failed to load scans', 'error');
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const response = await api.getScanTemplates();
      setTemplates(response.results || response);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([loadScans(), loadTemplates()]);
      setLoading(false);
    };
    loadData();
  }, [loadScans, loadTemplates]);

  // Auto-refresh scans every 5 seconds (but not when dialog is open)
  useEffect(() => {
    const interval = setInterval(() => {
      // Don't auto-refresh if any dialog is open to prevent form disruption
      if (!createDialogOpen && !detailsDialogOpen && !templateDialogOpen) {
        loadScans();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [loadScans, createDialogOpen, detailsDialogOpen, templateDialogOpen]);

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  // Scan management functions
  const handleCreateScan = async () => {
    try {
      await api.createNetworkScan(scanForm);
      showNotification('Scan created successfully', 'success');
      setCreateDialogOpen(false);
      setScanForm({
            name: '',
    description: '',
    scan_type: 'discovery',
    priority: 'normal',
    target_range: '192.168.1.0/24',
    target_ports: '',
    exclude_hosts: '',
    scan_techniques: ['tcp_connect'],
    timing_template: 'normal',
    max_retries: 3,
    timeout_per_host: 30,
    max_parallel_hosts: 50,
    max_parallel_ports: 100,
    randomize_hosts: true,
    fragment_packets: false,
    spoof_source_ip: '',
    service_detection: true,
    version_detection: false,
    os_detection: false,
    script_scanning: false,
    aggressive_scan: false,
    is_scheduled: false,
    schedule_cron: '',
    auto_retry_on_failure: false,
    max_auto_retries: 3,
    generate_report: true,
    report_format: 'json',
    tags: [],
    metadata: {},
      });
      loadScans();
    } catch (error) {
      console.error('Error creating scan:', error);
      showNotification('Failed to create scan', 'error');
    }
  };

  const handleStartScan = async (scanId) => {
    try {
      await api.startNetworkScan(scanId);
      showNotification('Scan started successfully', 'success');
      loadScans();
    } catch (error) {
      console.error('Error starting scan:', error);
      showNotification('Failed to start scan', 'error');
    }
  };

  const handlePauseScan = async (scanId) => {
    try {
      await api.pauseNetworkScan(scanId);
      showNotification('Scan paused successfully', 'success');
      loadScans();
    } catch (error) {
      console.error('Error pausing scan:', error);
      showNotification('Failed to pause scan', 'error');
    }
  };

  const handleStopScan = async (scanId) => {
    try {
      await api.stopNetworkScan(scanId);
      showNotification('Scan stopped successfully', 'success');
      loadScans();
    } catch (error) {
      console.error('Error stopping scan:', error);
      showNotification('Failed to stop scan', 'error');
    }
  };

  const handleDeleteScan = async (scanId) => {
    if (window.confirm('Are you sure you want to delete this scan?')) {
      try {
        await api.deleteNetworkScan(scanId);
        showNotification('Scan deleted successfully', 'success');
        loadScans();
      } catch (error) {
        console.error('Error deleting scan:', error);
        showNotification('Failed to delete scan', 'error');
      }
    }
  };

  const handleDownloadReport = async (scanId, scanName) => {
    try {
      // Use default format (txt) by not specifying format parameter
      const blob = await api.downloadScanReport(scanId, 'txt');
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${scanName || 'scan'}_report_${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      
      showNotification('Report downloaded successfully', 'success');
    } catch (error) {
      console.error('Error downloading report:', error);
      showNotification('Failed to download report', 'error');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'info';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <PlayArrow />;
      case 'completed': return <CheckCircle />;
      case 'failed': return <Error />;
      case 'cancelled': return <Stop />;
      case 'paused': return <Pause />;
      default: return <Schedule />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'normal': return 'info';
      case 'low': return 'default';
      default: return 'default';
    }
  };

  const getScanTypeIcon = (scanType) => {
    const icons = {
      ping_sweep: <NetworkCheck />,
      port_scan: <Router />,
      service_detection: <Computer />,
      os_fingerprinting: <Computer />,
      vulnerability_scan: <Security />,
      discovery: <Search />,
      stealth_scan: <Shield />,
      comprehensive: <Assessment />,
      custom: <Settings />,
    };
    return icons[scanType] || <Computer />;
  };

  const getRiskColor = (riskScore) => {
    if (riskScore >= 80) return 'error';
    if (riskScore >= 60) return 'warning';
    if (riskScore >= 40) return 'info';
    return 'success';
  };

  // Filter scans
  const filteredScans = scans.filter(scan => {
    const matchesSearch = scan.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scan.target_range?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scan.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || scan.status === statusFilter;
    const matchesType = typeFilter === 'all' || scan.scan_type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // Paginated scans
  const paginatedScans = filteredScans.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  // Statistics
  const scanStats = {
    total: scans.length,
    running: scans.filter(s => s.status === 'running').length,
    completed: scans.filter(s => s.status === 'completed').length,
    failed: scans.filter(s => s.status === 'failed').length,
    pending: scans.filter(s => s.status === 'pending').length,
  };

  // Scan creation form component
  const ScanCreationForm = () => {
    const handleStep = (step) => () => {
      setActiveStep(step);
    };

  return (
      <Box sx={{ minWidth: 600 }}>
        <Stepper activeStep={activeStep} orientation="vertical" nonLinear>
        <Step>
          <StepLabel onClick={handleStep(0)} sx={{ cursor: 'pointer' }}>Basic Configuration</StepLabel>
          <StepContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Scan Name"
                  value={scanForm.name}
                  onChange={(e) => setScanForm({ ...scanForm, name: e.target.value })}
                  placeholder="e.g., Production Network Scan"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Description"
                  value={scanForm.description}
                  onChange={(e) => setScanForm({ ...scanForm, description: e.target.value })}
                  placeholder="Describe the purpose of this scan..."
                />
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth>
                  <InputLabel>Scan Type</InputLabel>
                  <Select
                    value={scanForm.scan_type}
                    onChange={(e) => setScanForm({ ...scanForm, scan_type: e.target.value })}
                    label="Scan Type"
                  >
                    <MenuItem value="ping_sweep">Ping Sweep</MenuItem>
                    <MenuItem value="port_scan">Port Scan</MenuItem>
                    <MenuItem value="service_detection">Service Detection</MenuItem>
                    <MenuItem value="os_fingerprinting">OS Fingerprinting</MenuItem>
                    <MenuItem value="vulnerability_scan">Vulnerability Scan</MenuItem>
                    <MenuItem value="discovery">Network Discovery</MenuItem>
                    <MenuItem value="stealth_scan">Stealth Scan</MenuItem>
                    <MenuItem value="comprehensive">Comprehensive Scan</MenuItem>
                    <MenuItem value="custom">Custom Scan</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={scanForm.priority}
                    onChange={(e) => setScanForm({ ...scanForm, priority: e.target.value })}
                    label="Priority"
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="normal">Normal</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </StepContent>
        </Step>
        
        <Step>
          <StepLabel onClick={handleStep(1)} sx={{ cursor: 'pointer' }}>Target Configuration</StepLabel>
          <StepContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Target Range"
                  value={scanForm.target_range}
                  onChange={(e) => setScanForm({ ...scanForm, target_range: e.target.value })}
                  placeholder="e.g., 192.168.1.0/24, 192.168.1.1 - 192.168.1.50, 192.168.1.1-50"
                  helperText="Supports: CIDR (192.168.1.0/24), Range with spaces (192.168.1.1 - 192.168.1.25), Short range (192.168.1.1-50)"
                  error={scanForm.target_range && !isValidTargetRange(scanForm.target_range)}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Target Ports"
                  value={scanForm.target_ports}
                  onChange={(e) => setScanForm({ ...scanForm, target_ports: e.target.value })}
                  placeholder="22,80,443,1000-2000"
                  helperText="Comma-separated ports or ranges"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Exclude Hosts"
                  value={scanForm.exclude_hosts}
                  onChange={(e) => setScanForm({ ...scanForm, exclude_hosts: e.target.value })}
                  placeholder="192.168.1.1,192.168.1.254"
                  helperText="Comma-separated IPs to exclude"
                />
              </Grid>
            </Grid>
          </StepContent>
        </Step>
        
        <Step>
          <StepLabel onClick={handleStep(2)} sx={{ cursor: 'pointer' }}>Advanced Options</StepLabel>
          <StepContent>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth>
                  <InputLabel>Timing Template</InputLabel>
                  <Select
                    value={scanForm.timing_template}
                    onChange={(e) => setScanForm({ ...scanForm, timing_template: e.target.value })}
                    label="Timing Template"
                  >
                    <MenuItem value="paranoid">Paranoid (T0) - Very Slow</MenuItem>
                    <MenuItem value="sneaky">Sneaky (T1) - Slow</MenuItem>
                    <MenuItem value="polite">Polite (T2) - Slower</MenuItem>
                    <MenuItem value="normal">Normal (T3) - Default</MenuItem>
                    <MenuItem value="aggressive">Aggressive (T4) - Fast</MenuItem>
                    <MenuItem value="insane">Insane (T5) - Very Fast</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Max Parallel Hosts"
                  value={scanForm.max_parallel_hosts}
                  onChange={(e) => setScanForm({ ...scanForm, max_parallel_hosts: parseInt(e.target.value) })}
                  inputProps={{ min: 1, max: 1000 }}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Detection Options</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={3}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={scanForm.service_detection}
                          onChange={(e) => setScanForm({ ...scanForm, service_detection: e.target.checked })}
                        />
                      }
                      label="Service Detection"
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={scanForm.version_detection}
                          onChange={(e) => setScanForm({ ...scanForm, version_detection: e.target.checked })}
                        />
                      }
                      label="Version Detection"
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={scanForm.os_detection}
                          onChange={(e) => setScanForm({ ...scanForm, os_detection: e.target.checked })}
                        />
                      }
                      label="OS Detection"
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={scanForm.script_scanning}
                          onChange={(e) => setScanForm({ ...scanForm, script_scanning: e.target.checked })}
                        />
                      }
                      label="Script Scanning"
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </StepContent>
        </Step>
      </Stepper>
    </Box>
    );
  };

  // Scan details component
  const ScanDetails = ({ scan, activeTab, onTabChange }) => {
    if (!scan) return null;

    return (
      <Box sx={{ minWidth: 800, maxHeight: '80vh', overflow: 'hidden' }}>
        <Tabs value={activeTab} onChange={onTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Overview" />
          <Tab label="Results" />
          <Tab label="Performance" />
          <Tab label="Logs" />
        </Tabs>
        
        <Box sx={{ mt: 2, maxHeight: 'calc(80vh - 120px)', overflow: 'auto' }}>
          {/* Overview Tab */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Scan Information</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Name" secondary={scan.name || 'Unnamed Scan'} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Type" secondary={scan.scan_type?.replace('_', ' ')} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Status" secondary={scan.status} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Target" secondary={scan.target_range} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Ports" secondary={scan.target_ports || 'Default'} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Started" secondary={new Date(scan.started_at).toLocaleString()} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Completed" secondary={scan.completed_at ? new Date(scan.completed_at).toLocaleString() : 'N/A'} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Duration" secondary={scan.duration_formatted || 'N/A'} />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Progress</Typography>
                  <Box sx={{ mb: 2 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={scan.progress_percentage || 0}
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {scan.progress_percentage || 0}% Complete
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Current Phase: {scan.current_phase || 'Completed'}
                  </Typography>
                  {scan.status === 'running' && scan.current_target && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Current Target: {scan.current_target}
                    </Typography>
                  )}
                </Paper>
              </Grid>
              
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Results Summary</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="primary">
                          {scan.total_hosts_scanned || 0}
                        </Typography>
                        <Typography variant="body2">Hosts Scanned</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="success.main">
                          {scan.hosts_up || 0}
                        </Typography>
                        <Typography variant="body2">Hosts Up</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="info.main">
                          {scan.open_ports_found || 0}
                        </Typography>
                        <Typography variant="body2">Open Ports</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color={getRiskColor(scan.risk_score || 0)}>
                          {scan.risk_score || 0}
                        </Typography>
                        <Typography variant="body2">Risk Score</Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  {(scan.services_detected > 0 || scan.vulnerabilities_found > 0) && (
                    <Box sx={{ mt: 2 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Box textAlign="center">
                            <Typography variant="h5" color="warning.main">
                              {scan.services_detected || 0}
                            </Typography>
                            <Typography variant="body2">Services Detected</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box textAlign="center">
                            <Typography variant="h5" color="error.main">
                              {scan.vulnerabilities_found || 0}
                            </Typography>
                            <Typography variant="body2">Vulnerabilities</Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Results Tab */}
          {activeTab === 1 && (
    <Box>
              {scan.status !== 'completed' ? (
                <Paper sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="h6" color="text.secondary">
                    Scan results will be available once the scan completes
      </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Current status: {scan.status}
      </Typography>
                </Paper>
              ) : (
                <Grid container spacing={3}>
                  {/* Host Results */}
                  <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="h6" gutterBottom>Discovered Hosts</Typography>
                      {scan.host_results && scan.host_results.length > 0 ? (
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>IP Address</TableCell>
                              <TableCell>Hostname</TableCell>
                              <TableCell>Status</TableCell>
                              <TableCell>Response Time</TableCell>
                              <TableCell>Open Ports</TableCell>
                              <TableCell>Services</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {scan.host_results.map((host, index) => (
                              <TableRow key={index}>
                                <TableCell>{host.ip}</TableCell>
                                <TableCell>{host.hostname || 'N/A'}</TableCell>
                                <TableCell>
                                  <Chip 
                                    label={host.status} 
                                    color={host.status === 'up' ? 'success' : 'default'}
                                    size="small"
                                  />
                                </TableCell>
                                <TableCell>{host.response_time ? `${host.response_time.toFixed(2)}ms` : 'N/A'}</TableCell>
                                <TableCell>{host.ports_found || 0}</TableCell>
                                <TableCell>{host.services_found || 0}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      ) : (
                        <Typography color="text.secondary">No hosts discovered</Typography>
                      )}
                    </Paper>
                  </Grid>

                  {/* Port Results */}
                  {scan.port_results && scan.port_results.length > 0 && (
                    <Grid item xs={12}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>Open Ports</Typography>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Host</TableCell>
                              <TableCell>Port</TableCell>
                              <TableCell>Protocol</TableCell>
                              <TableCell>Service</TableCell>
                              <TableCell>Risk Level</TableCell>
                              <TableCell>Banner</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {scan.port_results.slice(0, 50).map((port, index) => (
                              <TableRow key={index}>
                                <TableCell>{port.ip}</TableCell>
                                <TableCell>{port.port}</TableCell>
                                <TableCell>{port.protocol}</TableCell>
                                <TableCell>{port.service || 'Unknown'}</TableCell>
                                <TableCell>
                                  <Chip 
                                    label={port.risk_level}
                                    color={
                                      port.risk_level === 'critical' ? 'error' :
                                      port.risk_level === 'high' ? 'warning' :
                                      port.risk_level === 'medium' ? 'info' : 'default'
                                    }
                                    size="small"
                                  />
                                </TableCell>
                                <TableCell>
                                  <Typography 
                                    variant="caption" 
                                    sx={{ 
                                      maxWidth: 200, 
                                      overflow: 'hidden', 
                                      textOverflow: 'ellipsis',
                                      display: 'block',
                                      whiteSpace: 'nowrap'
                                    }}
                                  >
                                    {port.banner || 'N/A'}
                                  </Typography>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                        {scan.port_results.length > 50 && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            Showing first 50 of {scan.port_results.length} open ports
                          </Typography>
                        )}
                      </Paper>
                    </Grid>
                  )}

                  {/* Service Results */}
                  {scan.service_results && scan.service_results.length > 0 && (
                    <Grid item xs={12}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>Detected Services</Typography>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Host</TableCell>
                              <TableCell>Port</TableCell>
                              <TableCell>Service</TableCell>
                              <TableCell>Version</TableCell>
                              <TableCell>Details</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {scan.service_results.map((service, index) => (
                              <TableRow key={index}>
                                <TableCell>{service.ip}</TableCell>
                                <TableCell>{service.port}</TableCell>
                                <TableCell>{service.service}</TableCell>
                                <TableCell>{service.version || 'N/A'}</TableCell>
                                <TableCell>
                                  {service.details && Object.keys(service.details).length > 0 ? (
                                    <Typography variant="caption">
                                      {JSON.stringify(service.details).substring(0, 100)}...
                                    </Typography>
                                  ) : (
                                    'N/A'
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </Paper>
                    </Grid>
                  )}

                  {/* Show message if no detailed results */}
                  {(!scan.host_results || scan.host_results.length === 0) && 
                   (!scan.port_results || scan.port_results.length === 0) && 
                   (!scan.service_results || scan.service_results.length === 0) && (
                    <Grid item xs={12}>
                      <Paper sx={{ p: 3, textAlign: 'center' }}>
                        <Typography variant="h6" color="text.secondary">
                          No detailed scan results available
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          This scan may not have found any active hosts or open ports
                        </Typography>
                      </Paper>
                    </Grid>
                  )}
                </Grid>
              )}
            </Box>
          )}

          {/* Performance Tab */}
          {activeTab === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Scan Performance</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Scan Rate" 
                        secondary={`${(scan.scan_rate || 0).toFixed(2)} hosts/sec`} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Bandwidth Used" 
                        secondary={`${(scan.bandwidth_used || 0).toFixed(2)} MB`} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="CPU Usage (Avg)" 
                        secondary={`${(scan.cpu_usage_avg || 0).toFixed(1)}%`} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Memory Peak" 
                        secondary={`${(scan.memory_usage_peak || 0).toFixed(1)} MB`} 
                      />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Scan Statistics</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Total Targets" 
                        secondary={scan.total_hosts_scanned || 0} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Success Rate" 
                        secondary={`${((scan.hosts_up / (scan.total_hosts_scanned || 1)) * 100).toFixed(1)}%`} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Ports Scanned" 
                        secondary={scan.total_ports_scanned || 0} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Discovery Rate" 
                        secondary={`${((scan.open_ports_found / (scan.total_ports_scanned || 1)) * 100).toFixed(1)}%`} 
                      />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>

              {scan.scan_results && scan.scan_results.performance && (
                <Grid item xs={12}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>Detailed Performance Metrics</Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={3}>
                        <Box textAlign="center">
                          <Typography variant="h5" color="primary">
                            {scan.scan_results.performance.scan_rate?.toFixed(2) || 0}
                          </Typography>
                          <Typography variant="body2">Hosts/Second</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={3}>
                        <Box textAlign="center">
                          <Typography variant="h5" color="info.main">
                            {scan.scan_results.performance.bandwidth_used?.toFixed(2) || 0}
                          </Typography>
                          <Typography variant="body2">MB Bandwidth</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={3}>
                        <Box textAlign="center">
                          <Typography variant="h5" color="warning.main">
                            {scan.scan_results.performance.cpu_usage_avg?.toFixed(1) || 0}%
                          </Typography>
                          <Typography variant="body2">Avg CPU Usage</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={3}>
                        <Box textAlign="center">
                          <Typography variant="h5" color="success.main">
                            {scan.scan_results.performance.memory_usage_peak?.toFixed(1) || 0}
                          </Typography>
                          <Typography variant="body2">Peak Memory (MB)</Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}

          {/* Logs Tab */}
          {activeTab === 3 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Scan Logs</Typography>
                  
                  {/* Error Summary */}
                  <Box sx={{ mb: 2 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="error.main">
                            {scan.errors_count || 0}
                          </Typography>
                          <Typography variant="body2">Errors</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="warning.main">
                            {scan.warnings_count || 0}
                          </Typography>
                          <Typography variant="body2">Warnings</Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Error Log */}
                  {scan.error_log && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>Error Log</Typography>
                      <Paper 
                        variant="outlined" 
                        sx={{ 
                          p: 2, 
                          backgroundColor: 'grey.50',
                          maxHeight: 200,
                          overflow: 'auto',
                          fontFamily: 'monospace',
                          fontSize: '0.875rem'
                        }}
                      >
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                          {scan.error_log}
                        </pre>
                      </Paper>
                    </Box>
                  )}

                  {/* Debug Log */}
                  {scan.debug_log && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>Debug Log</Typography>
                      <Paper 
                        variant="outlined" 
                        sx={{ 
                          p: 2, 
                          backgroundColor: 'grey.50',
                          maxHeight: 200,
                          overflow: 'auto',
                          fontFamily: 'monospace',
                          fontSize: '0.875rem'
                        }}
                      >
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                          {scan.debug_log}
                        </pre>
                      </Paper>
                    </Box>
                  )}

                  {!scan.error_log && !scan.debug_log && (
                    <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      No detailed logs available for this scan
                    </Typography>
                  )}
                </Paper>
              </Grid>
            </Grid>
          )}


        </Box>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
    </Box>
  );
} 

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Network Scans
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadScans}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<Assessment />}
            onClick={() => setTemplateDialogOpen(true)}
          >
            Quick Start
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Scan
          </Button>
        </Box>
      </Box>

      {/* Quick Start Templates */}
      {templates.length > 0 && (
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Quick Start Templates
          </Typography>
          <Grid container spacing={2}>
            {templates.slice(0, 4).map((template) => (
              <Grid item xs={12} sm={6} md={3} key={template.id}>
                <Card 
                  elevation={1} 
                  sx={{ 
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      elevation: 3,
                      transform: 'translateY(-2px)',
                    }
                  }}
                  onClick={() => {
                    setScanForm({
                      ...scanForm,
                      name: `${template.name} - ${new Date().toLocaleDateString()}`,
                      description: template.description,
                      scan_type: template.scan_type,
                      target_ports: template.default_ports,
                      scan_techniques: template.scan_techniques || ['tcp_connect'],
                      timing_template: template.timing_template || 'normal',
                      service_detection: template.service_detection || false,
                      version_detection: template.version_detection || false,
                      os_detection: template.os_detection || false,
                      script_scanning: template.script_scanning || false,
                      max_parallel_hosts: template.max_parallel_hosts || 50,
                      timeout_per_host: template.timeout_per_host || 30,
                    });
                    setCreateDialogOpen(true);
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      {getScanTypeIcon(template.scan_type)}
                      <Typography variant="subtitle2" fontWeight="bold">
                        {template.name}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {template.description}
                    </Typography>
                    <Box mt={1}>
                      <Chip 
                        label={template.scan_type?.replace('_', ' ')} 
                        size="small" 
                        variant="outlined"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {scanStats.total}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Scans
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="info.main">
              {scanStats.running}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Running
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">
              {scanStats.completed}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Completed
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="error.main">
              {scanStats.failed}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Failed
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main">
              {scanStats.pending}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pending
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search scans..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              size="small"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="running">Running</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                label="Type"
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="ping_sweep">Ping Sweep</MenuItem>
                <MenuItem value="port_scan">Port Scan</MenuItem>
                <MenuItem value="service_detection">Service Detection</MenuItem>
                <MenuItem value="vulnerability_scan">Vulnerability Scan</MenuItem>
                <MenuItem value="comprehensive">Comprehensive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Scans List */}
      {filteredScans.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <NetworkCheck sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Network Scans Found
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {scans.length === 0 
              ? "Get started by creating your first network scan using our professional templates or custom configuration."
              : "No scans match your current filters. Try adjusting your search criteria."
            }
          </Typography>
          <Box display="flex" gap={2} justifyContent="center" mt={3}>
            <Button
              variant="contained"
              startIcon={<Assessment />}
              onClick={() => setTemplateDialogOpen(true)}
            >
              Quick Start Templates
            </Button>
            <Button
              variant="outlined"
              startIcon={<Add />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Custom Scan
            </Button>
          </Box>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {paginatedScans.map((scan) => (
            <Grid item xs={12} md={6} lg={4} key={scan.id}>
              <Card elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getScanTypeIcon(scan.scan_type)}
                      <Typography variant="h6" component="div" noWrap>
                        {scan.name || `${scan.scan_type?.replace('_', ' ')} Scan`}
                      </Typography>
                    </Box>
                    <Chip
                      icon={getStatusIcon(scan.status)}
                      label={scan.status?.toUpperCase()}
                      color={getStatusColor(scan.status)}
                      size="small"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Target: {scan.target_range}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {scan.description || 'No description provided'}
                  </Typography>
                  
                  {scan.status === 'running' && (
                    <Box sx={{ mt: 2 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={scan.progress_percentage || 0}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {scan.progress_percentage || 0}% - {scan.current_phase || 'Processing...'}
                      </Typography>
                    </Box>
                  )}
                  
                  <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                    <Chip
                      label={scan.priority?.toUpperCase()}
                      color={getPriorityColor(scan.priority)}
                      size="small"
                    />
                    <Typography variant="caption" color="text.secondary">
                      {scan.duration_formatted || 'Not started'}
                    </Typography>
                  </Box>
                  
                  {scan.status === 'completed' && (
                    <Box sx={{ mt: 2 }}>
                      <Grid container spacing={1}>
                        <Grid item xs={4}>
                          <Box textAlign="center">
                            <Typography variant="body2" fontWeight="bold">
                              {scan.hosts_up || 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Hosts Up
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={4}>
                          <Box textAlign="center">
                            <Typography variant="body2" fontWeight="bold">
                              {scan.open_ports_found || 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Open Ports
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={4}>
                          <Box textAlign="center">
                            <Typography 
                              variant="body2" 
                              fontWeight="bold"
                              color={getRiskColor(scan.risk_score || 0)}
                            >
                              {scan.risk_score || 0}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Risk Score
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </CardContent>
                
                <CardActions>
                  <Tooltip title="View Details">
                    <IconButton 
                      size="small"
                                          onClick={() => {
                      setSelectedScan(scan);
                      setSelectedScanTab(0); // Reset to Overview tab for new scan
                      setDetailsDialogOpen(true);
                    }}
                    >
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                  
                  {scan.status === 'pending' && (
                    <Tooltip title="Start Scan">
                      <IconButton 
                        size="small" 
                        color="primary"
                        onClick={() => handleStartScan(scan.id)}
                      >
                        <PlayArrow />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  {scan.status === 'running' && (
                    <>
                      <Tooltip title="Pause Scan">
                        <IconButton 
                          size="small" 
                          color="warning"
                          onClick={() => handlePauseScan(scan.id)}
                        >
                          <Pause />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Stop Scan">
                        <IconButton 
                          size="small" 
                          color="error"
                          onClick={() => handleStopScan(scan.id)}
                        >
                          <Stop />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                  
                  {scan.status === 'paused' && (
                    <Tooltip title="Resume Scan">
                      <IconButton 
                        size="small" 
                        color="primary"
                        onClick={() => handleStartScan(scan.id)}
                      >
                        <PlayArrow />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  {scan.status === 'completed' && (
                    <Tooltip title="Download Report">
                      <IconButton 
                        size="small" 
                        color="primary"
                        onClick={() => handleDownloadReport(scan.id, scan.name)}
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  <Tooltip title="Delete Scan">
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => handleDeleteScan(scan.id)}
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Pagination */}
      {filteredScans.length > 0 && (
        <Box display="flex" justifyContent="center" mt={3}>
          <TablePagination
            component="div"
            count={filteredScans.length}
            page={page}
            onPageChange={(e, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[6, 12, 24]}
          />
        </Box>
      )}

      {/* Create Scan Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Network Scan</DialogTitle>
        <DialogContent>
          <ScanCreationForm />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateScan} variant="contained">
            Create Scan
          </Button>
        </DialogActions>
      </Dialog>

      {/* Template Selection Dialog */}
      <Dialog 
        open={templateDialogOpen} 
        onClose={() => setTemplateDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Assessment />
            Quick Start Templates
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Choose from our professional scan templates to quickly start common network security assessments.
          </Typography>
          
          <Grid container spacing={3}>
            {templates.map((template) => (
              <Grid item xs={12} md={6} key={template.id}>
                <Card 
                  elevation={2}
                  sx={{ 
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      elevation: 4,
                      transform: 'translateY(-2px)',
                    }
                  }}
                  onClick={() => {
                    setScanForm({
                      ...scanForm,
                      name: `${template.name} - ${new Date().toLocaleDateString()}`,
                      description: template.description,
                      scan_type: template.scan_type,
                      target_ports: template.default_ports,
                      scan_techniques: template.scan_techniques || ['tcp_connect'],
                      timing_template: template.timing_template || 'normal',
                      service_detection: template.service_detection || false,
                      version_detection: template.version_detection || false,
                      os_detection: template.os_detection || false,
                      script_scanning: template.script_scanning || false,
                      max_parallel_hosts: template.max_parallel_hosts || 50,
                      timeout_per_host: template.timeout_per_host || 30,
                    });
                    setTemplateDialogOpen(false);
                    setCreateDialogOpen(true);
                  }}
                >
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                      {getScanTypeIcon(template.scan_type)}
                      <Box>
                        <Typography variant="h6" component="div">
                          {template.name}
                        </Typography>
                        <Chip 
                          label={template.scan_type?.replace('_', ' ')} 
                          size="small" 
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {template.description}
                    </Typography>
                    
                    <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                      {template.service_detection && (
                        <Chip label="Service Detection" size="small" variant="outlined" />
                      )}
                      {template.version_detection && (
                        <Chip label="Version Detection" size="small" variant="outlined" />
                      )}
                      {template.os_detection && (
                        <Chip label="OS Detection" size="small" variant="outlined" />
                      )}
                      {template.script_scanning && (
                        <Chip label="Script Scanning" size="small" variant="outlined" />
                      )}
                    </Box>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Timing: {template.timing_template || 'Normal'}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Max Hosts: {template.max_parallel_hosts || 50}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Timeout: {template.timeout_per_host || 30}s
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Ports: {template.default_ports ? 
                            (template.default_ports.length > 20 ? 
                              template.default_ports.substring(0, 20) + '...' : 
                              template.default_ports) : 
                            'Auto'
                          }
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplateDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Scan Details Dialog */}
      <Dialog 
        open={detailsDialogOpen} 
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Scan Details: {selectedScan?.name || 'Unnamed Scan'}
        </DialogTitle>
        <DialogContent>
          <ScanDetails 
            scan={selectedScan} 
            activeTab={selectedScanTab}
            onTabChange={(event, newValue) => setSelectedScanTab(newValue)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert 
          onClose={() => setNotification({ ...notification, open: false })} 
          severity={notification.severity}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default NetworkScans;