# Google Calendar Sync Setup Guide - Step by Step Instructions

This guide will walk you through setting up Google Calendar synchronization for your MultiBook application.

## 📋 Prerequisites

- A Google Cloud Platform (GCP) account
- Access to Google Cloud Console
- Your application's backend running (Django)
- Python environment with pip

---

## Step 1: Create a Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project**
   - Click the project dropdown at the top
   - Click "New Project"
   - Enter project name: `MultiBook Calendar Sync` (or your preferred name)
   - Click "Create"
   - Wait for the project to be created (may take a few seconds)

3. **Select Your Project**
   - Make sure your new project is selected in the project dropdown

---

## Step 2: Enable Google Calendar API

1. **Navigate to APIs & Services**
   - In the left sidebar, click "APIs & Services" → "Library"
   - Or go directly to: https://console.cloud.google.com/apis/library

2. **Search for Google Calendar API**
   - In the search bar, type: `Google Calendar API`
   - Click on "Google Calendar API" from the results

3. **Enable the API**
   - Click the "Enable" button
   - Wait for the API to be enabled (usually takes a few seconds)

---

## Step 3: Create OAuth 2.0 Credentials

1. **Go to Credentials Page**
   - In the left sidebar, click "APIs & Services" → "Credentials"
   - Or go directly to: https://console.cloud.google.com/apis/credentials

2. **Configure OAuth Consent Screen** (First Time Only)
   - Click "Configure Consent Screen" button
   - Select "External" (unless you have a Google Workspace account)
   - Click "Create"
   
   **Fill in the OAuth Consent Screen:**
   - **App name**: `MultiBook` (or your app name)
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
   - Click "Save and Continue"
   
   **Scopes** (Step 2):
   - Click "Add or Remove Scopes"
   - Search for: `https://www.googleapis.com/auth/calendar`
   - Check the box for "Calendar" scope
   - Click "Update" → "Save and Continue"
   
   **Test users** (Step 3 - Optional for testing):
   - Add test users if your app is in testing mode
   - Click "Save and Continue"
   
   **Summary** (Step 4):
   - Review the information
   - Click "Back to Dashboard"

3. **Create OAuth 2.0 Client ID**
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, select "Web application"
   
   **Application Type**: Web application
   
   **Name**: `MultiBook Calendar Sync` (or your preferred name)
   
   **Authorized JavaScript origins**:
   - Click "Add URI"
   - Add: `http://localhost:8000` (for local development)
   - Add: `https://yourdomain.com` (for production - replace with your actual domain)
   
   **Authorized redirect URIs**:
   - Click "Add URI"
   - Add: `http://localhost:8000/api/calendar/google/callback/` (for local development)
   - Add: `https://yourdomain.com/api/calendar/google/callback/` (for production)
   
   - Click "Create"

4. **Copy Your Credentials**
   - A popup will appear with your **Client ID** and **Client Secret**
   - **IMPORTANT**: Copy these values immediately - you won't be able to see the secret again!
   - Click "OK" to close the popup

---

## Step 4: Install Required Python Libraries

Open your terminal/command prompt in your backend directory and run:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Or if using a virtual environment:

```bash
# Activate your virtual environment first
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Then install
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## Step 5: Configure Environment Variables

1. **Open your `.env` file** in the `backend` directory
   - If it doesn't exist, copy `backend/env.example` to `backend/.env`

2. **Add the following variables:**

```bash
# Google Calendar OAuth Credentials
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Redirect URI (must match what you configured in Google Cloud Console)
GOOGLE_REDIRECT_URI=http://localhost:8000/api/calendar/google/callback/

# For production, use:
# GOOGLE_REDIRECT_URI=https://yourdomain.com/api/calendar/google/callback/
```

**Example (use placeholders, never commit real values):**
```bash
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
GOOGLE_REDIRECT_URI=http://localhost:8000/api/calendar/google/callback/
```

**Replace:**
- `your-client-id-here.apps.googleusercontent.com` with your actual Client ID
- `your-client-secret-here` with your actual Client Secret
- `yourdomain.com` with your production domain (when deploying)

---

## Step 6: Verify Django Settings

The settings are already configured in `backend/config/settings/base.py`. The code will automatically read:
- `GOOGLE_CLIENT_ID` from your `.env` file
- `GOOGLE_CLIENT_SECRET` from your `.env` file  
- `GOOGLE_REDIRECT_URI` from your `.env` file (defaults to `http://localhost:8000/api/calendar/google/callback/`)

No code changes needed - just make sure your `.env` file has the correct values!

---

## Step 7: Restart Your Django Server

After adding the environment variables, restart your Django development server:

```bash
# Stop the server (Ctrl+C)
# Then restart
python manage.py runserver
```

---

## Step 8: Test the Integration

1. **Start your frontend and backend servers**

2. **Log in to your application** as a user (customer, staff, or admin)

3. **Navigate to Calendar Settings**
   - Go to: `/settings/calendar` (or wherever your calendar settings page is)

4. **Connect Google Calendar**
   - Click "Connect Google Calendar" button
   - You'll be redirected to Google's OAuth consent screen
   - Sign in with your Google account
   - Grant permissions to access your calendar
   - You'll be redirected back to your app

5. **Verify Connection**
   - Check that the status shows "Connected"
   - Create a test appointment
   - Check your Google Calendar - the appointment should appear!

---

## 🔧 Troubleshooting

### Error: "Google OAuth credentials not configured"
- **Solution**: Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in your `.env` file
- Restart your Django server after adding them

### Error: "redirect_uri_mismatch"
- **Solution**: Make sure the redirect URI in your `.env` exactly matches what you configured in Google Cloud Console
- Check for trailing slashes: `/api/calendar/google/callback/` vs `/api/calendar/google/callback`

### Error: "Library not installed"
- **Solution**: Run `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
- Make sure you're in the correct virtual environment

### Error: "Access blocked: This app's request is invalid"
- **Solution**: 
  - Make sure your OAuth consent screen is configured
  - If in testing mode, add your email as a test user
  - For production, submit your app for verification

### Appointments not syncing to Google Calendar
- **Solution**:
  - Check that the user has successfully connected their calendar
  - Verify the appointment status is `confirmed` or `in_progress`
  - Check Django logs for any error messages
  - Ensure the Google Calendar API is enabled in your GCP project

---

## 📝 Production Deployment Checklist

When deploying to production:

1. ✅ Update `GOOGLE_REDIRECT_URI` in production `.env` to your production domain
2. ✅ Add production redirect URI in Google Cloud Console
3. ✅ Add production JavaScript origin in Google Cloud Console
4. ✅ Submit OAuth consent screen for verification (if needed)
5. ✅ Test the OAuth flow on production domain
6. ✅ Monitor error logs for any OAuth issues

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use different credentials** for development and production
3. **Rotate credentials** if they're ever exposed
4. **Limit OAuth scopes** to only what's needed (`calendar` scope)
5. **Use HTTPS** in production (required for OAuth)

---

## 📚 Additional Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 for Web Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google Cloud Console](https://console.cloud.google.com/)

---

## ✅ Verification Checklist

- [ ] Google Cloud Project created
- [ ] Google Calendar API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth 2.0 Client ID created
- [ ] Redirect URIs configured correctly
- [ ] Python libraries installed
- [ ] Environment variables set in `.env`
- [ ] Django server restarted
- [ ] Test connection successful
- [ ] Appointments syncing to Google Calendar

---

**Need Help?** Check the error logs in your Django console or Google Cloud Console for detailed error messages.
