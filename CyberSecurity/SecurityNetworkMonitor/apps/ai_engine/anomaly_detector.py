"""
Professional Anomaly Detection System
Neural network-based behavioral analysis for cybersecurity
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import joblib
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Professional AI-powered anomaly detection system
    Learns normal network behavior and detects deviations
    """
    
    def __init__(self, model_path: str = "models/anomaly_detector"):
        self.model_path = model_path
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% of variance
        self.baseline_stats = {}
        self.behavioral_patterns = defaultdict(list)
        self.is_trained = False
        self.contamination = 0.1  # Expected anomaly rate
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load existing model if available
        self._load_model()
    
    def learn_baseline(self, security_events: List[Dict], network_data: List[Dict] = None) -> Dict:
        """
        Learn normal network behavior patterns
        """
        logger.info(f"Learning baseline from {len(security_events)} events")
        
        # Extract behavioral features
        features_df = self._extract_behavioral_features(security_events)
        
        # Calculate baseline statistics
        self.baseline_stats = {
            'events_per_hour': self._calculate_hourly_patterns(security_events),
            'severity_distribution': self._calculate_severity_distribution(security_events),
            'device_activity': self._calculate_device_activity(security_events),
            'event_type_patterns': self._calculate_event_type_patterns(security_events),
            'temporal_patterns': self._calculate_temporal_patterns(security_events)
        }
        
        # Train anomaly detection models
        if len(features_df) > 10:  # Need minimum samples
            # Scale features
            X_scaled = self.scaler.fit_transform(features_df)
            
            # Apply PCA for dimensionality reduction
            X_pca = self.pca.fit_transform(X_scaled)
            
            # Train Isolation Forest
            self.isolation_forest = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
            self.isolation_forest.fit(X_pca)
            
            self.is_trained = True
            self._save_model()
            
            logger.info("Baseline learning completed successfully")
            
            return {
                'baseline_events': len(security_events),
                'feature_dimensions': X_pca.shape[1],
                'contamination_rate': self.contamination,
                'training_completed': True,
                'timestamp': datetime.now().isoformat()
            }
        else:
            logger.warning("Insufficient data for baseline learning")
            return {
                'baseline_events': len(security_events),
                'training_completed': False,
                'error': 'Insufficient data'
            }
    
    def detect_anomalies(self, current_events: List[Dict]) -> Dict:
        """
        Detect anomalies in current network behavior
        """
        if not self.is_trained:
            return {
                'anomalies_detected': 0,
                'anomaly_score': 0.0,
                'status': 'not_trained',
                'details': []
            }
        
        anomalies = []
        total_anomaly_score = 0.0
        
        # Extract features for current events
        features_df = self._extract_behavioral_features(current_events)
        
        if len(features_df) > 0:
            # Scale and transform features
            X_scaled = self.scaler.transform(features_df)
            X_pca = self.pca.transform(X_scaled)
            
            # Detect anomalies using Isolation Forest
            anomaly_scores = self.isolation_forest.decision_function(X_pca)
            predictions = self.isolation_forest.predict(X_pca)
            
            # Analyze each event
            for i, (event, score, prediction) in enumerate(zip(current_events, anomaly_scores, predictions)):
                if prediction == -1:  # Anomaly detected
                    anomaly_detail = {
                        'event_id': event.get('id'),
                        'anomaly_score': float(-score),  # Convert to positive score
                        'anomaly_type': self._classify_anomaly_type(event, score),
                        'explanation': self._generate_anomaly_explanation(event, score),
                        'severity': self._calculate_anomaly_severity(score),
                        'timestamp': event.get('timestamp'),
                        'device_ip': event.get('source_device_ip') or event.get('target_device_ip')
                    }
                    anomalies.append(anomaly_detail)
                    total_anomaly_score += float(-score)
        
        # Additional behavioral anomaly checks
        behavioral_anomalies = self._detect_behavioral_anomalies(current_events)
        anomalies.extend(behavioral_anomalies)
        
        # Calculate overall anomaly score
        overall_score = min(total_anomaly_score / max(len(current_events), 1), 1.0)
        
        return {
            'anomalies_detected': len(anomalies),
            'anomaly_score': overall_score,
            'status': 'active',
            'details': anomalies,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def update_baseline(self, new_events: List[Dict]) -> Dict:
        """
        Update baseline with new normal behavior data
        """
        logger.info(f"Updating baseline with {len(new_events)} new events")
        
        # Filter out anomalous events for baseline update
        normal_events = []
        for event in new_events:
            if not self._is_likely_anomaly(event):
                normal_events.append(event)
        
        if normal_events:
            # Re-learn baseline with combined data
            return self.learn_baseline(normal_events)
        else:
            return {
                'baseline_updated': False,
                'reason': 'No normal events found in new data'
            }
    
    def _extract_behavioral_features(self, events: List[Dict]) -> pd.DataFrame:
        """
        Extract behavioral features for anomaly detection
        """
        if not events:
            return pd.DataFrame()
        
        # Group events by time windows
        hourly_features = self._extract_hourly_features(events)
        device_features = self._extract_device_features(events)
        pattern_features = self._extract_pattern_features(events)
        
        # Combine all features
        all_features = []
        
        # Create feature vectors for each hour
        for hour_data in hourly_features:
            # Reconstruct hour key from numerical components for helper methods
            hour_key = f"{hour_data['month_of_year']:02d}-{hour_data['day_of_month']:02d}-{hour_data['hour_of_day']:02d}"
            
            feature_vector = {
                **hour_data,
                **self._get_device_features_for_hour(device_features, hour_key),
                **self._get_pattern_features_for_hour(pattern_features, hour_key)
            }
            all_features.append(feature_vector)
        
        return pd.DataFrame(all_features)
    
    def _extract_hourly_features(self, events: List[Dict]) -> List[Dict]:
        """
        Extract hourly behavioral features
        """
        hourly_data = defaultdict(lambda: {
            'event_count': 0,
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'unique_devices': set(),
            'event_types': set()
        })
        
        for event in events:
            try:
                timestamp = pd.to_datetime(event.get('timestamp'))
                hour_key = timestamp.strftime('%Y-%m-%d-%H')
                
                hourly_data[hour_key]['event_count'] += 1
                
                severity = event.get('severity', 'low')
                hourly_data[hour_key][f'{severity}_count'] += 1
                
                device_ip = event.get('source_device_ip') or event.get('target_device_ip')
                if device_ip:
                    hourly_data[hour_key]['unique_devices'].add(device_ip)
                
                event_type = event.get('event_type')
                if event_type:
                    hourly_data[hour_key]['event_types'].add(event_type)
                    
            except Exception as e:
                logger.warning(f"Error processing event timestamp: {e}")
                continue
        
        # Convert to feature list
        features = []
        for hour_key, data in hourly_data.items():
            # Extract numerical time features from hour_key (e.g., '2025-06-06-18')
            try:
                parts = hour_key.split('-')
                if len(parts) >= 4:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    hour = int(parts[3])
                else:
                    # Fallback to current time if parsing fails
                    now = datetime.now()
                    year, month, day, hour = now.year, now.month, now.day, now.hour
            except (ValueError, IndexError):
                # Fallback to current time if parsing fails
                now = datetime.now()
                year, month, day, hour = now.year, now.month, now.day, now.hour
            
            features.append({
                'hour_of_day': hour,
                'day_of_month': day,
                'month_of_year': month,
                'event_count': data['event_count'],
                'critical_ratio': data['critical_count'] / max(data['event_count'], 1),
                'high_ratio': data['high_count'] / max(data['event_count'], 1),
                'medium_ratio': data['medium_count'] / max(data['event_count'], 1),
                'low_ratio': data['low_count'] / max(data['event_count'], 1),
                'unique_devices_count': len(data['unique_devices']),
                'unique_event_types': len(data['event_types']),
                'device_diversity': len(data['unique_devices']) / max(data['event_count'], 1),
                'type_diversity': len(data['event_types']) / max(data['event_count'], 1)
            })
        
        return features
    
    def _extract_device_features(self, events: List[Dict]) -> Dict:
        """
        Extract device-specific behavioral features
        """
        device_stats = defaultdict(lambda: {
            'event_count': 0,
            'severity_scores': [],
            'event_types': set(),
            'timestamps': []
        })
        
        for event in events:
            device_ip = event.get('source_device_ip') or event.get('target_device_ip')
            if device_ip:
                device_stats[device_ip]['event_count'] += 1
                
                severity_score = self._severity_to_score(event.get('severity', 'low'))
                device_stats[device_ip]['severity_scores'].append(severity_score)
                
                event_type = event.get('event_type')
                if event_type:
                    device_stats[device_ip]['event_types'].add(event_type)
                
                timestamp = event.get('timestamp')
                if timestamp:
                    device_stats[device_ip]['timestamps'].append(timestamp)
        
        return dict(device_stats)
    
    def _extract_pattern_features(self, events: List[Dict]) -> Dict:
        """
        Extract pattern-based features
        """
        patterns = {
            'event_sequences': [],
            'time_intervals': [],
            'severity_transitions': [],
            'device_interactions': defaultdict(set)
        }
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda x: x.get('timestamp', ''))
        
        # Analyze sequences
        for i in range(len(sorted_events) - 1):
            current = sorted_events[i]
            next_event = sorted_events[i + 1]
            
            # Event type sequences
            current_type = current.get('event_type')
            next_type = next_event.get('event_type')
            if current_type and next_type:
                patterns['event_sequences'].append(f"{current_type}->{next_type}")
            
            # Time intervals
            try:
                current_time = pd.to_datetime(current.get('timestamp'))
                next_time = pd.to_datetime(next_event.get('timestamp'))
                interval = (next_time - current_time).total_seconds()
                patterns['time_intervals'].append(interval)
            except:
                pass
            
            # Severity transitions
            current_severity = current.get('severity')
            next_severity = next_event.get('severity')
            if current_severity and next_severity:
                patterns['severity_transitions'].append(f"{current_severity}->{next_severity}")
        
        return patterns
    
    def _detect_behavioral_anomalies(self, events: List[Dict]) -> List[Dict]:
        """
        Detect behavioral anomalies using rule-based analysis
        """
        anomalies = []
        
        if not self.baseline_stats:
            return anomalies
        
        # Check for unusual event frequency
        current_hour = datetime.now().hour
        baseline_hourly = self.baseline_stats.get('events_per_hour', {})
        expected_events = baseline_hourly.get(str(current_hour), 0)
        current_events = len(events)
        
        if current_events > expected_events * 3:  # 3x normal rate
            anomalies.append({
                'anomaly_type': 'unusual_frequency',
                'anomaly_score': min((current_events / max(expected_events, 1)) / 3, 1.0),
                'explanation': f"Event frequency ({current_events}) is {current_events/max(expected_events, 1):.1f}x normal",
                'severity': 'high' if current_events > expected_events * 5 else 'medium'
            })
        
        # Check for unusual severity distribution
        current_severity_dist = self._calculate_severity_distribution(events)
        baseline_severity_dist = self.baseline_stats.get('severity_distribution', {})
        
        for severity, current_ratio in current_severity_dist.items():
            baseline_ratio = baseline_severity_dist.get(severity, 0)
            if current_ratio > baseline_ratio * 2 and severity in ['critical', 'high']:
                anomalies.append({
                    'anomaly_type': 'unusual_severity_pattern',
                    'anomaly_score': min(current_ratio / max(baseline_ratio, 0.01), 1.0),
                    'explanation': f"Unusual increase in {severity} events: {current_ratio:.2f} vs baseline {baseline_ratio:.2f}",
                    'severity': 'high'
                })
        
        return anomalies
    
    def _severity_to_score(self, severity: str) -> float:
        """Convert severity to numerical score"""
        severity_map = {
            'critical': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25
        }
        return severity_map.get(severity.lower(), 0.0)
    
    def _calculate_hourly_patterns(self, events: List[Dict]) -> Dict:
        """Calculate hourly event patterns"""
        hourly_counts = defaultdict(int)
        
        for event in events:
            try:
                timestamp = pd.to_datetime(event.get('timestamp'))
                hour = timestamp.hour
                hourly_counts[str(hour)] += 1
            except:
                continue
        
        return dict(hourly_counts)
    
    def _calculate_severity_distribution(self, events: List[Dict]) -> Dict:
        """Calculate severity distribution"""
        severity_counts = defaultdict(int)
        total_events = len(events)
        
        for event in events:
            severity = event.get('severity', 'low')
            severity_counts[severity] += 1
        
        # Convert to ratios
        return {
            severity: count / max(total_events, 1) 
            for severity, count in severity_counts.items()
        }
    
    def _calculate_device_activity(self, events: List[Dict]) -> Dict:
        """Calculate device activity patterns"""
        device_counts = defaultdict(int)
        
        for event in events:
            device_ip = event.get('source_device_ip') or event.get('target_device_ip')
            if device_ip:
                device_counts[device_ip] += 1
        
        return dict(device_counts)
    
    def _calculate_event_type_patterns(self, events: List[Dict]) -> Dict:
        """Calculate event type patterns"""
        type_counts = defaultdict(int)
        
        for event in events:
            event_type = event.get('event_type')
            if event_type:
                type_counts[event_type] += 1
        
        return dict(type_counts)
    
    def _calculate_temporal_patterns(self, events: List[Dict]) -> Dict:
        """Calculate temporal patterns"""
        patterns = {
            'day_of_week': defaultdict(int),
            'hour_of_day': defaultdict(int)
        }
        
        for event in events:
            try:
                timestamp = pd.to_datetime(event.get('timestamp'))
                patterns['day_of_week'][timestamp.dayofweek] += 1
                patterns['hour_of_day'][timestamp.hour] += 1
            except:
                continue
        
        return {
            'day_of_week': dict(patterns['day_of_week']),
            'hour_of_day': dict(patterns['hour_of_day'])
        }
    
    def _classify_anomaly_type(self, event: Dict, score: float) -> str:
        """Classify the type of anomaly"""
        if abs(score) > 0.8:
            return 'severe_anomaly'
        elif abs(score) > 0.6:
            return 'moderate_anomaly'
        else:
            return 'mild_anomaly'
    
    def _generate_anomaly_explanation(self, event: Dict, score: float) -> str:
        """Generate human-readable explanation for anomaly"""
        severity = event.get('severity', 'unknown')
        event_type = event.get('event_type', 'unknown')
        device_ip = event.get('source_device_ip') or event.get('target_device_ip', 'unknown')
        
        return f"Unusual {severity} {event_type} event from {device_ip} (anomaly score: {abs(score):.3f})"
    
    def _calculate_anomaly_severity(self, score: float) -> str:
        """Calculate severity level for anomaly"""
        abs_score = abs(score)
        if abs_score > 0.8:
            return 'critical'
        elif abs_score > 0.6:
            return 'high'
        elif abs_score > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _is_likely_anomaly(self, event: Dict) -> bool:
        """Quick check if event is likely an anomaly"""
        # Simple heuristic - in production, use more sophisticated logic
        severity = event.get('severity', 'low')
        return severity in ['critical', 'high']
    
    def _get_device_features_for_hour(self, device_features: Dict, hour: str) -> Dict:
        """Get device features for specific hour"""
        # Simplified - in production, properly time-align features
        return {
            'active_devices': len(device_features),
            'avg_device_events': np.mean([data['event_count'] for data in device_features.values()]) if device_features else 0
        }
    
    def _get_pattern_features_for_hour(self, pattern_features: Dict, hour: str) -> Dict:
        """Get pattern features for specific hour"""
        return {
            'unique_sequences': len(set(pattern_features.get('event_sequences', []))),
            'avg_time_interval': np.mean(pattern_features.get('time_intervals', [0])),
            'unique_transitions': len(set(pattern_features.get('severity_transitions', [])))
        }
    
    def _save_model(self):
        """Save the trained model"""
        try:
            model_data = {
                'isolation_forest': self.isolation_forest,
                'scaler': self.scaler,
                'pca': self.pca,
                'baseline_stats': self.baseline_stats,
                'behavioral_patterns': dict(self.behavioral_patterns),
                'is_trained': self.is_trained,
                'contamination': self.contamination,
                'timestamp': datetime.now().isoformat()
            }
            joblib.dump(model_data, f"{self.model_path}.pkl")
            logger.info(f"Anomaly detection model saved to {self.model_path}.pkl")
        except Exception as e:
            logger.error(f"Failed to save anomaly detection model: {e}")
    
    def _load_model(self):
        """Load existing model"""
        try:
            if os.path.exists(f"{self.model_path}.pkl"):
                model_data = joblib.load(f"{self.model_path}.pkl")
                self.isolation_forest = model_data.get('isolation_forest')
                self.scaler = model_data.get('scaler')
                self.pca = model_data.get('pca')
                self.baseline_stats = model_data.get('baseline_stats', {})
                self.behavioral_patterns = defaultdict(list, model_data.get('behavioral_patterns', {}))
                self.is_trained = model_data.get('is_trained', False)
                self.contamination = model_data.get('contamination', 0.1)
                logger.info(f"Anomaly detection model loaded from {self.model_path}.pkl")
        except Exception as e:
            logger.warning(f"Could not load existing anomaly detection model: {e}") 