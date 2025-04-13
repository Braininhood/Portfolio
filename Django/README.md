# Django Projects

This directory contains a collection of web applications built with Django, each demonstrating different features and functionality of the Django framework.

## Project Overview

### Wiki

A Wikipedia-like online encyclopedia that allows users to create, edit, and browse informational articles.

**Key Features:**
* Create and edit encyclopedia entries with Markdown support
* Search functionality with suggestions based on query
* Random page navigation
* Responsive design for all devices

**Project Structure:**
* `/wiki/` - Main project directory
* `/wiki/encyclopedia/` - Main app with views, models, and templates
* `/wiki/entries/` - Directory containing Markdown files for encyclopedia articles

**Technologies Used:**
* Django
* Markdown2 (for converting Markdown to HTML)
* Bootstrap for responsive design 

### Mail

A single-page email client application that allows users to send, receive, and archive emails. Built with Django for the backend and JavaScript for the frontend.

**Key Features:**
* User authentication system
* Compose and send emails to other users
* Inbox, Sent, Archive, and Drafts mailboxes
* Mark emails as read/unread
* Archive/unarchive functionality
* Responsive UI

**Project Structure:**
* `/mail/` - Main project directory
* `/mail/mail/` - Main app with models, views, and API endpoints
* `/mail/mail/static/` - Frontend JavaScript and CSS
* `/mail/mail/templates/` - HTML templates

**Technologies Used:**
* Django
* JavaScript (vanilla JS for frontend functionality)
* REST API architecture
* Bootstrap for styling

### Commerce

An eBay-like e-commerce auction site that allows users to post auction listings, place bids, comment, and add items to a "watchlist."

**Key Features:**
* User authentication and registration
* Create, view, and bid on auction listings
* Add listings to watchlist
* Categories for organizing listings
* Comments on auction listings
* Image upload for listings

**Project Structure:**
* `/commerce/` - Main project directory
* `/commerce/auctions/` - Main app with models, views, and templates
* `/commerce/auctions/templates/` - HTML templates
* `/commerce/auctions/static/` - CSS and static files

**Technologies Used:**
* Django
* Django Forms for data validation
* File upload handling
* Django Pagination
* Bootstrap for responsive design

### Network

A Twitter-like social network web application that allows users to create posts, follow other users, and interact with content.

**Key Features:**
* User profile creation and management
* Create and edit posts
* Follow/unfollow other users
* Custom feed based on followed users
* Like/unlike posts
* Pagination for post listings

**Project Structure:**
* `/network/` - Main project directory
* `/network/network/` - Main app with models, views, and templates
* `/network/network/static/` - JavaScript and CSS files
* `/network/network/templates/` - HTML templates

**Technologies Used:**
* Django
* JavaScript for asynchronous interactions
* AJAX for frontend-backend communication
* Django REST framework for API endpoints
* Bootstrap for responsive design

### Data Visualization

A web application for uploading, cleaning, and visualizing data from various file formats with enhanced security and database integration.

**Key Features:**
* User authentication with encrypted profiles
* Support for multiple data formats (CSV, Excel, SQLite)
* Connect to external databases (MySQL, PostgreSQL, SQL Server)
* Advanced data cleaning and processing tools
* Interactive data visualization with customization options
* GDPR compliance and data security features
* Mobile-responsive design

**Project Structure:**
* `/data_viz_project/` - Main project directory
* `/data_viz_project/data_project/` - Main app with models, views, and templates
* `/data_viz_project/data_project/static/` - CSS, JavaScript, and visualization assets
* `/data_viz_project/data_project/templates/` - HTML templates
* `/data_viz_project/media/` - User uploaded files and generated visualizations

**Technologies Used:**
* Django for backend
* Pandas and NumPy for data processing
* Matplotlib and Seaborn for visualization
* SQLAlchemy for database connectivity
* Cryptography for data encryption
* Bootstrap for responsive design
* JavaScript for interactive features

## Getting Started

Each project can be run independently. To start any of the projects:

1. Navigate to the project directory:
   ```
   cd Django/[project_name]
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Apply migrations:
   ```
   python manage.py migrate
   ```

4. Run the development server:
   ```
   python manage.py runserver
   ```

5. Open your browser and go to `http://127.0.0.1:8000/`

## Features Demonstrated

These projects collectively demonstrate a wide range of Django features:

* **Models & Database Management**: Creating models, relationships, and queries
* **Authentication**: User registration, login, and permission management
* **Forms**: Django forms for validation and processing
* **Templates**: Template inheritance and rendering
* **Static Files**: Management of CSS, JavaScript, and media files
* **Admin Interface**: Django's built-in admin functionality
* **API Development**: Building API endpoints with Django views
* **File Handling**: Uploading and managing files and images
* **Pagination**: Handling large sets of data with Django's pagination
* **Single-Page Applications**: Building SPAs with Django backend
* **Data Processing**: Working with external data processing libraries like Pandas
* **Data Visualization**: Creating dynamic visualizations with Matplotlib and Seaborn
* **Database Connectivity**: Connecting to various external database systems
* **Security Implementation**: Encryption and secure credential management
* **GDPR Compliance**: User consent management and data protection

## Project Dependencies

All projects use Django as the core framework, with additional libraries as needed for specific functionality. Common dependencies include:

* Django
* Markdown2 (for Wiki)
* Pillow (for Commerce image handling)
* Bootstrap (for frontend styling)
* Pandas and NumPy (for Data Visualization)
* Matplotlib and Seaborn (for Data Visualization)
* SQLAlchemy and database connectors (for Data Visualization)
* Cryptography and PyCryptodome (for Data Visualization security) 