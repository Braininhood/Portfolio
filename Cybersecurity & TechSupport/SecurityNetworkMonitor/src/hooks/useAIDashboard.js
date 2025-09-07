import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const useAIDashboard = () => {
  const [aiStatus, setAiStatus] = useState(null);
  const [threatPredictions, setThreatPredictions] = useState([]);
  const [anomalyReport, setAnomalyReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAIStatus = useCallback(async () => {
    try {
      const response = await api.get('/api/v1/ai-engine/system_status/');
      setAiStatus(response.data.ai_system_status?.system_status || {});
    } catch (err) {
      console.error('Failed to fetch AI status:', err);
    }
  }, []);

  const fetchThreatPredictions = useCallback(async () => {
    try {
      const response = await api.get('/api/v1/ai-engine/threat_predictions/');
      setThreatPredictions(response.data.predictions || []);
    } catch (err) {
      console.error('Failed to fetch threat predictions:', err);
    }
  }, []);

  const fetchAnomalyReport = useCallback(async () => {
    try {
      const response = await api.get('/api/v1/ai-engine/anomaly_report/');
      setAnomalyReport(response.data.anomaly_report || {});
    } catch (err) {
      console.error('Failed to fetch anomaly report:', err);
    }
  }, []);

  const fetchAllAIData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchAIStatus(),
        fetchThreatPredictions(),
        fetchAnomalyReport()
      ]);
    } catch (err) {
      console.error('Failed to fetch AI data:', err);
      setError(err.message || 'Failed to fetch AI data');
    } finally {
      setIsLoading(false);
    }
  }, [fetchAIStatus, fetchThreatPredictions, fetchAnomalyReport]);

  const initializeAISystem = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/api/v1/ai-engine/initialize_system/');
      
      // Refresh AI status after initialization
      await fetchAIStatus();
      
      return response.data;
    } catch (err) {
      console.error('Failed to initialize AI system:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchAIStatus]);

  const triggerLearning = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/api/v1/ai-engine/trigger_learning/');
      
      // Refresh AI status after learning
      await fetchAIStatus();
      
      return response.data;
    } catch (err) {
      console.error('Failed to trigger learning:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchAIStatus]);

  useEffect(() => {
    fetchAllAIData();
  }, [fetchAllAIData]);

  return {
    aiStatus,
    threatPredictions,
    anomalyReport,
    isLoading,
    error,
    fetchAllAIData,
    initializeAISystem,
    triggerLearning,
    fetchAIStatus,
    fetchThreatPredictions,
    fetchAnomalyReport
  };
};

export default useAIDashboard;
