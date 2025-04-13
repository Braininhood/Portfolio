# Social Network Platform

A feature-rich social media platform built with Python Django and JavaScript, offering real-time interactions and a modern user interface.

## Features

### User Management
- User registration and authentication
- Customizable user profiles with avatars and bio
- Follow/unfollow functionality

### Posts
- Create, edit, and delete posts
- Support for text content and image uploads
- Like/unlike posts
- Emoji reactions to posts

### Comments
- Multi-level nested comments (unlimited depth)
- Edit and delete comments
- Emoji reactions to comments
- Reply to any comment at any level in the comment tree

### UI/UX
- Mobile-responsive design
- Real-time updates
- Emoji picker for posts and comments
- Infinite scrolling for posts
- Customizable interface

## Technology Stack

- **Backend**: Django (Python)
- **Frontend**: JavaScript, Bootstrap, React components
- **Database**: SQLite (default), supports PostgreSQL for production
- **Media Storage**: Local storage with option for AWS S3 integration

## Installation

### Prerequisites
- Python 3.8+
- Node.js and npm (for frontend asset compilation)
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/network.git
   cd network
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser (admin):
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Visit `http://localhost:8000` in your browser

### Frontend Development

For modifying the JavaScript components:

1. Install npm dependencies:
   ```bash
   cd network/static/network
   npm install
   ```

2. Build the frontend assets:
   ```bash
   # Development mode with auto-rebuild
   npm run dev
   
   # Production build
   npm run build
   ```

## Usage

### Basic Navigation

- **Home Feed**: View all posts from all users
- **Following Feed**: View posts from users you follow
- **User Profiles**: View a user's posts and follow/unfollow them
- **Create Post**: Click the "New Post" button to create a post
- **Interact**: Like, react, or comment on posts

### Comments and Replies

The platform supports unlimited nested comments:

1. Click "Comment" on any post to add a top-level comment
2. Click "Reply" on any comment to add a nested reply
3. Edit or delete your own comments using the provided buttons
4. React to comments with emojis

## Security Features

The application includes several security measures:

- CSRF protection
- XSS prevention through content sanitization
- SQL injection protection
- Secure password handling
- Input validation

## API Documentation

The application provides a RESTful API for accessing and manipulating data programmatically.

### Authentication

Most API endpoints require authentication. Include your CSRF token in request headers:

```
X-CSRFToken: <csrf_token>
```

### API Endpoints

#### Posts

|              Endpoint           | Method |          Description          |                       Parameters                          |
|---------------------------------|--------|-------------------------------|-----------------------------------------------------------|
| `/api/posts`                    | GET    | Get all posts                 | `page`: Page number (optional)                            |
| `/api/posts/create`             | POST   | Create a new post             | `content`: Post content<br>`image`: Image file (optional) |
| `/api/posts/<post_id>`          | GET    | Get a specific post           | None                                                      |
| `/api/posts/<post_id>/edit`     | PUT    | Edit a post                   | `content`: New post content                               |
| `/api/posts/<post_id>/delete`   | DELETE | Delete a post                 | None                                                      |
| `/api/posts/<post_id>/like`     | POST   | Toggle like on a post         | None                                                      |
| `/api/posts/<post_id>/reaction` | POST   | Add/remove emoji reaction     | `emoji`: Emoji character                                  |
| `/api/posts/following`          | GET    | Get posts from followed users | `page`: Page number (optional)                            |

#### Comments

|                 Endpoint               | Method |         Description       |                                Parameters                               |
|----------------------------------------|--------|---------------------------|-------------------------------------------------------------------------|
| `/api/posts/<post_id>/comments`        | GET    | Get comments for a post   | None                                                                    |
| `/api/posts/<post_id>/comments/create` | POST   | Create a comment          | `content`: Comment content<br>`parent_id`: Parent comment ID (optional) |
| `/api/comments/<comment_id>/edit`      | PUT    | Edit a comment            | `content`: New comment content                                          |
| `/api/comments/<comment_id>/delete`    | DELETE | Delete a comment          | None                                                                    |
| `/api/comments/<comment_id>/reaction`  | POST   | Add/remove emoji reaction | `emoji`: Emoji character                                                |

#### Users

|             Endpoint           | Method |          Description         |                           Parameters                             |
|--------------------------------|--------|------------------------------|------------------------------------------------------------------|
| `/api/users/<username>`        | GET    | Get user profile data        | None                                                             |
| `/api/users/<username>/follow` | POST   | Toggle follow for a user     | None                                                             |
| `/api/users/<username>/posts`  | GET    | Get posts by a specific user | `page`: Page number (optional)                                   |
| `/api/users/update-profile`    | PUT    | Update user profile          | `bio`: User bio (optional)<br>`avatar`: Profile image (optional) |

### Example API Requests

#### Get all posts (JavaScript fetch)

```javascript
fetch('/api/posts', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  credentials: 'same-origin'
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

#### Create a new post

```javascript
const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

fetch('/api/posts/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken,
    'Accept': 'application/json'
  },
  body: JSON.stringify({
    content: 'This is a new post!'
  }),
  credentials: 'same-origin'
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django framework and community
- Bootstrap for UI components
- All contributors to the project 