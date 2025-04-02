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

## Project Dependencies

All projects use Django as the core framework, with additional libraries as needed for specific functionality. Common dependencies include:

* Django
* Markdown2 (for Wiki)
* Pillow (for Commerce image handling)
* Bootstrap (for frontend styling) 