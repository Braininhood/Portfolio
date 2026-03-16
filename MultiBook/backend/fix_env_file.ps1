# Script to create/fix .env file for PostgreSQL
$envContent = @"
# Django Settings
SECRET_KEY=OHBYKGcXUEFNoqaN_XmKXcEmHP5-nKqYyMOl_p3vSDvPptP7A8uH1rAmrrY5pjUZW34
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://multibook_user:multibook_pass@localhost:5432/multibook_db

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000
CORS_ALLOW_CREDENTIALS=True

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# SMS Settings (Twilio - Optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Payment Gateways (Stripe)
STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Payment Gateways (PayPal)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=sandbox

# Google Services
GOOGLE_MAPS_API_KEY=
GOOGLE_PLACES_API_KEY=
GOOGLE_CALENDAR_CLIENT_ID=
GOOGLE_CALENDAR_CLIENT_SECRET=

# Microsoft Services
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
"@

$envContent | Out-File -FilePath .env -Encoding utf8 -NoNewline
Write-Host ".env file created/updated successfully!" -ForegroundColor Green
