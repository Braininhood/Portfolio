# Data Visualization Web App

A Django web application for uploading, cleaning, and visualizing data from various file formats with enhanced security and database integration.

## Distinctiveness and Complexity

This Data Visualization Web App stands distinctly apart from other CS50W projects for several key reasons:

1. **Purpose and Functionality**: Unlike the e-commerce platform (Project 2), social network (Project 4), or other course projects, this application focuses on data analysis and visualization—a fundamentally different domain. While other projects primarily dealt with content creation and sharing, this application transforms raw data into meaningful insights through visualizations and data processing techniques.

2. **Technical Implementation**: 
   - **Advanced Data Processing Pipeline**: The application implements a sophisticated data cleaning system that allows users to detect outliers, normalize data, handle missing values, and transform data types—capabilities far beyond the simple CRUD operations in previous projects.
   - **Integration with External Database Systems**: Unlike previous projects that used a single database, this app connects to multiple external database systems (MySQL, PostgreSQL, SQL Server) and integrates with the Supabase API, requiring complex connection handling and credential management.
   - **Enhanced Security Layer**: The implementation of encryption for sensitive user data and database credentials represents a significant complexity increase, utilizing the cryptography library for key derivation and secure encryption.

3. **Frontend Complexity**:
   - **Interactive Data Visualization**: The application uses JavaScript to create dynamic, interactive visualizations based on user inputs, with real-time previews before committing changes.
   - **Advanced Chart Creation**: Users can create complex visualizations (heatmaps, bubble charts, etc.) with customization options for color palettes, groupings, and visual elements.
   - **Responsive Data Tables and Forms**: The frontend adapts to different data types and formats, providing appropriate interfaces for each visualization type and data cleaning operation.

4. **Architectural Complexity**:
   - **Modular Design**: The application is built with a modular architecture separating data handling, visualization, and security concerns.
   - **Signal-Based Data Processing**: Django signals are used for automatic data encryption and secure file deletion.
   - **Comprehensive Error Handling**: Robust error handling throughout the application deals with various data formats, connection issues, and processing errors.

5. **Technical Challenges Overcome**:
   - **Multi-format Data Handling**: The application processes diverse file formats (CSV, Excel, SQLite) and database types, each requiring specific handling methods.
   - **Security Implementation**: Database credentials are safely encrypted, and user data is protected through encryption mechanisms.
   - **Performance Optimization**: Data processing operations are optimized to handle large datasets efficiently.
   - **GDPR Compliance**: Implementation of data consent management and retention policies adds complexity in terms of data lifecycle management.

The application demonstrates significant complexity through the integration of multiple technologies (Django, SQLAlchemy, Pandas, Matplotlib, Seaborn, Cryptography) working together to provide a cohesive and powerful data visualization platform. It requires understanding of data science concepts, security principles, and database management beyond what was covered in the course.

## File Structure and Contents

### Backend (Django)

- **project/settings.py**: Contains configuration for the Django project, including database settings, installed apps, and middleware.
- **project/urls.py**: Defines the main URL patterns and includes app-specific URLs.
- **data_project/models.py**: Defines the database models:
  - `EncryptionManager`: Handles encryption/decryption with key derivation
  - `EncryptedUserProfile`: Stores encrypted user information
  - `UserDataFile`: Manages user-uploaded data files and database connections
  - `Visualization`: Stores visualization metadata and images
  - `SlideImage`: Manages slideshow images for the home page
- **data_project/views.py**: Contains all view functions for handling requests, including:
  - User authentication (signup, login, logout)
  - File and database operations (upload, connect, read)
  - Data cleaning functions
  - Visualization creation and rendering
  - GDPR consent management
- **data_project/forms.py**: Defines forms for user input:
  - `SignUpForm`: User registration
  - `LoginForm`: User login
  - `DataFileUploadForm`: File upload
  - `DatabaseConnectionForm`: Database connection details
  - `EncryptionMixin`: Mixin for handling form data encryption
- **data_project/urls.py**: Defines app-specific URL patterns
- **data_project/admin.py**: Configures the Django admin interface for models

### Frontend (Templates & Static Files)

- **data_project/templates/data_project/**: Contains HTML templates
  - `base.html`: Base template with navigation and common elements
  - `dashboard.html`: User dashboard showing uploaded files and visualizations
  - `file_detail.html`: Displays file details and data preview
  - `clean_data.html`: Interface for data cleaning operations
  - `create_visualization.html`: Basic visualization creation interface
  - `advanced_visualization.html`: Advanced visualization options
  - Other templates for authentication, settings, and more
- **data_project/static/**: Contains static assets
  - CSS files for styling
  - JavaScript files for interactive elements and visualization previews
  - Images and icons

## Features

- **Welcome Page**: Attractive slideshow with login and registration buttons
- **User Authentication**: Secure login and registration system
- **Data Encryption**: Secure encryption for sensitive user data and database credentials
- **Database Connectivity**: Connect to various database systems:
  - SQLite, MySQL, PostgreSQL, SQL Server
  - Supabase API integration
- **File Upload**: Support for CSV, Excel, and SQLite database files
- **Data Cleaning**: 
  - Handle missing values, duplicates, and outliers
  - Convert data types, normalize, and standardize data
  - Text processing tools for string columns
- **Advanced Data Visualization**: 
  - Basic charts: bar, line, scatter, pie, histogram
  - Advanced visualizations: heatmaps, bubble charts, area plots
  - Customization options with various color palettes
- **Responsive Design**: Works on desktop and mobile devices
- **GDPR Compliance**: User consent management and data retention policies

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd data_viz_project
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Apply migrations:
```
python manage.py migrate
```

4. Create a superuser (optional):
```
python manage.py createsuperuser
```

5. Set environment variables for encryption (optional but recommended):
```
export ENCRYPTION_KEY="your-secure-key"
export ENCRYPTION_SALT="your-secure-salt"
```

6. Run the development server:
```
python manage.py runserver
```

7. Visit http://127.0.0.1:8000/ in your browser

## Usage

### 1. User Registration and Login
- Create a new account or login with existing credentials
- Admin users can also upload slideshow images through the admin panel

### 2. Uploading and Connecting to Data
- **File Upload**: Click "Upload Data" in the navigation menu
  - Provide a title for your data file
  - Select and upload a CSV, Excel, or SQLite database file
- **Database Connection**: Click "Connect Database" 
  - Choose your database type (MySQL, PostgreSQL, SQL Server)
  - Enter connection details securely (credentials are encrypted)
- **Supabase Integration**: Connect to Supabase via direct PostgreSQL or REST API

### 3. Viewing Data
- Your uploaded files and database connections appear in your dashboard
- Click on a file/connection to view details, including a data preview
- For database connections, you can browse available tables

### 4. Cleaning Data
- From the file detail page, click "Clean Data"
- **Basic Cleaning**:
  - Handle missing values (drop, fill, interpolate)
  - Remove duplicates
  - Trim whitespace in text columns
- **Advanced Cleaning**:
  - Outlier detection and handling (IQR, Z-score)
  - Data transformations (normalize, standardize, log transform)
  - Text processing (case conversion, pattern replacement)
  - Type conversion (to numeric, datetime, category)

### 5. Creating Visualizations
- From the file detail page, click "Create Visualization"
- **Basic Visualization**:
  - Choose a visualization type (bar, line, scatter, pie, histogram)
  - Select columns for X and Y axes
- **Advanced Visualization**:
  - Create more complex visualizations (heatmaps, bubble charts)
  - Customize with color palettes and grouping options
  - Add visual elements for better data representation

### 6. Data Privacy and Security
- User data and credentials are encrypted using industry-standard methods
- GDPR compliance tools for consent management
- Option to export or delete your data

## Additional Implementation Details

### Mobile Responsiveness
The application is fully responsive across devices of different screen sizes:
- Responsive navigation with collapsible menu on smaller screens
- Fluid grid layouts for dashboard and visualization displays
- Touch-friendly controls for mobile users
- Optimized data tables that adapt to screen width

### JavaScript Functionality
The frontend uses JavaScript for several key features:
- Dynamic visualization previews before saving
- Interactive data cleaning interface with realtime feedback
- AJAX for asynchronous data loading and form submissions
- Form validation and error handling

### Database Schema
The database model relationships are designed to support the application's functionality:
- `User` (Django's built-in user model) has one `EncryptedUserProfile` for secure data
- `User` has many `UserDataFile` records for uploaded files and database connections
- Each `UserDataFile` can have multiple `Visualization` records
- GDPR consent tracking is built into the `UserDataFile` model

## Technology Stack

- **Backend**: Django
- **Frontend**: Bootstrap 5, Font Awesome
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Security**: Cryptography, PyCryptodome
- **Database Connectivity**: SQLAlchemy, PyMySQL, psycopg2
- **API Integration**: Requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django
- Bootstrap
- Pandas
- Matplotlib 