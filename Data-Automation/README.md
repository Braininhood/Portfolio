# Data Automation Web Application

A comprehensive web application for Excel data processing, cohort management, and email automation, built with Django REST API and React frontend. This application transforms the original CLI tool into a user-friendly web interface.

## Features

### 🚀 Core Functionality
- **Dual File Upload**: Upload Excel files directly or import from Microsoft Forms
- **Excel File Processing**: Upload and process Excel files with participant data
- **Microsoft Forms Integration**: Import data directly from Microsoft Forms using response URLs
- **Data Analysis**: Comprehensive analysis with statistics and validation
- **Cohort Management**: Automatic creation of participant cohorts based on characteristics
- **Email System**: Send personalized emails to cohort participants
- **BPA (Business Process Automation)**: Automated duplicate resolution and cohort balancing
- **Reporting**: Generate detailed reports for analysis and monitoring
- **Real-time Dashboard**: Live statistics and system monitoring

### 📊 Data Processing
- Smart data cleaning and validation
- Email format validation
- Date validation and normalization
- Duplicate detection and resolution
- Automatic cohort assignment (11 different cohort types)
- Support for both Excel files (.xlsx, .xls) and Microsoft Forms data
- Real-time processing status updates

### 👥 Cohort Types
- **Main Cohorts**: Primary vs Alternative (attendance-based)
- **Technical Cohorts**: Software setup requirements
- **Support Cohorts**: High support vs Standard support
- **Communication Cohorts**: Email validation status
- **Readiness Cohorts**: Course readiness assessment

### 📧 Email Features
- Gmail integration with app password authentication
- Customizable email templates with automatic generation
- Template preview functionality
- Delivery tracking and reporting
- Cohort-based email targeting
- **HTML Email with Embedded Charts**: Rich email format with Base64 embedded chart images
- **Chart Selection**: Choose which charts to include in emails
- **Professional Email Layout**: Clean, responsive design with proper styling
- **Chart Attachments**: Chart images attached as separate PNG files

## Technology Stack

### Backend
- **Django 4.2+**: Web framework
- **Django REST Framework**: API development
- **PostgreSQL/SQLite**: Database
- **Celery**: Background task processing
- **Redis**: Caching and message broker
- **Pandas**: Data processing
- **OpenPyXL**: Excel file handling
- **Matplotlib & Seaborn**: Chart generation
- **Base64**: Image encoding for email embedding

### Frontend
- **React 18**: UI framework
- **React Router**: Navigation
- **React Query**: Data fetching and caching
- **Tailwind CSS**: Styling
- **Axios**: HTTP client
- **React Dropzone**: File upload handling
- **Lucide React**: Modern icon library
- **React Toastify**: Notifications
- **Recharts**: Interactive chart components

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis (for background tasks)
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Data-Automation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

### Redis Setup (Optional)

For background task processing:

1. **Install Redis**
   - Windows: Download from https://redis.io/download
   - macOS: `brew install redis`
   - Linux: `sudo apt-get install redis-server`

2. **Start Redis**
   ```bash
   redis-server
   ```

## Usage

### 1. File Upload

#### Excel File Upload
- Navigate to the File Upload page
- Select "Upload Excel File" method
- Drag and drop Excel files or click to select (.xlsx, .xls)
- Files are automatically processed and validated
- View processing status and participant count in real-time

#### Microsoft Forms Import
- Select "Import from Microsoft Forms" method
- Enter your Microsoft Forms response URL (e.g., `https://forms.office.com/...`)
- The system validates the URL format automatically
- Click "Import from Forms" to fetch and process the data
- No file size limitations - import unlimited responses

**How to get Microsoft Forms URL:**
1. Open your Microsoft Forms
2. Click on "Responses" tab
3. Click "Open in Excel" or "Export to Excel"
4. Copy the URL from the browser address bar
5. Paste it in the application

### 2. Dashboard
- View real-time statistics and system overview
- Monitor file uploads, participants, and cohorts
- Quick access to all major features
- System status monitoring

### 3. Data Analysis
- Select processed files for analysis
- View comprehensive statistics and insights
- Identify data quality issues and email validation problems
- Generate detailed analysis reports

### 4. Cohort Management
- Create cohorts from processed files automatically
- View cohort details and participant counts
- Manage 11 different cohort types
- Send targeted emails to specific cohorts

### 5. Email System
- Configure Gmail credentials with app password
- Select email templates and target cohorts
- Preview emails before sending
- Test email connection and track delivery status

### 6. BPA Demo
- View Business Process Automation in action
- See how duplicate registrations are handled
- Understand cohort balancing logic
- Learn about automated decision making

### 7. Reports
- Generate various types of reports with chart data
- **Interactive Chart Preview**: View charts before sending emails
- **Chart Selection**: Choose which charts to include in reports
- **HTML Email Reports**: Send reports with embedded chart images
- **Professional Chart Titles**: Clear, descriptive chart names
- Download reports in multiple formats
- Track report generation status
- View historical reports
- **Delete Reports**: Remove unwanted reports from the system

## API Endpoints

### Files
- `GET /api/files/` - List all files
- `POST /api/upload/` - Upload Excel file
- `POST /api/upload/forms/` - Import from Microsoft Forms
- `GET /api/files/{id}/` - Get file details
- `DELETE /api/files/{id}/` - Delete file

### Data Processing
- `POST /api/process/` - Process multiple files
- `POST /api/analyze/` - Analyze file data
- `POST /api/cohorts/create/` - Create cohorts from files

### Cohorts
- `GET /api/cohorts/` - List all cohorts
- `GET /api/cohorts/{id}/` - Get cohort details
- `GET /api/cohorts/{id}/participants/` - Get cohort participants

### Email
- `GET /api/email/templates/` - List email templates
- `POST /api/email/send/` - Send emails to cohort
- `POST /api/email/preview/` - Preview email template
- `POST /api/email/test-connection/` - Test email connection

### BPA (Business Process Automation)
- `POST /api/bpa/process/` - Process cohorts with BPA
- `GET /api/bpa/demo/` - Run BPA demonstration

### Reports
- `GET /api/reports/list/` - List all reports
- `POST /api/reports/generate/` - Generate new report
- `POST /api/reports/generate-enhanced/` - Generate enhanced report with charts
- `GET /api/reports/download/{id}/` - Download report file
- `POST /api/reports/send-email/` - Send report via email with charts
- `DELETE /api/reports/delete/{id}/` - Delete report

### Dashboard
- `GET /api/dashboard/stats/` - Get dashboard statistics

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Settings
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery Settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Frontend Settings
REACT_APP_API_URL=http://localhost:8000/api
```

### Gmail Setup

1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification
   - App passwords → Generate new password
3. Use the app password (not your regular password) in the email configuration

## Development

### Backend Development
```bash
# Run tests
python manage.py test

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver
```

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Deployment

### Backend Deployment
1. Set `DEBUG=False` in production
2. Configure production database
3. Set up static file serving
4. Configure email settings
5. Set up Redis for background tasks

### Frontend Deployment
1. Build the React app: `npm run build`
2. Serve static files through Django or a CDN
3. Configure API URL for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository or contact the development team.

## Current Status

### ✅ Fully Functional Features
- **Dual File Upload**: Both Excel and Microsoft Forms import working
- **Real-time Dashboard**: Live statistics and system monitoring
- **File Management**: Upload, view, and delete files
- **Data Processing**: Automatic processing and validation
- **Cohort Management**: Create and manage participant cohorts
- **Email System**: Configure and send emails to cohorts
- **BPA Demo**: Business Process Automation demonstration
- **Reports**: Generate and download various reports
- **API Integration**: All REST endpoints working correctly

### 🔧 Technical Status
- **Backend**: Django server running on http://localhost:8000
- **Frontend**: React app running on http://localhost:3000
- **Database**: SQLite with all migrations applied
- **API**: All endpoints returning 200 OK responses
- **Authentication**: AllowAny for development (no login required)

## Quick Start

### Automated Setup
1. **Run the setup script**:
   ```bash
   python setup.py
   ```
   This will automatically:
   - Install all dependencies
   - Set up the database
   - Create sample data
   - Start both backend and frontend servers

2. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Manual Setup
Follow the detailed installation steps in the Installation section above.

## Changelog

### Version 1.1.0 (Latest)
- **HTML Email with Embedded Charts**: Rich email format with Base64 embedded chart images
- **Interactive Chart Preview**: View charts before sending emails
- **Chart Selection Interface**: Choose which charts to include in reports and emails
- **Professional Chart Titles**: Clear, descriptive chart names instead of technical keys
- **Enhanced Report Content**: Full report content included in email body
- **Chart Attachments**: Chart images attached as separate PNG files
- **Delete Report Functionality**: Remove unwanted reports from the system
- **Improved Email Layout**: Professional, responsive design with proper styling
- **Chart Generation**: Matplotlib and Seaborn integration for chart creation

### Version 1.0.0
- Initial release
- Dual file upload (Excel + Microsoft Forms)
- Real-time dashboard with statistics
- Excel file processing and validation
- Microsoft Forms integration
- Cohort management (11 cohort types)
- Email system with Gmail integration
- BPA automation and demo
- Comprehensive reporting system
- Modern React UI with Tailwind CSS
- RESTful API with Django REST Framework
