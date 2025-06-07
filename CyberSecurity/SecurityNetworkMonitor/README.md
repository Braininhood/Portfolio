# 🛡️ Security Network Monitor

A comprehensive, AI-powered cybersecurity monitoring platform built with Django and React. This professional-grade application provides real-time network monitoring, intelligent threat detection, and advanced security analytics for local network environments.

## ✨ Key Features

### 🤖 AI-Powered Security Engine
- **Machine Learning Threat Detection**: Advanced RandomForest-based threat classifier with 12+ feature extraction algorithms
- **Intelligent Spam Filtering**: Automated false positive detection and filtering with 100% effectiveness on repetitive alerts
- **Anomaly Detection**: Real-time behavioral analysis using Isolation Forest algorithms
- **Continuous Learning**: Self-improving AI models that adapt to new threat patterns
- **Smart Explanations**: Context-aware threat analysis with actionable recommendations

### 🌐 Real-Time Network Monitoring
- **Automatic Device Discovery**: Intelligent network scanning with device fingerprinting
- **Live Traffic Analysis**: Real-time bandwidth, packet rate, and connection monitoring
- **Port Scanning Engine**: Comprehensive port discovery with service detection
- **Network Topology Mapping**: Visual representation of network infrastructure
- **Device Status Tracking**: Uptime monitoring with historical status analysis

### 🔒 Advanced Security Features
- **Multi-Layer Threat Detection**: Device threats, port scans, unauthorized access detection
- **Security Event Management**: Comprehensive event logging with severity classification
- **Real-Time Alerting**: Instant notifications for critical security events
- **Incident Response**: Built-in event resolution and tracking system
- **Security Scoring**: Dynamic security assessment for network devices

### 📊 Professional Dashboard
- **Real-Time Metrics**: Live updating dashboard with WebSocket connectivity
- **Interactive Charts**: Advanced data visualization using Recharts and Chart.js
- **Device Management**: Comprehensive device inventory with detailed information
- **Security Timeline**: Chronological view of security events and incidents
- **Network Analytics**: Traffic patterns, device distribution, and performance metrics

### 🔧 Technical Excellence
- **WebSocket Integration**: Real-time bidirectional communication
- **RESTful API**: Comprehensive API with 15+ endpoints
- **Responsive Design**: Material-UI based interface optimized for all devices
- **Background Processing**: Celery-based async task management
- **Production Ready**: Gunicorn, Whitenoise, and Redis integration

## 🏗️ Architecture

### Backend Stack
- **Framework**: Django 4.2.7 with Django REST Framework 3.14.0
- **AI/ML**: scikit-learn, NumPy, Pandas for machine learning capabilities
- **Real-time**: Django Channels 4.0.0 with Redis for WebSocket support
- **Network Tools**: python-nmap, scapy, psutil, netifaces for network operations
- **Database**: SQLite (production-ready for PostgreSQL/MySQL)
- **Background Tasks**: Celery 5.3.4 with Redis broker

### Frontend Stack
- **Framework**: React 18.2.0 with modern hooks and functional components
- **UI Library**: Material-UI 5.14.20 with custom dark theme
- **State Management**: TanStack React Query 5.8.4 for server state
- **Routing**: React Router 6.19.0 for SPA navigation
- **Charts**: Recharts 2.8.0 and Chart.js 4.4.9 for data visualization
- **HTTP Client**: Axios 1.6.2 for API communication

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (tested with Python 3.13)
- **Node.js 16+** (for development)
- **Git**

### Installation

1. **Clone the Repository**
```bash
git clone <repository-url>
cd SecurityNetworkMonitor
```

2. **Backend Setup**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

3. **Frontend Setup** (Development)
```bash
# Install Node.js dependencies
npm install

# Start React development server
npm start
```

4. **Start the Application**
```bash
# Start Django server (serves both API and built React app)
python manage.py runserver 8000

# For WebSocket support (optional)
python manage.py runserver_ws 8000
```

5. **Access the Application**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/
- **Django Admin**: http://localhost:8000/admin/

## 📱 Application Features

### Dashboard
- **Live Metrics Cards**: Device count, security events, network status
- **Real-Time Charts**: Network traffic, device distribution, security trends
- **Quick Actions**: Network discovery, security reports, device management
- **Status Indicators**: System health, AI engine status, monitoring state

### Device Management
- **Device Discovery**: Automatic network scanning and device detection
- **Device Profiles**: Detailed information including OS, services, ports
- **Status Monitoring**: Real-time uptime, response time, packet loss tracking
- **Port Scanning**: On-demand comprehensive port analysis
- **Device History**: Historical status and performance data

### Security Center
- **Event Timeline**: Chronological security event display with filtering
- **Threat Analysis**: AI-powered threat classification and scoring
- **Incident Management**: Event resolution and tracking system
- **Security Reports**: Comprehensive security analytics and trends
- **Alert Configuration**: Customizable alerting rules and thresholds

### AI Engine
- **Threat Predictions**: Machine learning-based threat assessment
- **Anomaly Detection**: Behavioral analysis and outlier identification
- **Smart Filtering**: Automated false positive reduction
- **Learning Dashboard**: AI model performance and training metrics
- **Recommendation Engine**: Actionable security recommendations

### Network Monitoring
- **Real-Time Traffic**: Live bandwidth and packet monitoring
- **Network Topology**: Visual network mapping and device relationships
- **Performance Metrics**: Latency, throughput, and connection analysis
- **Historical Data**: Long-term network performance trends
- **Traffic Analysis**: Protocol analysis and connection patterns

## 🔌 API Endpoints

### Core Endpoints
```
GET  /api/v1/dashboard/stats/           # Dashboard statistics
GET  /api/v1/devices/                   # Network devices list
POST /api/v1/devices/{id}/scan/         # Scan specific device
GET  /api/v1/security-events/           # Security events
GET  /api/v1/scans/                     # Network scans history
POST /api/v1/scans/quick_discovery/     # Start network discovery
```

### AI Engine Endpoints
```
GET  /api/v1/ai-engine/system_status/   # AI system status
GET  /api/v1/ai-engine/threat_predictions/ # Threat analysis
GET  /api/v1/ai-engine/anomaly_report/  # Anomaly detection
POST /api/v1/ai-engine/train/           # Train AI models
```

### Monitoring Endpoints
```
GET  /api/v1/monitoring/status/         # Monitoring status
POST /api/v1/monitoring/start/          # Start monitoring
POST /api/v1/monitoring/stop/           # Stop monitoring
GET  /api/v1/traffic/real-time-metrics/ # Live traffic data
```

### WebSocket Endpoints
```
ws://localhost:8000/ws/network/         # Real-time network updates
ws://localhost:8000/ws/scan-progress/   # Scan progress updates
ws://localhost:8000/ws/device-detail/{id}/ # Device-specific updates
```

## 🛡️ Security Features

### Threat Detection
- **Device Threat Detection**: Behavioral analysis and anomaly identification
- **Port Scan Detection**: Automated detection of scanning activities
- **Unauthorized Access**: Failed authentication and intrusion attempts
- **Traffic Anomalies**: Unusual bandwidth or connection patterns
- **Malware Indicators**: Suspicious network behavior patterns

### AI-Powered Analysis
- **12+ Feature Extraction**: Temporal, network, behavioral, and pattern features
- **Ensemble Learning**: RandomForest classifier with 100 estimators
- **Confidence Scoring**: Probabilistic threat assessment (0-100%)
- **False Positive Filtering**: Multi-layer spam detection and filtering
- **Continuous Learning**: Model retraining with new threat data

### Security Event Management
- **Event Classification**: Critical, High, Medium, Low severity levels
- **Real-Time Alerting**: Instant notifications for security incidents
- **Event Resolution**: Built-in incident response workflow
- **Audit Trail**: Comprehensive logging and event history
- **Reporting**: Security analytics and trend analysis

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration (for WebSocket and Celery)
REDIS_URL=redis://localhost:6379/0

# AI Engine Settings
AI_MODELS_DIR=models
AI_LEARNING_ENABLED=True
AI_RETRAIN_HOURS=24

# Network Monitoring
DEFAULT_SCAN_RANGE=192.168.1.0/24
MONITORING_INTERVAL=30
MAX_CONCURRENT_SCANS=5
```

### Network Configuration
- **Auto-Discovery**: Automatically detects network interfaces and ranges
- **Custom Ranges**: Configurable IP ranges for scanning
- **Port Configuration**: Customizable port ranges and scan techniques
- **Timing Templates**: Adjustable scan timing (paranoid to insane)
- **Exclusion Lists**: Hosts and networks to exclude from scanning

## 📊 Monitoring & Analytics

### Real-Time Metrics
- **Device Status**: Online/offline status with uptime percentages
- **Network Traffic**: Bandwidth utilization and packet rates
- **Security Events**: Real-time threat detection and alerting
- **System Performance**: CPU, memory, and network utilization
- **AI Engine**: Model performance and prediction accuracy

### Historical Analytics
- **Device History**: Long-term device status and performance trends
- **Security Trends**: Historical security event analysis
- **Network Performance**: Bandwidth and latency trends over time
- **Threat Intelligence**: AI model learning and improvement metrics
- **Incident Reports**: Comprehensive security incident documentation

## 🚀 Production Deployment

### Build for Production
```bash
# Build React frontend
npm run build

# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn network_monitor.wsgi:application --bind 0.0.0.0:8000
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "network_monitor.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Environment Setup
- **Database**: Configure PostgreSQL or MySQL for production
- **Redis**: Set up Redis for WebSocket and Celery support
- **Reverse Proxy**: Use Nginx for static file serving and SSL termination
- **SSL/TLS**: Configure HTTPS for secure communication
- **Monitoring**: Set up logging and monitoring for production use

## 🧪 Development

### Development Server
```bash
# Backend development
python manage.py runserver 8000

# Frontend development (with hot reload)
npm start

# WebSocket development
python manage.py runserver_ws 8000
```

### Code Structure
```
SecurityNetworkMonitor/
├── apps/
│   ├── ai_engine/              # AI/ML threat detection
│   │   ├── threat_detector.py  # Machine learning models
│   │   ├── anomaly_detector.py # Anomaly detection
│   │   ├── ai_manager.py       # AI system coordinator
│   │   └── views.py            # AI API endpoints
│   ├── api/                    # REST API
│   │   ├── views.py            # API viewsets
│   │   ├── serializers.py      # Data serialization
│   │   └── urls.py             # API routing
│   ├── network_monitor/        # Core monitoring
│   │   ├── models.py           # Database models
│   │   ├── services/           # Network services
│   │   └── monitoring_services/ # Real-time monitoring
│   └── websocket/              # WebSocket handlers
├── src/                        # React frontend
│   ├── components/             # React components
│   ├── pages/                  # Page components
│   ├── contexts/               # React contexts
│   └── services/               # API services
├── models/                     # AI model storage
├── static/                     # Static files
└── templates/                  # Django templates
```

## 📚 Help & Documentation

### Getting Started
1. **Initial Setup**: Follow the installation guide above
2. **Network Discovery**: Use the "Start Discovery" button on the dashboard
3. **Device Management**: View and manage devices in the Devices section
4. **Security Monitoring**: Monitor events in the Security Center
5. **AI Configuration**: Train AI models in the AI Engine section

### Troubleshooting
- **Network Permissions**: Ensure the application has network scanning permissions
- **Port Access**: Verify that required ports (8000, 6379) are available
- **Dependencies**: Check that all Python and Node.js dependencies are installed
- **Database**: Ensure database migrations have been run successfully
- **WebSocket**: Verify Redis is running for real-time features

### Support
- **Documentation**: Comprehensive help available in the application's Help section
- **API Reference**: Interactive API documentation at `/api/v1/`
- **Admin Interface**: Django admin panel for advanced configuration
- **Logs**: Check application logs for detailed error information

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Security Network Monitor** - Professional cybersecurity monitoring made simple and intelligent. 