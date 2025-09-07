"""
Professional AI Manager
Central coordinator for all AI/ML components in cybersecurity system
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
from concurrent.futures import ThreadPoolExecutor

from .threat_detector import ThreatDetector
from .anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class AIManager:
    """
    Central AI management system for cybersecurity monitoring
    Coordinates threat detection, anomaly detection, and continuous learning
    """
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.threat_detector = ThreatDetector(f"{models_dir}/threat_detector")
        self.anomaly_detector = AnomalyDetector(f"{models_dir}/anomaly_detector")
        
        # AI system state
        self.is_learning = False
        self.last_training = None
        self.performance_metrics = {}
        self.learning_schedule = {
            'auto_retrain_hours': 24,  # Retrain every 24 hours
            'min_new_events': 50,      # Minimum events needed for retraining
            'learning_enabled': True
        }
        
        # Thread pool for async AI operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        logger.info("AI Manager initialized successfully")
    
    async def initialize_ai_system(self, historical_events: List[Dict]) -> Dict:
        """
        Initialize the AI system with historical data
        """
        logger.info(f"Initializing AI system with {len(historical_events)} historical events")
        
        try:
            # Train threat detector
            threat_results = await self._async_train_threat_detector(historical_events)
            
            # Learn baseline for anomaly detection
            anomaly_results = await self._async_learn_baseline(historical_events)
            
            # Update system state
            self.last_training = datetime.now()
            self.performance_metrics = {
                'threat_detector': threat_results,
                'anomaly_detector': anomaly_results,
                'initialization_time': datetime.now().isoformat(),
                'total_training_events': len(historical_events)
            }
            
            logger.info("AI system initialization completed successfully")
            
            return {
                'status': 'success',
                'threat_detector_trained': self.threat_detector.is_trained,
                'anomaly_detector_trained': anomaly_results.get('training_completed', False),
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            logger.error(f"AI system initialization failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'threat_detector_trained': False,
                'anomaly_detector_trained': False
            }
    
    async def analyze_security_event(self, event: Dict) -> Dict:
        """
        Comprehensive AI analysis of a single security event
        """
        try:
            # Run threat detection and anomaly detection in parallel
            threat_task = self._async_predict_threat(event)
            anomaly_task = self._async_detect_event_anomaly(event)
            
            threat_result, anomaly_result = await asyncio.gather(
                threat_task, anomaly_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(threat_result, Exception):
                logger.error(f"Threat detection failed: {threat_result}")
                threat_result = {'error': str(threat_result)}
            
            if isinstance(anomaly_result, Exception):
                logger.error(f"Anomaly detection failed: {anomaly_result}")
                anomaly_result = {'error': str(anomaly_result)}
            
            # Combine results
            ai_analysis = {
                'event_id': event.get('id'),
                'timestamp': datetime.now().isoformat(),
                'threat_analysis': threat_result,
                'anomaly_analysis': anomaly_result,
                'combined_risk_score': self._calculate_combined_risk_score(threat_result, anomaly_result),
                'ai_recommendations': self._generate_recommendations(threat_result, anomaly_result, event)
            }
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed for event {event.get('id')}: {e}")
            return {
                'event_id': event.get('id'),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def analyze_security_events_batch(self, events: List[Dict]) -> Dict:
        """
        Analyze multiple security events for patterns and anomalies
        """
        logger.info(f"Analyzing batch of {len(events)} security events")
        
        try:
            # Individual event analysis
            individual_analyses = []
            for event in events:
                analysis = await self.analyze_security_event(event)
                individual_analyses.append(analysis)
            
            # Batch anomaly detection
            batch_anomalies = await self._async_detect_batch_anomalies(events)
            
            # Pattern analysis
            patterns = self._analyze_event_patterns(events, individual_analyses)
            
            # Generate batch insights
            insights = self._generate_batch_insights(individual_analyses, batch_anomalies, patterns)
            
            return {
                'batch_size': len(events),
                'analysis_timestamp': datetime.now().isoformat(),
                'individual_analyses': individual_analyses,
                'batch_anomalies': batch_anomalies,
                'patterns': patterns,
                'insights': insights,
                'overall_risk_level': self._calculate_overall_risk_level(individual_analyses)
            }
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return {
                'error': str(e),
                'batch_size': len(events),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    async def continuous_learning_update(self, new_events: List[Dict]) -> Dict:
        """
        Update AI models with new events (continuous learning)
        """
        if not self.learning_schedule['learning_enabled']:
            return {'status': 'learning_disabled'}
        
        if len(new_events) < self.learning_schedule['min_new_events']:
            return {
                'status': 'insufficient_data',
                'events_received': len(new_events),
                'min_required': self.learning_schedule['min_new_events']
            }
        
        logger.info(f"Starting continuous learning with {len(new_events)} new events")
        
        try:
            self.is_learning = True
            
            # Update threat detector
            threat_update = await self._async_update_threat_detector(new_events)
            
            # Update anomaly detector baseline
            anomaly_update = await self._async_update_anomaly_baseline(new_events)
            
            # Update performance metrics
            self.performance_metrics.update({
                'last_learning_update': datetime.now().isoformat(),
                'learning_events_count': len(new_events),
                'threat_detector_update': threat_update,
                'anomaly_detector_update': anomaly_update
            })
            
            self.last_training = datetime.now()
            self.is_learning = False
            
            logger.info("Continuous learning update completed")
            
            return {
                'status': 'success',
                'events_processed': len(new_events),
                'threat_detector_updated': threat_update.get('training_completed', False),
                'anomaly_detector_updated': anomaly_update.get('baseline_updated', False),
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            self.is_learning = False
            logger.error(f"Continuous learning failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'events_processed': len(new_events)
            }
    
    def get_ai_system_status(self) -> Dict:
        """
        Get current AI system status and performance metrics
        """
        return {
            'system_status': {
                'threat_detector_trained': self.threat_detector.is_trained,
                'anomaly_detector_trained': self.anomaly_detector.is_trained,
                'is_learning': self.is_learning,
                'last_training': self.last_training.isoformat() if self.last_training else None,
                'models_directory': self.models_dir
            },
            'learning_configuration': self.learning_schedule,
            'performance_metrics': self.performance_metrics,
            'capabilities': {
                'threat_classification': self.threat_detector.is_trained,
                'anomaly_detection': self.anomaly_detector.is_trained,
                'continuous_learning': self.learning_schedule['learning_enabled'],
                'real_time_analysis': True,
                'batch_processing': True
            }
        }
    
    def configure_learning_schedule(self, config: Dict) -> Dict:
        """
        Configure AI learning parameters
        """
        old_config = self.learning_schedule.copy()
        
        # Update configuration
        if 'auto_retrain_hours' in config:
            self.learning_schedule['auto_retrain_hours'] = config['auto_retrain_hours']
        
        if 'min_new_events' in config:
            self.learning_schedule['min_new_events'] = config['min_new_events']
        
        if 'learning_enabled' in config:
            self.learning_schedule['learning_enabled'] = config['learning_enabled']
        
        logger.info(f"Learning schedule updated: {self.learning_schedule}")
        
        return {
            'status': 'updated',
            'old_config': old_config,
            'new_config': self.learning_schedule
        }
    
    async def _async_train_threat_detector(self, events: List[Dict]) -> Dict:
        """Async wrapper for threat detector training"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.threat_detector.train, 
            events
        )
    
    async def _async_learn_baseline(self, events: List[Dict]) -> Dict:
        """Async wrapper for anomaly detector baseline learning"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.anomaly_detector.learn_baseline, 
            events
        )
    
    async def _async_predict_threat(self, event: Dict) -> Dict:
        """Async wrapper for threat prediction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.threat_detector.predict_threat, 
            event
        )
    
    async def _async_detect_event_anomaly(self, event: Dict) -> Dict:
        """Async wrapper for single event anomaly detection"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.anomaly_detector.detect_anomalies, 
            [event]
        )
    
    async def _async_detect_batch_anomalies(self, events: List[Dict]) -> Dict:
        """Async wrapper for batch anomaly detection"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.anomaly_detector.detect_anomalies, 
            events
        )
    
    async def _async_update_threat_detector(self, events: List[Dict]) -> Dict:
        """Async wrapper for threat detector continuous learning"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.threat_detector.continuous_learning, 
            events
        )
    
    async def _async_update_anomaly_baseline(self, events: List[Dict]) -> Dict:
        """Async wrapper for anomaly detector baseline update"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.anomaly_detector.update_baseline, 
            events
        )
    
    def _calculate_combined_risk_score(self, threat_result: Dict, anomaly_result: Dict) -> float:
        """
        Calculate combined risk score from threat and anomaly analysis
        """
        try:
            threat_score = threat_result.get('ai_score', 0) / 100.0
            anomaly_score = anomaly_result.get('anomaly_score', 0)
            
            # Weighted combination (70% threat, 30% anomaly)
            combined_score = (threat_score * 0.7) + (anomaly_score * 0.3)
            
            return min(combined_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate combined risk score: {e}")
            return 0.0
    
    def _generate_recommendations(self, threat_result: Dict, anomaly_result: Dict, event: Dict) -> List[str]:
        """
        Generate AI-powered recommendations based on analysis
        """
        recommendations = []
        
        try:
            # Threat-based recommendations
            threat_level = threat_result.get('threat_level', 'unknown')
            confidence = threat_result.get('confidence', 0)
            
            if threat_level == 'critical_threat' and confidence > 0.8:
                recommendations.append("🚨 IMMEDIATE ACTION: Isolate affected device from network")
                recommendations.append("🔍 Conduct forensic analysis of device")
                recommendations.append("📋 Review security logs for related activities")
            
            elif threat_level == 'high_threat' and confidence > 0.7:
                recommendations.append("⚠️ HIGH PRIORITY: Investigate device activity")
                recommendations.append("🛡️ Increase monitoring for this device")
                recommendations.append("🔒 Consider temporary access restrictions")
            
            # Anomaly-based recommendations
            anomaly_count = anomaly_result.get('anomalies_detected', 0)
            if anomaly_count > 0:
                recommendations.append(f"🔍 Investigate {anomaly_count} detected anomalies")
                recommendations.append("📊 Review baseline behavior patterns")
            
            # Event-specific recommendations
            severity = event.get('severity', 'low')
            if severity == 'critical':
                recommendations.append("🚨 Escalate to security team immediately")
            
            # Default recommendation if none generated
            if not recommendations:
                recommendations.append("📝 Monitor event and update threat intelligence")
            
        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            recommendations.append("⚠️ Manual review recommended")
        
        return recommendations
    
    def _analyze_event_patterns(self, events: List[Dict], analyses: List[Dict]) -> Dict:
        """
        Analyze patterns across multiple events
        """
        patterns = {
            'temporal_clustering': False,
            'device_clustering': False,
            'severity_escalation': False,
            'attack_chain_detected': False
        }
        
        try:
            # Check for temporal clustering (multiple events in short time)
            timestamps = []
            for event in events:
                try:
                    timestamp = datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))
                    timestamps.append(timestamp)
                except:
                    continue
            
            if len(timestamps) > 1:
                timestamps.sort()
                time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
                avg_diff = sum(time_diffs) / len(time_diffs)
                if avg_diff < 300:  # Less than 5 minutes average
                    patterns['temporal_clustering'] = True
            
            # Check for device clustering
            devices = set()
            for event in events:
                device_ip = event.get('source_device_ip') or event.get('target_device_ip')
                if device_ip:
                    devices.add(device_ip)
            
            if len(devices) < len(events) * 0.5:  # Same devices involved in multiple events
                patterns['device_clustering'] = True
            
            # Check for severity escalation
            severities = [event.get('severity', 'low') for event in events]
            severity_scores = [self._severity_to_score(s) for s in severities]
            if len(severity_scores) > 1:
                escalation_trend = all(severity_scores[i] <= severity_scores[i+1] for i in range(len(severity_scores)-1))
                patterns['severity_escalation'] = escalation_trend
            
        except Exception as e:
            logger.warning(f"Pattern analysis failed: {e}")
        
        return patterns
    
    def _generate_batch_insights(self, analyses: List[Dict], anomalies: Dict, patterns: Dict) -> List[str]:
        """
        Generate insights from batch analysis
        """
        insights = []
        
        try:
            # High-risk events insight
            high_risk_count = sum(1 for analysis in analyses 
                                if analysis.get('combined_risk_score', 0) > 0.7)
            
            if high_risk_count > 0:
                insights.append(f"🚨 {high_risk_count} high-risk events detected requiring immediate attention")
            
            # Anomaly insights
            anomaly_count = anomalies.get('anomalies_detected', 0)
            if anomaly_count > 0:
                insights.append(f"🔍 {anomaly_count} behavioral anomalies detected")
            
            # Pattern insights
            if patterns.get('temporal_clustering'):
                insights.append("⏰ Temporal clustering detected - possible coordinated attack")
            
            if patterns.get('device_clustering'):
                insights.append("🖥️ Multiple events from same devices - possible compromised systems")
            
            if patterns.get('severity_escalation'):
                insights.append("📈 Severity escalation pattern detected - attack may be progressing")
            
            # Overall assessment
            total_events = len(analyses)
            if total_events > 50:
                insights.append(f"📊 High activity period: {total_events} events analyzed")
            
        except Exception as e:
            logger.warning(f"Insight generation failed: {e}")
            insights.append("⚠️ Manual analysis recommended")
        
        return insights
    
    def _calculate_overall_risk_level(self, analyses: List[Dict]) -> str:
        """
        Calculate overall risk level for the batch
        """
        try:
            if not analyses:
                return 'unknown'
            
            risk_scores = [analysis.get('combined_risk_score', 0) for analysis in analyses]
            avg_risk = sum(risk_scores) / len(risk_scores)
            max_risk = max(risk_scores)
            
            if max_risk > 0.9 or avg_risk > 0.7:
                return 'critical'
            elif max_risk > 0.7 or avg_risk > 0.5:
                return 'high'
            elif max_risk > 0.5 or avg_risk > 0.3:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.warning(f"Risk level calculation failed: {e}")
            return 'unknown'
    
    def _severity_to_score(self, severity: str) -> float:
        """Convert severity to numerical score"""
        severity_map = {
            'critical': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25
        }
        return severity_map.get(severity.lower(), 0.0)
    
    def __del__(self):
        """Cleanup resources"""
        try:
            self.executor.shutdown(wait=False)
        except:
            pass 