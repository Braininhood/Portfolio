import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  TextField,
  CircularProgress
} from '@mui/material';
import {
  Psychology as AIIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Analytics as AnalyticsIcon,
  SmartToy as BotIcon
} from '@mui/icons-material';
import { Doughnut } from 'react-chartjs-2';

const AIDashboard = () => {
  const [aiStatus, setAiStatus] = useState({
    system_status: {
      threat_detector_trained: false,
      anomaly_detector_trained: false,
      is_learning: false,
      last_training: null
    },
    performance_metrics: {},
    capabilities: {}
  });
  
  const [threatPredictions, setThreatPredictions] = useState([]);
  const [anomalyReport, setAnomalyReport] = useState({});
  const [loading, setLoading] = useState(true);
  const [initializingAI, setInitializingAI] = useState(false);
  const [learningInProgress, setLearningInProgress] = useState(false);
  const [configDialog, setConfigDialog] = useState(false);
  const [learningConfig, setLearningConfig] = useState({
    auto_retrain_hours: 24,
    min_new_events: 50,
    learning_enabled: true
  });

  useEffect(() => {
    fetchAIStatus();
    fetchThreatPredictions();
    fetchAnomalyReport();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchAIStatus();
      if (!learningInProgress) {
        fetchThreatPredictions();
        fetchAnomalyReport();
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [learningInProgress]);

  const fetchAIStatus = async () => {
    try {
      const response = await fetch('/api/v1/ai-engine/system_status/');
      if (response.ok) {
        const data = await response.json();
        setAiStatus(data.ai_system_status);
      }
    } catch (error) {
      console.error('Failed to fetch AI status:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchThreatPredictions = async () => {
    try {
      const response = await fetch('/api/v1/ai-engine/threat_predictions/');
      if (response.ok) {
        const data = await response.json();
        setThreatPredictions(data.predictions || []);
      }
    } catch (error) {
      console.error('Failed to fetch threat predictions:', error);
    }
  };

  const fetchAnomalyReport = async () => {
    try {
      const response = await fetch('/api/v1/ai-engine/anomaly_report/');
      if (response.ok) {
        const data = await response.json();
        setAnomalyReport(data.anomaly_report || {});
      }
    } catch (error) {
      console.error('Failed to fetch anomaly report:', error);
    }
  };

  const initializeAISystem = async () => {
    setInitializingAI(true);
    try {
      const response = await fetch('/api/v1/ai-engine/initialize_system/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('AI System initialized:', data);
        await fetchAIStatus();
        await fetchThreatPredictions();
        await fetchAnomalyReport();
      } else {
        console.error('Failed to initialize AI system');
      }
    } catch (error) {
      console.error('Error initializing AI system:', error);
    } finally {
      setInitializingAI(false);
    }
  };

  const triggerContinuousLearning = async () => {
    setLearningInProgress(true);
    try {
      const response = await fetch('/api/v1/ai-engine/continuous_learning/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hours: 24 })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Continuous learning completed:', data);
        await fetchAIStatus();
      } else {
        console.error('Failed to trigger continuous learning');
      }
    } catch (error) {
      console.error('Error in continuous learning:', error);
    } finally {
      setLearningInProgress(false);
    }
  };

  const updateLearningConfig = async () => {
    try {
      const response = await fetch('/api/v1/ai-engine/configure_learning/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(learningConfig)
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Learning configuration updated:', data);
        setConfigDialog(false);
        await fetchAIStatus();
      } else {
        console.error('Failed to update learning configuration');
      }
    } catch (error) {
      console.error('Error updating learning configuration:', error);
    }
  };

  const getStatusColor = (isActive) => {
    return isActive ? 'success' : 'error';
  };

  const getStatusText = (isActive) => {
    return isActive ? 'Active' : 'Inactive';
  };

  const getThreatLevelColor = (threatLevel) => {
    switch (threatLevel) {
      case 'critical_threat': return 'error';
      case 'high_threat': return 'warning';
      case 'medium_threat': return 'info';
      case 'low_threat': return 'success';
      default: return 'default';
    }
  };

  const formatThreatLevel = (threatLevel) => {
    return threatLevel?.replace('_', ' ').toUpperCase() || 'UNKNOWN';
  };

  // Chart data for threat predictions
  const threatChartData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [
        threatPredictions.filter(p => p.prediction?.threat_level === 'critical_threat').length,
        threatPredictions.filter(p => p.prediction?.threat_level === 'high_threat').length,
        threatPredictions.filter(p => p.prediction?.threat_level === 'medium_threat').length,
        threatPredictions.filter(p => p.prediction?.threat_level === 'low_threat').length,
      ],
      backgroundColor: ['#f44336', '#ff9800', '#2196f3', '#4caf50'],
      borderWidth: 2,
      borderColor: '#fff'
    }]
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading AI Dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <BotIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            AI Security Engine
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Configure Learning">
            <IconButton onClick={() => setConfigDialog(true)} color="primary">
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh Data">
            <IconButton onClick={fetchAIStatus} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* AI System Status Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6">Threat Detector</Typography>
                  <Chip 
                    label={getStatusText(aiStatus.system_status?.threat_detector_trained)}
                    color={getStatusColor(aiStatus.system_status?.threat_detector_trained)}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <SecurityIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6">Anomaly Detector</Typography>
                  <Chip 
                    label={getStatusText(aiStatus.system_status?.anomaly_detector_trained)}
                    color={getStatusColor(aiStatus.system_status?.anomaly_detector_trained)}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <AnalyticsIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6">Learning Status</Typography>
                  <Chip 
                    label={aiStatus.system_status?.is_learning ? 'Learning' : 'Idle'}
                    color={aiStatus.system_status?.is_learning ? 'warning' : 'success'}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <AIIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6">Predictions</Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {threatPredictions.length}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Grid container spacing={2} mb={4}>
        <Grid item>
          <Button
            variant="contained"
            startIcon={initializingAI ? <CircularProgress size={20} /> : <PlayIcon />}
            onClick={initializeAISystem}
            disabled={initializingAI || (aiStatus.system_status?.threat_detector_trained && aiStatus.system_status?.anomaly_detector_trained)}
            color="primary"
            size="large"
          >
            {initializingAI ? 'Initializing...' : 'Initialize AI System'}
          </Button>
        </Grid>
        <Grid item>
          <Button
            variant="contained"
            startIcon={learningInProgress ? <CircularProgress size={20} /> : <AIIcon />}
            onClick={triggerContinuousLearning}
            disabled={learningInProgress || !aiStatus.system_status?.threat_detector_trained}
            color="secondary"
            size="large"
          >
            {learningInProgress ? 'Learning...' : 'Trigger Learning'}
          </Button>
        </Grid>
      </Grid>

      {/* AI Insights and Charts */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Threat Predictions
              </Typography>
              {threatPredictions.length > 0 ? (
                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                  <Table stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Event ID</TableCell>
                        <TableCell>Threat Level</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>AI Score</TableCell>
                        <TableCell>Explanation</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {threatPredictions.slice(0, 10).map((prediction) => (
                        <TableRow key={prediction.event_id}>
                          <TableCell>{prediction.event_id}</TableCell>
                          <TableCell>
                            <Chip
                              label={formatThreatLevel(prediction.prediction?.threat_level)}
                              color={getThreatLevelColor(prediction.prediction?.threat_level)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {(prediction.prediction?.confidence * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              <LinearProgress
                                variant="determinate"
                                value={prediction.prediction?.ai_score || 0}
                                sx={{ width: 60, mr: 1 }}
                              />
                              {prediction.prediction?.ai_score || 0}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Tooltip title={prediction.prediction?.explanation || 'No explanation'}>
                              <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                                {prediction.prediction?.explanation || 'No explanation'}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  No threat predictions available. Initialize the AI system to start generating predictions.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Threat Distribution
              </Typography>
              {threatPredictions.length > 0 ? (
                <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Doughnut 
                    data={threatChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom'
                        }
                      }
                    }}
                  />
                </Box>
              ) : (
                <Alert severity="info">
                  No data available for threat distribution chart.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Anomaly Report */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Anomaly Detection Report
              </Typography>
              {anomalyReport.anomalies_detected > 0 ? (
                <Box>
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">
                      {anomalyReport.anomalies_detected} anomalies detected with overall score: {(anomalyReport.anomaly_score * 100).toFixed(1)}%
                    </Typography>
                  </Alert>
                  {anomalyReport.details && anomalyReport.details.length > 0 && (
                    <TableContainer component={Paper}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Type</TableCell>
                            <TableCell>Score</TableCell>
                            <TableCell>Severity</TableCell>
                            <TableCell>Explanation</TableCell>
                            <TableCell>Device</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {anomalyReport.details.map((anomaly, index) => (
                            <TableRow key={index}>
                              <TableCell>{anomaly.anomaly_type}</TableCell>
                              <TableCell>
                                <LinearProgress
                                  variant="determinate"
                                  value={anomaly.anomaly_score * 100}
                                  sx={{ width: 100 }}
                                />
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={anomaly.severity?.toUpperCase()}
                                  color={getThreatLevelColor(anomaly.severity + '_threat')}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>{anomaly.explanation}</TableCell>
                              <TableCell>{anomaly.device_ip || 'N/A'}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </Box>
              ) : (
                <Alert severity="success">
                  No anomalies detected in recent network behavior.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>AI Learning Configuration</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={learningConfig.learning_enabled}
                  onChange={(e) => setLearningConfig({
                    ...learningConfig,
                    learning_enabled: e.target.checked
                  })}
                />
              }
              label="Enable Continuous Learning"
            />
            <TextField
              fullWidth
              label="Auto Retrain Hours"
              type="number"
              value={learningConfig.auto_retrain_hours}
              onChange={(e) => setLearningConfig({
                ...learningConfig,
                auto_retrain_hours: parseInt(e.target.value)
              })}
              sx={{ mt: 2 }}
            />
            <TextField
              fullWidth
              label="Minimum New Events for Learning"
              type="number"
              value={learningConfig.min_new_events}
              onChange={(e) => setLearningConfig({
                ...learningConfig,
                min_new_events: parseInt(e.target.value)
              })}
              sx={{ mt: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
          <Button onClick={updateLearningConfig} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIDashboard; 