import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../services/api';

const useRealTimeDevices = () => {
  const [devices, setDevices] = useState([]);
  const [networkStats, setNetworkStats] = useState({
    total_devices: 0,
    online_devices: 0,
    offline_devices: 0,
    unknown_devices: 0,
    new_devices_today: 0,
    unresolved_alerts: 0,
    critical_alerts: 0,
    last_updated: null
  });
  const [connectionStatus, setConnectionStatus] = useState('initializing');
  const [notifications, setNotifications] = useState([]);
  const [monitoringStatus, setMonitoringStatus] = useState('unknown');
  
  const ws = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 1; // Only try WebSocket once
  const reconnectDelay = useRef(1000);
  const pollingInterval = useRef(null);
  const hasTriedWebSocket = useRef(false);

  const showNotification = useCallback((message, type = 'info') => {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date().toISOString()
    };
    
    setNotifications(prev => [...prev.slice(-4), notification]);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  }, []);

  // REST API polling fallback
  const startPolling = useCallback(() => {
    console.log('📡 Using REST API polling (10-second updates)');
    setConnectionStatus('polling');
    
    const poll = async () => {
      try {
        // Load devices and stats via REST API
        const [devicesResponse, statsResponse] = await Promise.all([
          api.getDevices(),
          api.getDashboardStats()
        ]);
        
        setDevices(devicesResponse.results || devicesResponse);
        setNetworkStats(prev => ({
          ...prev,
          ...statsResponse,
          last_updated: new Date().toISOString()
        }));
        
      } catch (error) {
        console.error('❌ API polling error:', error);
        setConnectionStatus('error');
        showNotification('Failed to load data via API', 'error');
      }
    };
    
    // Initial load
    poll();
    
    // Poll every 10 seconds
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
    }
    pollingInterval.current = setInterval(poll, 10000);
  }, [showNotification]);

  const stopPolling = useCallback(() => {
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
      pollingInterval.current = null;
    }
  }, []);

  // Function to refresh device list and stats
  const refreshDeviceList = useCallback(async () => {
    try {
      console.log('🔄 Refreshing device list...');
      const [devicesResponse, statsResponse] = await Promise.all([
        api.getDevices(),
        api.getDashboardStats()
      ]);
      
      setDevices(devicesResponse.results || devicesResponse);
      setNetworkStats(prev => ({
        ...prev,
        ...statsResponse,
        last_updated: new Date().toISOString()
      }));
      
      console.log('✅ Device list refreshed successfully');
    } catch (error) {
      console.error('❌ Error refreshing device list:', error);
    }
  }, []);

  const handleWebSocketMessage = useCallback((data) => {
    // Debug logging for all WebSocket messages
    console.log('📨 WebSocket message received:', {
      type: data.type,
      typeOf: typeof data.type,
      data: data
    });
    
    // Ensure type is a string and trim any whitespace
    const messageType = String(data.type || '').trim();
    console.log('🔍 Processing message type:', messageType);
    
    switch (messageType) {
      case 'initial_state':
        setDevices(data.devices || []);
        setNetworkStats(prev => ({
          ...prev,
          ...(data.stats || {}),
          last_updated: new Date().toISOString()
        }));
        console.log('📋 Received initial state:', data.devices?.length, 'devices');
        break;

      case 'device_list':
        setDevices(data.devices || []);
        console.log('📋 Received device list:', data.devices?.length, 'devices');
        break;

      case 'device_status_changed':
        console.log('📊 Device status changed:', {
          ip: data.ip_address,
          old_status: data.old_status,
          new_status: data.new_status
        });
        setDevices(prev => prev.map(device => 
          device.ip_address === data.ip_address
            ? { 
                ...device, 
                status: data.new_status,
                last_seen: data.last_seen,
                response_time: data.response_time
              }
            : device
        ));
        showNotification(
          `${data.hostname || data.ip_address} is now ${data.new_status}`,
          data.new_status === 'online' ? 'success' : 'warning'
        );
        break;

      case 'device_discovered':
        console.log('🆕 New device discovered:', data.device);
        setDevices(prev => {
          const exists = prev.find(d => d.ip_address === data.device.ip_address);
          if (!exists) {
            showNotification(
              `New device discovered: ${data.device.hostname || data.device.ip_address}`,
              'success'
            );
            return [...prev, data.device];
          }
          return prev;
        });
        break;

      case 'port_scan_started':
        console.log('🚀 Port scan started:', {
          ip: data.device_ip || data.ip_address,
          progress: data.progress
        });
        const startDeviceIp = data.device_ip || data.ip_address;
        setDevices(prev => prev.map(device => 
          device.ip_address === startDeviceIp
            ? { 
                ...device, 
                is_scanning: true,
                scan_progress: data.progress || 0
              }
            : device
        ));
        showNotification(
          `Port scan started for ${startDeviceIp}`,
          'info'
        );
        break;

      case 'port_scan_progress':
        console.log('⏳ Port scan progress:', {
          ip: data.device_ip || data.ip_address,
          progress: data.progress
        });
        const progressDeviceIp = data.device_ip || data.ip_address;
        setDevices(prev => prev.map(device => 
          device.ip_address === progressDeviceIp
            ? { 
                ...device, 
                is_scanning: true,
                scan_progress: data.progress || 0
              }
            : device
        ));
        break;

      case 'port_scan_complete':
        console.log('🔍 Port scan completed:', {
          ip: data.device_ip || data.ip_address,
          ports: data.open_ports
        });
        const deviceIp = data.device_ip || data.ip_address;
        setDevices(prev => prev.map(device => 
          device.ip_address === deviceIp
            ? { 
                ...device, 
                open_ports: data.open_ports,
                is_scanning: false,
                scan_progress: 100,
                last_port_scan: data.scan_time
              }
            : device
        ));
        showNotification(
          `Port scan completed for ${deviceIp}: ${data.open_ports?.length || 0} open ports`,
          'success'
        );
        break;

      case 'port_scan_error':
        console.log('❌ Port scan failed:', {
          ip: data.device_ip || data.ip_address,
          error: data.error
        });
        const errorDeviceIp = data.device_ip || data.ip_address;
        setDevices(prev => prev.map(device => 
          device.ip_address === errorDeviceIp
            ? { 
                ...device, 
                is_scanning: false,
                scan_progress: 0
              }
            : device
        ));
        showNotification(
          `Port scan failed for ${errorDeviceIp}: ${data.error}`,
          'error'
        );
        break;

      case 'network_stats_update':
        console.log('📊 Network stats updated:', data.data);
        setNetworkStats(prev => ({
          ...prev,
          ...data.data,
          last_updated: data.timestamp
        }));
        break;

      case 'device_update':
        console.log('🔄 Device updated:', data.device);
        setDevices(prev => {
          const existingDeviceIndex = prev.findIndex(device => device.id === data.device.id);
          if (existingDeviceIndex !== -1) {
            // Update existing device
            return prev.map(device => 
              device.id === data.device.id
                ? { ...device, ...data.device }
                : device
            );
          } else {
            // Add new device if it doesn't exist
            console.log('➕ Adding new device to list:', data.device);
            return [...prev, data.device];
          }
        });
        break;

      case 'traffic_update':
        // Handle different traffic update message structures
        let trafficDeviceIp, trafficData;
        
        if (data.device_ip && data.traffic_data) {
          // Structure from TrafficMonitor and ScanProgressConsumer
          trafficDeviceIp = data.device_ip;
          trafficData = data.traffic_data;
        } else if (data.data && data.data.device_metrics) {
          // Structure from NetworkMonitorConsumer
          console.log('📈 Traffic update (network monitor):', data.data);
          // Update network stats if available
          if (data.data.traffic_metrics) {
            setNetworkStats(prev => ({
              ...prev,
              ...data.data.traffic_metrics,
              last_updated: data.timestamp || new Date().toISOString()
            }));
          }
          // Process device metrics
          if (data.data.device_metrics && Array.isArray(data.data.device_metrics)) {
            data.data.device_metrics.forEach(deviceMetric => {
              if (deviceMetric.ip_address) {
                setDevices(prev => prev.map(device => 
                  device.ip_address === deviceMetric.ip_address
                    ? { 
                        ...device, 
                        current_bandwidth_usage: deviceMetric.bandwidth_usage || 0,
                        packet_rate: deviceMetric.packet_rate || 0,
                        connection_count: deviceMetric.connection_count || 0,
                        cpu_usage: deviceMetric.cpu_usage || 0,
                        memory_usage: deviceMetric.memory_usage || 0,
                        uptime: deviceMetric.uptime || 0,
                        threat_level: deviceMetric.threat_level || 'low',
                        last_seen: new Date().toISOString()
                      }
                    : device
                ));
              }
            });
          }
          break;
        }
        
        // Log appropriate message based on structure
        if (data.device_ip && data.traffic_data) {
          console.log('📈 Individual device traffic update:', {
            ip: trafficDeviceIp,
            traffic: trafficData
          });
        } else if (data.data && data.data.device_metrics) {
          console.log('📈 Network-wide traffic update:', {
            deviceCount: data.data.device_metrics.length,
            trafficMetrics: data.data.traffic_metrics,
            onlineDevices: data.data.online_devices,
            totalDevices: data.data.total_devices
          });
        } else {
          console.log('📈 Unknown traffic update structure:', data);
        }
        
        // Handle individual device traffic updates
        if (trafficDeviceIp && trafficData) {
          setDevices(prev => prev.map(device => 
            device.ip_address === trafficDeviceIp
              ? { 
                  ...device, 
                  current_bandwidth_usage: trafficData.bandwidth_usage || trafficData.current_bandwidth || 0,
                  total_bytes_in: trafficData.bytes_received || trafficData.bytes_in || device.total_bytes_in || 0,
                  total_bytes_out: trafficData.bytes_sent || trafficData.bytes_out || device.total_bytes_out || 0,
                  last_seen: new Date().toISOString()
                }
              : device
          ));
        }
        break;

      case 'scan_progress':
        console.log('⏳ Scan progress:', {
          scan_id: data.scan_id,
          progress: data.progress,
          current_ip: data.current_ip
        });
        showNotification(
          `Scanning ${data.current_ip || 'network'}: ${data.progress}% complete`,
          'info'
        );
        break;

      case 'scan_complete':
        console.log('✅ Scan completed:', {
          scan_id: data.scan_id,
          status: data.status,
          hosts_up: data.hosts_up || 0
        });
        showNotification(
          `Network scan completed: ${data.hosts_up || 0} devices found`,
          'success'
        );
        
        // Refresh device list after scan completion to ensure all devices are shown
        setTimeout(() => {
          console.log('🔄 Auto-refreshing device list after scan completion...');
          refreshDeviceList();
        }, 500);
        break;

      case 'security_alert':
        console.log('🚨 Security alert received:', data.alert);
        showNotification(
          `Security Alert: ${data.alert.title}`,
          data.alert.severity === 'critical' ? 'error' : 'warning'
        );
        break;

      case 'security_event':
        console.log('🔒 Security event received:', {
          event_type: data.event_type,
          severity: data.severity,
          title: data.title,
          description: data.description
        });
        showNotification(
          `Security Event: ${data.title}`,
          data.severity === 'critical' ? 'error' : data.severity === 'high' ? 'warning' : 'info'
        );
        break;

      case 'port_changes_detected':
        console.log('🔄 Port changes detected:', {
          device: data.device_ip,
          hostname: data.hostname,
          new_ports: data.new_ports,
          closed_ports: data.closed_ports
        });
        
        // Update device in state
        setDevices(prev => prev.map(device => 
          device.ip_address === data.device_ip
            ? { 
                ...device, 
                // Port changes will be reflected in next device update
                last_port_change: data.timestamp
              }
            : device
        ));
        
        // Show notification for port changes
        const deviceName = data.hostname || data.device_ip;
        let message = `Port changes on ${deviceName}:`;
        if (data.new_ports.length > 0) {
          message += ` +${data.new_ports.join(', ')}`;
        }
        if (data.closed_ports.length > 0) {
          message += ` -${data.closed_ports.join(', ')}`;
        }
        
        showNotification(message, data.new_ports.length > 0 ? 'warning' : 'info');
        break;

      case 'scan_update':
        console.log('🔍 Scan update received:', {
          scan_id: data.scan_id,
          status: data.status,
          hosts_up: data.hosts_up || 0
        });
        showNotification(
          `Network scan ${data.status}: ${data.hosts_up || 0} devices found`,
          data.status === 'completed' ? 'success' : 'info'
        );
        break;

      case 'scan_progress_update':
        console.log('📊 Scan progress update:', {
          scan_id: data.scan_id,
          status: data.status,
          progress: data.progress_percentage,
          current_phase: data.current_phase,
          current_target: data.current_target,
          hosts_scanned: data.hosts_scanned,
          hosts_up: data.hosts_up,
          open_ports: data.open_ports_found
        });
        // This is handled by the NetworkScans page directly
        break;

      case 'scan_started':
        console.log('🚀 Scan started:', {
          scan_id: data.scan_id,
          scan_type: data.scan_type,
          target_range: data.target_range
        });
        showNotification(
          `${data.scan_type?.replace('_', ' ')} scan started for ${data.target_range}`,
          'info'
        );
        break;

      case 'scan_completed':
        console.log('✅ Scan completed:', {
          scan_id: data.scan_id,
          status: data.status,
          duration: data.duration,
          hosts_scanned: data.hosts_scanned,
          hosts_up: data.hosts_up,
          open_ports: data.open_ports_found,
          risk_score: data.risk_score
        });
        showNotification(
          `Scan completed: ${data.hosts_up}/${data.hosts_scanned} hosts up, ${data.open_ports_found} open ports (Risk: ${data.risk_score})`,
          'success'
        );
        break;

      case 'scan_failed':
        console.log('❌ Scan failed:', {
          scan_id: data.scan_id,
          error: data.error
        });
        showNotification(
          `Scan failed: ${data.error}`,
          'error'
        );
        break;

      case 'pong':
        // Handle pong response (keep-alive)
        console.log('🏓 Pong received');
        break;

      case 'heartbeat_ack':
        // Handle heartbeat acknowledgment
        console.log('💓 Heartbeat acknowledged');
        break;

      case 'subscribed':
        console.log('✅ Subscribed to channels:', data.channels);
        break;

      case 'unsubscribed':
        console.log('❌ Unsubscribed from channels:', data.channels);
        break;

      case 'devices_cleared':
        console.log('🗑️ All devices cleared:', data.message);
        setDevices([]);
        setNetworkStats({
          total_devices: 0,
          online_devices: 0,
          offline_devices: 0,
          new_devices_today: 0,
          unresolved_alerts: 0
        });
        showNotification(data.message, 'success');
        
        // Automatically refresh device list after clearing
        setTimeout(() => {
          console.log('🔄 Auto-refreshing device list after clear...');
          refreshDeviceList();
        }, 1000);
        break;

      case 'device_ip_changed':
        console.log('🔄 Device IP changed:', {
          device_id: data.device_id,
          old_ip: data.old_ip,
          new_ip: data.new_ip,
          mac_address: data.mac_address,
          hostname: data.hostname
        });
        
        // Update device in state with new IP
        setDevices(prev => prev.map(device => 
          device.id === data.device_id
            ? { 
                ...device, 
                ip_address: data.new_ip,
                last_seen: data.timestamp
              }
            : device
        ));
        
        const changedDeviceName = data.hostname || data.mac_address || data.device_id;
        showNotification(
          `Device ${changedDeviceName} changed IP: ${data.old_ip} → ${data.new_ip}`,
          'warning'
        );
        break;

      case 'error':
        console.error('❌ WebSocket error:', data.message);
        showNotification(`Error: ${data.message}`, 'error');
        break;

      default:
        console.log('❓ Unknown WebSocket message type:', data.type, 'Full data:', data);
        
        // Special handling for port scan messages that might not be matching
        if (messageType.includes('port_scan')) {
          console.log('🔧 Port scan message detected but not handled:', {
            originalType: data.type,
            processedType: messageType,
            device_ip: data.device_ip,
            ip_address: data.ip_address,
            progress: data.progress,
            open_ports: data.open_ports
          });
          
          // Try to handle port scan messages manually
          const deviceIpFallback = data.device_ip || data.ip_address;
          if (messageType === 'port_scan_started') {
            console.log('🚀 Manually handling port_scan_started');
            setDevices(prev => prev.map(device => 
              device.ip_address === deviceIpFallback
                ? { 
                    ...device, 
                    is_scanning: true,
                    scan_progress: data.progress || 0
                  }
                : device
            ));
            showNotification(`Port scan started for ${deviceIpFallback}`, 'info');
          } else if (messageType === 'port_scan_progress') {
            console.log('⏳ Manually handling port_scan_progress');
            setDevices(prev => prev.map(device => 
              device.ip_address === deviceIpFallback
                ? { 
                    ...device, 
                    is_scanning: true,
                    scan_progress: data.progress || 0
                  }
                : device
            ));
          } else if (messageType === 'port_scan_complete') {
            console.log('🔍 Manually handling port_scan_complete');
            setDevices(prev => prev.map(device => 
              device.ip_address === deviceIpFallback
                ? { 
                    ...device, 
                    open_ports: data.open_ports,
                    is_scanning: false,
                    scan_progress: 100,
                    last_port_scan: data.scan_time
                  }
                : device
            ));
            showNotification(
              `Port scan completed for ${deviceIpFallback}: ${data.open_ports?.length || 0} open ports`,
              'success'
            );
          }
        }
    }
  }, [showNotification, refreshDeviceList]);

  const connectWebSocket = useCallback(() => {
    // Only try WebSocket once
    if (hasTriedWebSocket.current) {
      return;
    }
    
    hasTriedWebSocket.current = true;
    setConnectionStatus('connecting');
    
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/network/`;
    
    try {
      ws.current = new WebSocket(wsUrl);
      
      // Set timeout for WebSocket connection
      const connectionTimeout = setTimeout(() => {
        if (ws.current && ws.current.readyState !== WebSocket.OPEN) {
          ws.current.close();
          startPolling();
        }
      }, 8000); // 8 second timeout (increased for better stability)
      
      ws.current.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log('✅ WebSocket connected - Real-time mode active');
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        reconnectDelay.current = 1000;
        stopPolling(); // Stop polling when WebSocket works
        
        showNotification('Real-time connection established', 'success');
        
        // Request initial device list
        ws.current.send(JSON.stringify({
          type: 'get_devices',
          timestamp: new Date().toISOString()
        }));
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        clearTimeout(connectionTimeout);
        
        // Only try to reconnect if we haven't exceeded attempts
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          setConnectionStatus('reconnecting');
          setTimeout(() => {
            connectWebSocket();
          }, reconnectDelay.current);
          
          // Exponential backoff
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 5000);
        } else {
          // WebSocket failed, use REST API polling
          startPolling();
        }
      };

      ws.current.onerror = (error) => {
        clearTimeout(connectionTimeout);
        // Silently fall back to polling (this is expected behavior)
        startPolling();
      };

    } catch (error) {
      console.error('❌ Error creating WebSocket connection:', error);
      startPolling();
    }
  }, [handleWebSocketMessage, showNotification, startPolling, stopPolling]);

  // Ping/keep-alive mechanism
  useEffect(() => {
    if (connectionStatus !== 'connected') return;

    const pingInterval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({
          type: 'heartbeat',
          timestamp: new Date().toISOString()
        }));
      }
    }, 20000); // Heartbeat every 20 seconds (balanced for stability)

    return () => clearInterval(pingInterval);
  }, [connectionStatus]);

  // Initialize connection
  useEffect(() => {
    console.log('🚀 Network Security Monitor starting...');
    
    // Start with REST API immediately
    const loadInitialData = async () => {
      setConnectionStatus('loading');
      try {
        const [devicesResponse, statsResponse, monitoringResponse] = await Promise.all([
          api.getDevices(),
          api.getDashboardStats(),
          api.getMonitoringStatus()
        ]);
        
        setDevices(devicesResponse.results || devicesResponse);
        setNetworkStats(prev => ({
          ...prev,
          ...statsResponse,
          last_updated: new Date().toISOString()
        }));
        setMonitoringStatus(monitoringResponse.status || 'unknown');
        
        console.log('✅ Connected via REST API - Data loading every 10 seconds');
        console.log('📊 Monitoring status:', monitoringResponse.status);
        
        // Try WebSocket for real-time updates (will silently fall back if needed)
        setTimeout(() => {
          connectWebSocket();
        }, 1000);
        
      } catch (error) {
        console.error('❌ Error loading initial data:', error);
        setConnectionStatus('error');
        showNotification('Failed to load initial data', 'error');
      }
    };
    
    loadInitialData();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      stopPolling();
    };
  }, [connectWebSocket, stopPolling, showNotification]);

  // Device management functions
  const toggleDeviceMonitoring = useCallback(async (deviceId) => {
    try {
      await api.toggleDeviceMonitoring(deviceId);
      
      setDevices(prev => prev.map(device => 
        device.id === deviceId 
          ? { ...device, monitor_enabled: !device.monitor_enabled }
          : device
      ));
      
      showNotification('Device monitoring settings updated', 'success');
    } catch (error) {
      console.error('Error toggling device monitoring:', error);
      showNotification('Failed to update device monitoring', 'error');
    }
  }, [showNotification]);

  const pingDevice = useCallback(async (deviceId) => {
    try {
      const result = await api.pingDevice(deviceId);
      
      // Debug logging
      console.log('🏓 Ping API response:', result);
      
      // Use the status field from API response as primary indicator
      const isOnline = result.status === 'online' || result.is_alive === true;
      const responseTime = result.response_time || 0;
      
      // Update device in state immediately with ping result
      setDevices(prev => prev.map(device => 
        device.id === deviceId
          ? { 
              ...device, 
              status: result.status,
              response_time: result.response_time,
              last_seen: result.status === 'online' ? new Date().toISOString() : device.last_seen
            }
          : device
      ));
      
      // Also force refresh device list to ensure consistency
      try {
        const devicesResponse = await api.getDevices();
        setDevices(devicesResponse.results || devicesResponse);
        console.log('🔄 Device list refreshed after ping');
      } catch (refreshError) {
        console.warn('Failed to refresh device list after ping:', refreshError);
      }
      
      showNotification(
        `Ping result: ${isOnline ? 'Online' : 'Offline'} (${responseTime > 0 ? responseTime.toFixed(1) : '0'}ms)`,
        isOnline ? 'success' : 'warning'
      );
      
      return result;
    } catch (error) {
      console.error('Error pinging device:', error);
      showNotification('Failed to ping device', 'error');
      throw error;
    }
  }, [showNotification]);

  const scanDevicePorts = useCallback(async (deviceId) => {
    try {
      const result = await api.scanDevicePorts(deviceId);
      
      // Enhanced notification with risk summary
      const riskSummary = result.risk_summary || {};
      const criticalCount = riskSummary.critical || 0;
      const highCount = riskSummary.high || 0;
      const totalPorts = result.total_open_ports || 0;
      
      let notificationType = 'success';
      let message = `Port scan complete: ${totalPorts} open ports found`;
      
      if (criticalCount > 0) {
        notificationType = 'error';
        message += ` (🔴 ${criticalCount} critical risk!)`;
      } else if (highCount > 0) {
        notificationType = 'warning';
        message += ` (🟠 ${highCount} high risk)`;
      }
      
      if (result.scan_includes_udp) {
        message += ' [TCP+UDP]';
      }
      
      showNotification(message, notificationType);
      
      // Log detailed results for debugging
      console.log('🔍 Port scan results:', {
        device_id: deviceId,
        total_ports: totalPorts,
        risk_summary: riskSummary,
        includes_udp: result.scan_includes_udp,
        open_ports: result.open_ports
      });
      
      // Refresh devices to show updated port information
      const devicesResponse = await api.getDevices();
      setDevices(devicesResponse.results || devicesResponse);
      
      return result;
    } catch (error) {
      console.error('Error scanning device ports:', error);
      showNotification('Failed to scan device ports', 'error');
      throw error;
    }
  }, [showNotification]);

  const startNetworkDiscovery = useCallback(async () => {
    try {
      await api.quickDiscovery();
      showNotification('Network discovery started', 'info');
    } catch (error) {
      console.error('Error starting network discovery:', error);
      showNotification('Failed to start network discovery', 'error');
    }
  }, [showNotification]);

  const clearAllDevices = useCallback(async () => {
    try {
      const result = await api.clearAllDevices();
      
      // Clear devices from state immediately
      setDevices([]);
      
      // Reset network stats
      setNetworkStats({
        total_devices: 0,
        online_devices: 0,
        offline_devices: 0,
        new_devices_today: 0,
        unresolved_alerts: 0
      });
      
      showNotification(
        `Successfully cleared ${result.devices_cleared} devices`,
        'success'
      );
      
      return result;
    } catch (error) {
      console.error('Error clearing devices:', error);
      showNotification('Failed to clear devices', 'error');
      throw error;
    }
  }, [showNotification]);

  const startGlobalMonitoring = useCallback(async () => {
    try {
      const result = await api.startMonitoring(); // This will also update global state
      setMonitoringStatus('active');
      showNotification('Global monitoring started', 'success');
      
      // Refresh device list to get updated monitoring status
      const devicesResponse = await api.getDevices();
      setDevices(devicesResponse.results || devicesResponse);
      
      return result;
    } catch (error) {
      console.error('Error starting global monitoring:', error);
      showNotification('Failed to start global monitoring', 'error');
      throw error;
    }
  }, [showNotification]);

  const stopGlobalMonitoring = useCallback(async () => {
    try {
      const result = await api.stopMonitoring(); // This will also update global state
      setMonitoringStatus('inactive');
      showNotification('Global monitoring stopped', 'warning');
      
      // Refresh device list to get updated monitoring status
      const devicesResponse = await api.getDevices();
      setDevices(devicesResponse.results || devicesResponse);
      
      return result;
    } catch (error) {
      console.error('Error stopping global monitoring:', error);
      showNotification('Failed to stop global monitoring', 'error');
      throw error;
    }
  }, [showNotification]);

  // Computed values
  const onlineDevices = devices.filter(device => device.status === 'online');
  const offlineDevices = devices.filter(device => device.status === 'offline');
  const unknownDevices = devices.filter(device => device.status === 'unknown');

  const devicesByType = devices.reduce((acc, device) => {
    acc[device.device_type] = (acc[device.device_type] || 0) + 1;
    return acc;
  }, {});

  // Get connection status display info
  const getConnectionInfo = () => {
    switch (connectionStatus) {
      case 'initializing':
        return { status: 'initializing', color: 'info', text: 'Initializing...' };
      case 'loading':
        return { status: 'loading', color: 'info', text: 'Loading data...' };
      case 'connecting':
        return { status: 'connecting', color: 'warning', text: 'Connecting...' };
      case 'connected':
        return { status: 'connected', color: 'success', text: 'Real-time connected' };
      case 'reconnecting':
        return { status: 'reconnecting', color: 'warning', text: 'Reconnecting...' };
      case 'polling':
        return { status: 'polling', color: 'success', text: 'Polling mode (10s updates)' };
      case 'websocket_failed':
        return { status: 'polling', color: 'success', text: 'Polling mode (10s updates)' };
      case 'error':
        return { status: 'error', color: 'error', text: 'Connection error' };
      default:
        return { status: 'unknown', color: 'default', text: 'Unknown status' };
    }
  };

  return {
    // State
    devices,
    networkStats,
    connectionStatus,
    connectionInfo: getConnectionInfo(),
    notifications,
    monitoringStatus,
    
    // Computed values
    onlineDevices,
    offlineDevices,
    unknownDevices,
    devicesByType,
    
    // Actions
    toggleDeviceMonitoring,
    pingDevice,
    scanDevicePorts,
    startNetworkDiscovery,
    clearAllDevices,
    startGlobalMonitoring,
    stopGlobalMonitoring,
    
    // Connection management
    reconnect: connectWebSocket,
    
    // Utility
    showNotification
  };
};

export default useRealTimeDevices; 