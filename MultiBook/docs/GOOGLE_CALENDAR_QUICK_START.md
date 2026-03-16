# Google Calendar Setup - Quick Start ✅

## ✅ Configuration Complete!

Your Google Calendar OAuth credentials have been configured:

- **Client ID**: `YOUR_GOOGLE_CLIENT_ID`
- **Client Secret**: `YOUR_GOOGLE_CLIENT_SECRET`
- **Redirect URI**: `http://localhost:8000/api/calendar/google/callback/`

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Add Redirect URI in Google Cloud Console ⚠️ REQUIRED

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under **"Authorized redirect URIs"**, add:
   ```
   http://localhost:8000/api/calendar/google/callback/
   ```
4. Click **"Save"**

### Step 2: Install Python Libraries

```bash
cd backend
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Step 3: Restart Django Server

```bash
# Stop server (Ctrl+C), then restart:
python manage.py runserver
```

---

## ✅ Done! Test It

1. Log in to your app
2. Go to Calendar Settings (`/settings/calendar`)
3. Click "Connect Google Calendar"
4. Authorize with Google
5. Create a test appointment
6. Check your Google Calendar - it should appear!

---

## 📝 Important Notes

- **Supabase OAuth** = User authentication (login) ✅ Already working
- **Google Cloud OAuth** = Calendar sync ✅ Just configured
- These are **separate** and both needed!

---

## 🐛 Troubleshooting

**"redirect_uri_mismatch"** → Add redirect URI in Google Cloud Console (Step 1 above)

**"Library not installed"** → Run Step 2 above

**"Credentials not configured"** → Check `backend/.env` has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

---

**Full Guide**: See `GOOGLE_CALENDAR_SETUP_GUIDE.md` for detailed instructions.
