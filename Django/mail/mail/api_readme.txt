# Mail API Documentation for Postman

This document provides instructions on how to use Postman to interact with the Mail application's API endpoints running on your local development server.

## Getting Started with Postman

1. Download and install Postman from https://www.postman.com/downloads/
2. Open Postman and create a new request by selecting the "+" tab
3. Set up the request URL with your local server address: http://127.0.0.1:8000

## Setting Up Your Environment

1. Click the "Environments" tab in Postman (or the gear icon)
2. Click "Create Environment" and name it "Mail API Local"
3. Add these variables:
   - `base_url`: `http://127.0.0.1:8000`
   - `csrf_token`: [Leave blank for now]
4. Click "Save"
5. Select your new environment from the dropdown in the upper right corner

## Authentication

All API endpoints require authentication. You will need to:
1. Log into the web application first in your browser at http://127.0.0.1:8000/login
2. Make requests from Postman with cookies enabled
3. Include the CSRF token in your requests

### Getting the CSRF Token

For POST, PUT, and DELETE requests, you need to include the CSRF token:
1. In your browser, open http://127.0.0.1:8000 and log in
2. Open browser's Developer Tools (F12) > Application/Storage tab > Cookies > http://127.0.0.1:8000
3. Find the 'csrftoken' cookie and copy its value
4. In Postman, update your environment variable `csrf_token` with this value

## API Endpoints

### 1. Get Mailbox Emails

**Request:**
- Method: GET
- URL: `{{base_url}}/emails/{mailbox}`
- Where `{mailbox}` can be: "inbox", "sent", "archive", or "drafts"

**Example:**
```
GET http://127.0.0.1:8000/emails/inbox
```

**Response:** JSON array of email objects

### 2. Compose Email

**Request:**
- Method: POST
- URL: `{{base_url}}/emails`
- Headers:
  - Content-Type: application/json
  - X-CSRFToken: {{csrf_token}}
- Body:
```json
{
  "recipients": "user1@example.com, user2@example.com",
  "subject": "Meeting Tomorrow",
  "body": "Can we discuss the project status?",
  "is_draft": false
}
```

**Example:**
```
POST http://127.0.0.1:8000/emails
```

**Response:**
```json
{
  "message": "Email sent successfully.",
  "id": 123
}
```

### 3. Save Draft

**Request:**
- Method: POST
- URL: `{{base_url}}/emails`
- Headers:
  - Content-Type: application/json
  - X-CSRFToken: {{csrf_token}}
- Body:
```json
{
  "recipients": "user1@example.com",
  "subject": "Draft Message",
  "body": "This is a draft",
  "is_draft": true
}
```

**Example:**
```
POST http://127.0.0.1:8000/emails
```

**Response:**
```json
{
  "message": "Email sent successfully.",
  "id": 124
}
```

### 4. Get Single Email

**Request:**
- Method: GET
- URL: `{{base_url}}/emails/{email_id}`
- Where `{email_id}` is the numerical ID of the email

**Example:**
```
GET http://127.0.0.1:8000/emails/42
```

**Response:** Single email object
```json
{
  "id": 42,
  "sender": "sender@example.com",
  "recipients": ["recipient@example.com"],
  "subject": "Test Email",
  "body": "This is a test email",
  "timestamp": "Mar 31 2025, 10:15 AM",
  "read": false,
  "archived": false,
  "is_draft": false
}
```

### 5. Update Email (Mark as Read/Unread or Archive/Unarchive)

**Request:**
- Method: PUT
- URL: `{{base_url}}/emails/{email_id}`
- Headers:
  - Content-Type: application/json
  - X-CSRFToken: {{csrf_token}}
- Body (to mark as read):
```json
{
  "read": true
}
```
- Body (to archive):
```json
{
  "archived": true
}
```

**Example:**
```
PUT http://127.0.0.1:8000/emails/42
```

**Response:** Updated email object

### 6. Update Draft

**Request:**
- Method: PUT
- URL: `{{base_url}}/emails/{email_id}`
- Headers:
  - Content-Type: application/json
  - X-CSRFToken: {{csrf_token}}
- Body:
```json
{
  "recipients": "updated@example.com",
  "subject": "Updated Draft",
  "body": "This draft has been updated",
  "is_draft": true
}
```

**Example:**
```
PUT http://127.0.0.1:8000/emails/45
```

**Response:** Updated email object

### 7. Delete Draft

**Request:**
- Method: DELETE
- URL: `{{base_url}}/emails/{email_id}`
- Headers:
  - X-CSRFToken: {{csrf_token}}

**Example:**
```
DELETE http://127.0.0.1:8000/emails/45
```

**Response:**
```json
{
  "message": "Draft deleted successfully."
}
```

## Creating a Postman Collection for Local Testing

### Creating a Collection

1. Click the "New" button and select "Collection"
2. Name it "Mail API Local"
3. Add requests for each endpoint described above

### Cookie Management

To properly authenticate with your local server:

1. In Postman, go to Settings (gear icon) > General
2. Ensure "Automatically follow redirects" is enabled
3. Under "Cookies", click "Cookies" to open the Cookie Manager
4. Click the "+" button to add a domain
5. Enter "127.0.0.1" as the domain name
6. You can either:
   - Manually add the cookies from your browser, or
   - Use the Postman Interceptor extension to sync cookies automatically

### Request Examples With Full URLs

#### Example 1: Get Inbox
1. Create a GET request
2. URL: `http://127.0.0.1:8000/emails/inbox`
3. Send the request and view emails in your inbox

#### Example 2: Send Email
1. Create a POST request
2. URL: `http://127.0.0.1:8000/emails`
3. Headers:
   - Content-Type: application/json
   - X-CSRFToken: {{csrf_token}}
4. Body (raw JSON):
```json
{
  "recipients": "recipient@example.com",
  "subject": "Test from Postman",
  "body": "This is a test email sent via Postman to my local server"
}
```
5. Send the request

## Troubleshooting Local Server Connections

- **Server not running**: Make sure your Django server is running with `python manage.py runserver`
- **401 Unauthorized**: Make sure you're logged in to the application in your browser at http://127.0.0.1:8000
- **403 Forbidden**: Check that you've included the correct CSRF token
- **400 Bad Request**: Verify the format of your request body
- **404 Not Found**: Ensure the email ID or mailbox name is correct
- **Connection refused**: Verify that your server is running on port 8000

## Notes on CSRF Protection with Django

Django uses CSRF protection which requires:
1. A CSRF token in the request headers for unsafe methods (POST, PUT, DELETE)
2. The same cookies that your browser session has

For local development, you can:
- Use the Postman's cookie jar feature
- Use the Postman Interceptor extension to sync cookies automatically from Chrome
- Manually copy cookies from your browser to Postman

## Testing Workflow for Local Development

1. Start your Django server with `python manage.py runserver`
2. Log in to your application at http://127.0.0.1:8000
3. Get your CSRF token from browser cookies
4. Update your Postman environment variable
5. Send API requests through Postman to test your endpoints