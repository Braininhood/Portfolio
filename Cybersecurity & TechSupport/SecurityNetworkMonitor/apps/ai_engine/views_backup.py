"""
Django REST API Views for AI Engine Integration
Professional cybersecurity AI endpoints
"""

import asyncio
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import json

from .ai_manager import AIManager
from apps.network_monitor.models import SecurityEvent

logger = logging.getLogger(__name__)

class AIEngineViewSet(viewsets.ViewSet):
    """
    Professional AI Engine API endpoints
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai_manager = AIManager()
    
    @action(detail=False, methods=['post'])
    def initialize_system(self, request):
        """
        Initialize AI system with historical data
        POST /api/v1/ai-engine/initialize_system/
        """
        try:
            # Get historical security events
            security_events = SecurityEvent.objects.select_related(
                'source_device', 'target_device'
            ).all()
            
            events_list = []
            for event in security_events:
                event_dict = {
                    'id': event['id'],
                    'event_type': event['event_type'],
                    'severity': event['severity'],
                    'description': event['description'],
                    'timestamp': event['timestamp'].isoformat() if event['timestamp'] else None,
                    'is_resolved': event['is_resolved'],
                    'source_device_ip': event['source_device_ip'],
                    'target_device_ip': event['target_device_ip']
                }
                events_list.append(event_dict)
            
            # Initialize AI system asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.ai_manager.initialize_ai_system(events_list)
                )
            finally:
                loop.close()
            
            return Response({
                'status': 'success',
                'message': 'AI system initialized successfully',
                'data': result,
                'events_processed': len(events_list)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"AI system initialization failed: {e}")
            return Response({
                'status': 'error',
                'message': f'AI system initialization failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze_event(self, request):
        """
        Analyze a single security event with AI
        POST /api/v1/ai-engine/analyze_event/
        Body: {"event_id": 123} or full event data
        """
        try:
            data = request.data
            
            # Get event data
            if 'event_id' in data:
                try:
                    security_event = SecurityEvent.objects.get(id=data['event_id'])
                    event_data = {
                        'id': security_event.id,
                        'event_type': security_event.event_type,
                        'severity': security_event.severity,
                        'description': security_event.description,
                        'timestamp': security_event.timestamp.isoformat() if security_event.timestamp else None,
                        'is_resolved': security_event.is_resolved,
                        'source_device_ip': security_event.source_device_ip,
                        'target_device_ip': security_event.target_device_ip
                    }
                except SecurityEvent.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'Security event not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                event_data = data
            
            # Analyze event with AI
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                analysis_result = loop.run_until_complete(
                    self.ai_manager.analyze_security_event(event_data)
                )
            finally:
                loop.close()
            
            return Response({
                'status': 'success',
                'message': 'Event analyzed successfully',
                'analysis': analysis_result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Event analysis failed: {e}")
            return Response({
                'status': 'error',
                'message': f'Event analysis failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze_batch(self, request):
        """
        Analyze multiple security events for patterns
        POST /api/v1/ai-engine/analyze_batch/
        Body: {"event_ids": [1,2,3]} or {"limit": 100}
        """
        try:
            data = request.data
            
            # Get events to analyze
            if 'event_ids' in data:
                security_events = SecurityEvent.objects.filter(
                    id__in=data['event_ids']
                ).values(
                    'id', 'event_type', 'severity', 'description', 'timestamp',
                    'is_resolved', 'source_device_ip', 'target_device_ip'
                )
            else:
                limit = data.get('limit', 100)
                security_events = SecurityEvent.objects.all().order_by('-timestamp')[:limit].values(
                    'id', 'event_type', 'severity', 'description', 'timestamp',
                    'is_resolved', 'source_device_ip', 'target_device_ip'
                )
            
            events_list = []
            for event in security_events:
                event_dict = {
                    'id': event['id'],
                    'event_type': event['event_type'],
                    'severity': event['severity'],
                    'description': event['description'],
                    'timestamp': event['timestamp'].isoformat() if event['timestamp'] else None,
                    'is_resolved': event['is_resolved'],
                    'source_device_ip': event['source_device_ip'],
                    'target_device_ip': event['target_device_ip']
                }
                events_list.append(event_dict)
            
            # Analyze batch with AI
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                batch_analysis = loop.run_until_complete(
                    self.ai_manager.analyze_security_events_batch(events_list)
                )
            finally:
                loop.close()
            
            return Response({
                'status': 'success',
                'message': 'Batch analysis completed',
                'analysis': batch_analysis
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return Response({
                'status': 'error',
                'message': f'Batch analysis failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def continuous_learning(self, request):
        """
        Update AI models with new events (continuous learning)
        POST /api/v1/ai-engine/continuous_learning/
        Body: {"hours": 24} - learn from events in last N hours
        """
        try:
            data = request.data
            hours = data.get('hours', 24)
            
            # Get recent events for learning
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_time = timezone.now() - timedelta(hours=hours)
            recent_events = SecurityEvent.objects.filter(
                timestamp__gte=cutoff_time
            ).values(
                'id', 'event_type', 'severity', 'description', 'timestamp',
                'is_resolved', 'source_device_ip', 'target_device_ip'
            )
            
            events_list = []
            for event in recent_events:
                event_dict = {
                    'id': event['id'],
                    'event_type': event['event_type'],
                    'severity': event['severity'],
                    'description': event['description'],
                    'timestamp': event['timestamp'].isoformat() if event['timestamp'] else None,
                    'is_resolved': event['is_resolved'],
                    'source_device_ip': event['source_device_ip'],
                    'target_device_ip': event['target_device_ip']
                }
                events_list.append(event_dict)
            
            # Perform continuous learning
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                learning_result = loop.run_until_complete(
                    self.ai_manager.continuous_learning_update(events_list)
                )
            finally:
                loop.close()
            
            return Response({
                'status': 'success',
                'message': 'Continuous learning completed',
                'result': learning_result,
                'events_processed': len(events_list)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Continuous learning failed: {e}")
            return Response({
                'status': 'error',
                'message': f'Continuous learning failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def system_status(self, request):
        """
        Get AI system status and performance metrics
        GET /api/v1/ai-engine/system_status/
        """
        try:
            status_info = self.ai_manager.get_ai_system_status()
            
            return Response({
                'status': 'success',
                'ai_system_status': status_info
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get AI system status: {e}")
            return Response({
                'status': 'error',
                'message': f'Failed to get AI system status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def configure_learning(self, request):
        """
        Configure AI learning parameters
        POST /api/v1/ai-engine/configure_learning/
        Body: {"auto_retrain_hours": 24, "min_new_events": 50, "learning_enabled": true}
        """
        try:
            config = request.data
            result = self.ai_manager.configure_learning_schedule(config)
            
            return Response({
                'status': 'success',
                'message': 'Learning configuration updated',
                'configuration': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to configure learning: {e}")
            return Response({
                'status': 'error',
                'message': f'Failed to configure learning: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def threat_predictions(self, request):
        """
        Get threat predictions for recent unresolved events
        GET /api/v1/ai-engine/threat_predictions/
        """
        try:
            # Get recent unresolved events
            unresolved_events = SecurityEvent.objects.filter(
                is_resolved=False
            ).order_by('-timestamp')[:50].values(
                'id', 'event_type', 'severity', 'description', 'timestamp',
                'is_resolved', 'source_device_ip', 'target_device_ip'
            )
            
            predictions = []
            
            for event in unresolved_events:
                event_dict = {
                    'id': event['id'],
                    'event_type': event['event_type'],
                    'severity': event['severity'],
                    'description': event['description'],
                    'timestamp': event['timestamp'].isoformat() if event['timestamp'] else None,
                    'is_resolved': event['is_resolved'],
                    'source_device_ip': event['source_device_ip'],
                    'target_device_ip': event['target_device_ip']
                }
                
                # Get AI prediction for this event
                try:
                    prediction = self.ai_manager.threat_detector.predict_threat(event_dict)
                    predictions.append({
                        'event_id': event['id'],
                        'prediction': prediction
                    })
                except Exception as e:
                    logger.warning(f"Failed to predict threat for event {event['id']}: {e}")
                    continue
            
            return Response({
                'status': 'success',
                'predictions': predictions,
                'total_events_analyzed': len(predictions)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get threat predictions: {e}")
            return Response({
                'status': 'error',
                'message': f'Failed to get threat predictions: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def anomaly_report(self, request):
        """
        Get anomaly detection report for recent events
        GET /api/v1/ai-engine/anomaly_report/
        """
        try:
            # Get recent events for anomaly analysis
            hours = int(request.query_params.get('hours', 24))
            
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_time = timezone.now() - timedelta(hours=hours)
            recent_events = SecurityEvent.objects.filter(
                timestamp__gte=cutoff_time
            ).values(
                'id', 'event_type', 'severity', 'description', 'timestamp',
                'is_resolved', 'source_device_ip', 'target_device_ip'
            )
            
            events_list = []
            for event in recent_events:
                event_dict = {
                    'id': event['id'],
                    'event_type': event['event_type'],
                    'severity': event['severity'],
                    'description': event['description'],
                    'timestamp': event['timestamp'].isoformat() if event['timestamp'] else None,
                    'is_resolved': event['is_resolved'],
                    'source_device_ip': event['source_device_ip'],
                    'target_device_ip': event['target_device_ip']
                }
                events_list.append(event_dict)
            
            # Detect anomalies
            anomaly_report = self.ai_manager.anomaly_detector.detect_anomalies(events_list)
            
            return Response({
                'status': 'success',
                'anomaly_report': anomaly_report,
                'analysis_period_hours': hours,
                'events_analyzed': len(events_list)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to generate anomaly report: {e}")
            return Response({
                'status': 'error',
                'message': f'Failed to generate anomaly report: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 