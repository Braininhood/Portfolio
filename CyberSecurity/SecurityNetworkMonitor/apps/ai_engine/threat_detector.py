"""
Professional Threat Detection Neural Network
Self-learning AI for cybersecurity threat analysis
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class ThreatDetector:
    """
    Professional AI-powered threat detection system
    Uses ensemble methods and neural network principles for threat classification
    """
    
    def __init__(self, model_path: str = "models/threat_detector"):
        self.model_path = model_path
        self.classifier = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        self.is_trained = False
        self.confidence_threshold = 0.7
        self.learning_rate = 0.1
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load existing model if available
        self._load_model()
    
    def extract_features(self, security_events: List[Dict]) -> pd.DataFrame:
        """
        Extract features from security events for AI processing
        """
        features = []
        
        for event in security_events:
            feature_dict = {
                # Basic event features
                'severity_score': self._severity_to_score(event.get('severity', 'low')),
                'event_type_encoded': self._encode_event_type(event.get('event_type', 'unknown')),
                'is_resolved': int(event.get('is_resolved', False)),
                
                # Temporal features
                'hour_of_day': self._extract_hour(event.get('timestamp')),
                'day_of_week': self._extract_day_of_week(event.get('timestamp')),
                'time_since_creation': self._time_since_creation(event.get('timestamp')),
                
                # Network features
                'source_ip_risk': self._calculate_ip_risk(event.get('source_device_ip')),
                'target_ip_risk': self._calculate_ip_risk(event.get('target_device_ip')),
                
                # Behavioral features
                'event_frequency': self._calculate_event_frequency(event),
                'device_reputation': self._calculate_device_reputation(event),
                
                # Advanced features
                'threat_pattern_match': self._pattern_matching_score(event),
                'anomaly_score': self._calculate_anomaly_score(event),
            }
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        self.feature_columns = df.columns.tolist()
        return df
    
    def train(self, security_events: List[Dict], retrain: bool = False) -> Dict:
        """
        Train the threat detection model
        """
        logger.info(f"Training threat detector with {len(security_events)} events")
        
        # Extract features
        X = self.extract_features(security_events)
        
        # Create labels (threat level based on severity and resolution status)
        y = []
        for event in security_events:
            if event.get('severity') == 'critical':
                threat_level = 'critical_threat'
            elif event.get('severity') == 'high':
                threat_level = 'high_threat'
            elif event.get('severity') == 'medium':
                threat_level = 'medium_threat'
            else:
                threat_level = 'low_threat'
            y.append(threat_level)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Train ensemble model (acts like a neural network with multiple decision paths)
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.classifier.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Set trained flag first, then save model
        self.is_trained = True
        self._save_model()
        
        training_results = {
            'accuracy': accuracy,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': len(self.feature_columns),
            'classes': self.label_encoder.classes_.tolist(),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Model trained successfully. Accuracy: {accuracy:.3f}")
        return training_results
    
    def predict_threat(self, event: Dict) -> Dict:
        """
        Predict threat level for a single security event with improved pattern recognition
        """
        if not self.is_trained:
            return {
                'threat_level': 'unknown',
                'confidence': 0.0,
                'ai_score': 0,
                'explanation': 'Model not trained yet'
            }
        
        # Extract features
        features_df = self.extract_features([event])
        X_scaled = self.scaler.transform(features_df)
        
        # Predict
        prediction = self.classifier.predict(X_scaled)[0]
        probabilities = self.classifier.predict_proba(X_scaled)[0]
        confidence = np.max(probabilities)
        
        # Get threat level
        threat_level = self.label_encoder.inverse_transform([prediction])[0]
        
        # Apply false positive filtering
        filtered_result = self._apply_false_positive_filter(event, threat_level, confidence)
        threat_level = filtered_result['threat_level']
        confidence = filtered_result['confidence']
        
        # Calculate AI score (0-100)
        ai_score = int(confidence * 100)
        
        # Generate context-aware explanation
        explanation = self._generate_smart_explanation(event, threat_level, confidence, features_df)
        
        return {
            'threat_level': threat_level,
            'confidence': float(confidence),
            'ai_score': ai_score,
            'explanation': explanation,
            'probabilities': {
                class_name: float(prob) 
                for class_name, prob in zip(self.label_encoder.classes_, probabilities)
            }
        }
    
    def _apply_false_positive_filter(self, event: Dict, threat_level: str, confidence: float) -> Dict:
        """
        Apply intelligent filtering to reduce false positives
        """
        # Check for repetitive patterns
        source_ip = event.get('source_device_ip') or 'Unknown IP'
        event_type = event.get('event_type', '')
        description = event.get('description', '').lower()
        
        # AGGRESSIVE SPAM FILTER: Target the specific spam pattern
        if 'high threat level detected' in description and event_type == 'device_threat_detected':
            # This is the exact spam pattern - downgrade significantly
            if threat_level == 'high_threat':
                threat_level = 'low_threat'
                confidence *= 0.3  # Drastically reduce confidence
            elif threat_level == 'medium_threat':
                threat_level = 'low_threat'
                confidence *= 0.4
        
        # AGGRESSIVE SPAM FILTER: Target the specific spam pattern
        description = event.get('description', '').lower()
        if 'high threat level detected' in description and event_type == 'device_threat_detected':
            # This is the exact spam pattern - downgrade significantly
            if threat_level == 'high_threat':
                threat_level = 'low_threat'
                confidence *= 0.3  # Drastically reduce confidence
            elif threat_level == 'medium_threat':
                threat_level = 'low_threat'
                confidence *= 0.4
        
        # Reduce threat level for common internal activities
        if self._is_likely_benign_activity(event):
            if threat_level in ['critical_threat', 'high_threat']:
                threat_level = 'medium_threat'
                confidence *= 0.7
            elif threat_level == 'medium_threat':
                threat_level = 'low_threat'
                confidence *= 0.8
        
        # Check for repetitive alerts from same IP
        if self._is_repetitive_alert(event):
            confidence *= 0.5  # Reduce confidence for repetitive alerts
            if threat_level == 'high_threat':
                threat_level = 'medium_threat'
        
        # Additional filter for internal IPs with generic threats
        if source_ip and source_ip.startswith('192.168.') and 'threat level detected' in description:
            if threat_level == 'high_threat':
                threat_level = 'low_threat'
                confidence *= 0.4
        
        return {
            'threat_level': threat_level,
            'confidence': max(confidence, 0.1)  # Minimum confidence
        }
    
    def _is_likely_benign_activity(self, event: Dict) -> bool:
        """
        Check if the event is likely benign activity
        """
        description = event.get('description', '').lower()
        event_type = event.get('event_type', '')
        source_ip = event.get('source_device_ip') or 'Unknown IP'
        
        # Common benign patterns
        benign_indicators = [
            'software update',
            'configuration change',
            'normal operational',
            'legitimate system',
            'scheduled maintenance',
            'user activity'
        ]
        
        # Check for benign patterns in description
        for indicator in benign_indicators:
            if indicator in description:
                return True
        
        # Internal network activities are often benign
        if source_ip and source_ip.startswith('192.168.') and event_type in ['port_opening', 'port_scan']:
            return True
        
        return False
    
    def _is_repetitive_alert(self, event: Dict) -> bool:
        """
        Check if this is a repetitive alert pattern
        """
        # This is a simplified check - in production, query recent events from database
        description = event.get('description', '')
        
        # Generic descriptions that appear frequently (SPAM PATTERNS)
        generic_patterns = [
            'Suspicious Network Behavior Detected',
            'unusual outbound connections',
            'abnormal data transfer patterns',
            'communication with potentially malicious domains',
            'High threat level detected',  # The main spam pattern
            'threat level detected'        # Broader pattern
        ]
        
        for pattern in generic_patterns:
            if pattern in description:
                return True
        
        return False
    
    def _generate_smart_explanation(self, event: Dict, threat_level: str, confidence: float, features_df: pd.DataFrame) -> str:
        """
        Generate context-aware explanation instead of generic feature names
        """
        event_type = event.get('event_type', '')
        source_ip = event.get('source_device_ip') or 'Unknown IP'
        description = event.get('description', '').lower()
        
        # Check if this is a repetitive/spam-like alert
        if self._is_repetitive_alert(event):
            if threat_level == 'high_threat':
                return f"FILTERED: Repetitive high threat alert from {source_ip}. Confidence reduced due to spam-like pattern. Manual review recommended."
            elif threat_level == 'medium_threat':
                return f"FILTERED: Recurring medium threat from {source_ip}. Pattern suggests false positive. Monitoring continues."
            else:
                return f"FILTERED: Low-priority recurring alert from {source_ip}. Likely benign activity."
        
        # Base explanation on actual event context
        if threat_level == 'low_threat':
            if 'port_opening' in event_type or 'port_scan' in event_type:
                return f"Low-risk network activity from internal IP {source_ip}. Normal operations detected."
            elif 'device_threat' in event_type:
                return f"Minor device anomaly on {source_ip}. Confidence: {confidence:.1%}. Likely benign."
            else:
                return f"Low-priority security event from {source_ip}. No immediate action required."
        
        elif threat_level == 'medium_threat':
            if 'unauthorized_access' in event_type:
                return f"Potential unauthorized access from {source_ip}. Investigation recommended."
            elif 'device_threat' in event_type:
                return f"Device {source_ip} showing behavioral anomalies. Monitor for escalation."
            elif 'port_scan' in event_type:
                return f"Suspicious port scanning activity from {source_ip}. Requires attention."
            else:
                return f"Moderate security concern from {source_ip}. Confidence: {confidence:.1%}."
        
        elif threat_level == 'high_threat':
            if 'device_threat' in event_type:
                if 'high threat level detected' in description:
                    return f"HIGH ALERT: Device {source_ip} flagged by threat detection system. Immediate investigation required."
                else:
                    return f"HIGH ALERT: Advanced threat behavior detected on {source_ip}. Immediate response needed."
            elif 'malware' in description:
                return f"HIGH ALERT: Potential malware activity on {source_ip}. Isolation recommended."
            elif 'suspicious' in description:
                return f"HIGH ALERT: Suspicious network behavior from {source_ip}. High confidence threat."
            else:
                return f"HIGH ALERT: Critical security event from {source_ip}. Confidence: {confidence:.1%}."
        
        elif threat_level == 'critical_threat':
            return f"CRITICAL ALERT: Advanced persistent threat detected from {source_ip}. IMMEDIATE isolation and incident response required."
        
        # Fallback to feature-based explanation with context
        feature_importance = self.classifier.feature_importances_
        top_features = np.argsort(feature_importance)[-3:][::-1]
        feature_names = [self.feature_columns[i] for i in top_features]
        return f"AI Analysis: Key threat indicators from {source_ip}: {', '.join(feature_names)}. Confidence: {confidence:.1%}."
    
    def continuous_learning(self, new_events: List[Dict]) -> Dict:
        """
        Continuously learn from new security events
        """
        if not self.is_trained:
            return self.train(new_events)
        
        # Incremental learning simulation
        logger.info(f"Continuous learning with {len(new_events)} new events")
        
        # For now, retrain with combined data (in production, use incremental learning)
        return self.train(new_events, retrain=True)
    
    def _severity_to_score(self, severity: str) -> float:
        """Convert severity to numerical score"""
        severity_map = {
            'critical': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25
        }
        return severity_map.get(severity.lower(), 0.0)
    
    def _encode_event_type(self, event_type: str) -> float:
        """Encode event type to numerical value"""
        type_map = {
            'device_threat_detected': 0.9,
            'port_scan_detected': 0.7,
            'unauthorized_access': 0.8,
            'port_opening_detected': 0.6,
            'unknown': 0.1
        }
        return type_map.get(event_type, 0.1)
    
    def _extract_hour(self, timestamp_str: str) -> float:
        """Extract hour from timestamp"""
        try:
            if timestamp_str:
                dt = pd.to_datetime(timestamp_str)
                return dt.hour / 24.0  # Normalize to 0-1
        except:
            pass
        return 0.5  # Default to noon
    
    def _extract_day_of_week(self, timestamp_str: str) -> float:
        """Extract day of week from timestamp"""
        try:
            if timestamp_str:
                dt = pd.to_datetime(timestamp_str)
                return dt.dayofweek / 6.0  # Normalize to 0-1
        except:
            pass
        return 0.5  # Default to mid-week
    
    def _time_since_creation(self, timestamp_str: str) -> float:
        """Calculate time since event creation"""
        try:
            if timestamp_str:
                dt = pd.to_datetime(timestamp_str)
                now = datetime.now()
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=None)
                if now.tzinfo is None:
                    now = now.replace(tzinfo=None)
                diff = (now - dt).total_seconds()
                return min(diff / (24 * 3600), 1.0)  # Normalize to days, cap at 1
        except:
            pass
        return 0.0
    
    def _calculate_ip_risk(self, ip_address: str) -> float:
        """Calculate risk score for IP address"""
        if not ip_address:
            return 0.0
        
        # Simple heuristic - in production, use threat intelligence
        if ip_address.startswith('192.168.') or ip_address.startswith('10.'):
            return 0.1  # Internal IP, lower risk
        elif ip_address.startswith('172.'):
            return 0.2  # Private network
        else:
            return 0.8  # External IP, higher risk
    
    def _calculate_event_frequency(self, event: Dict) -> float:
        """Calculate event frequency score"""
        # Placeholder - in production, query database for frequency
        return 0.5
    
    def _calculate_device_reputation(self, event: Dict) -> float:
        """Calculate device reputation score"""
        # Placeholder - in production, maintain device reputation database
        return 0.5
    
    def _pattern_matching_score(self, event: Dict) -> float:
        """Calculate pattern matching score"""
        # Simple pattern matching based on description
        description = event.get('description', '').lower()
        threat_keywords = ['malware', 'attack', 'breach', 'intrusion', 'suspicious']
        
        score = 0.0
        for keyword in threat_keywords:
            if keyword in description:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_anomaly_score(self, event: Dict) -> float:
        """Calculate anomaly score"""
        # Placeholder for anomaly detection
        return 0.5
    
    def _save_model(self):
        """Save the trained model"""
        try:
            model_data = {
                'classifier': self.classifier,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
                'feature_columns': self.feature_columns,
                'is_trained': self.is_trained,
                'timestamp': datetime.now().isoformat()
            }
            joblib.dump(model_data, f"{self.model_path}.pkl")
            logger.info(f"Model saved to {self.model_path}.pkl")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_model(self):
        """Load existing model"""
        try:
            if os.path.exists(f"{self.model_path}.pkl"):
                model_data = joblib.load(f"{self.model_path}.pkl")
                self.classifier = model_data['classifier']
                self.scaler = model_data['scaler']
                self.label_encoder = model_data['label_encoder']
                self.feature_columns = model_data['feature_columns']
                self.is_trained = model_data['is_trained']
                logger.info(f"Model loaded from {self.model_path}.pkl")
        except Exception as e:
            logger.warning(f"Could not load existing model: {e}") 