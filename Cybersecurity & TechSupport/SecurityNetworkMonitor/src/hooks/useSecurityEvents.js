import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const useSecurityEvents = () => {
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState({
    criticalCount: 0,
    highCount: 0,
    mediumCount: 0,
    lowCount: 0,
    totalCount: 0,
    unresolvedCount: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchEvents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/api/v1/security-events/all/');
      const eventsData = response.data.results || response.data || [];
      
      setEvents(eventsData);
      
      // Calculate metrics
      const criticalCount = eventsData.filter(e => e.severity === 'critical').length;
      const highCount = eventsData.filter(e => e.severity === 'high').length;
      const mediumCount = eventsData.filter(e => e.severity === 'medium').length;
      const lowCount = eventsData.filter(e => e.severity === 'low').length;
      const unresolvedCount = eventsData.filter(e => !e.is_resolved).length;
      
      setMetrics({
        criticalCount,
        highCount,
        mediumCount,
        lowCount,
        totalCount: eventsData.length,
        unresolvedCount
      });
    } catch (err) {
      console.error('Failed to fetch security events:', err);
      setError(err.message || 'Failed to fetch security events');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const resolveEvent = useCallback(async (eventId) => {
    try {
      await api.patch(`/api/v1/security-events/${eventId}/`, {
        is_resolved: true
      });
      
      // Update local state
      setEvents(prevEvents => 
        prevEvents.map(event => 
          event.id === eventId 
            ? { ...event, is_resolved: true }
            : event
        )
      );
      
      // Recalculate metrics
      fetchEvents();
    } catch (err) {
      console.error('Failed to resolve event:', err);
      throw err;
    }
  }, [fetchEvents]);

  const createEvent = useCallback(async (eventData) => {
    try {
      const response = await api.post('/api/v1/security-events/', eventData);
      
      // Refresh events list
      fetchEvents();
      
      return response.data;
    } catch (err) {
      console.error('Failed to create event:', err);
      throw err;
    }
  }, [fetchEvents]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return {
    events,
    metrics,
    isLoading,
    error,
    fetchEvents,
    resolveEvent,
    createEvent
  };
};

export default useSecurityEvents;
