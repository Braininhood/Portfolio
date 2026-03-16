@echo off
REM Stripe Payment & Payout System Deployment Script for Windows
REM This script deploys all necessary Supabase Edge Functions for the payment system

echo.
echo ========================================
echo Brain Bulders Payment System Deployment
echo ========================================
echo.

echo [INFO] Using npx supabase (no global installation required)
echo.

echo === Payment Checkout Functions ===
echo.

echo [DEPLOYING] create-booking...
call npx supabase functions deploy create-booking
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] create-booking deployment failed
    exit /b 1
)
echo [OK] create-booking deployed
echo.

echo [DEPLOYING] create-product-checkout...
call npx supabase functions deploy create-product-checkout
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] create-product-checkout deployment failed
    exit /b 1
)
echo [OK] create-product-checkout deployed
echo.

echo [DEPLOYING] verify-product-purchase...
call npx supabase functions deploy verify-product-purchase
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] verify-product-purchase deployment failed
    exit /b 1
)
echo [OK] verify-product-purchase deployed
echo.

echo === Webhook Handler ===
echo.

echo [DEPLOYING] stripe-webhook...
call npx supabase functions deploy stripe-webhook
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] stripe-webhook deployment failed
    exit /b 1
)
echo [OK] stripe-webhook deployed
echo.

echo === Stripe Connect Functions ===
echo.

echo [DEPLOYING] create-stripe-connect-account...
call npx supabase functions deploy create-stripe-connect-account
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] create-stripe-connect-account deployment failed
    exit /b 1
)
echo [OK] create-stripe-connect-account deployed
echo.

echo [DEPLOYING] stripe-connect-onboarding...
call npx supabase functions deploy stripe-connect-onboarding
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] stripe-connect-onboarding deployment failed
    exit /b 1
)
echo [OK] stripe-connect-onboarding deployed
echo.

echo [DEPLOYING] stripe-connect-status...
call npx supabase functions deploy stripe-connect-status
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] stripe-connect-status deployment failed
    exit /b 1
)
echo [OK] stripe-connect-status deployed
echo.

echo === Confirmation Functions ===
echo.

echo [DEPLOYING] send-booking-confirmation...
call npx supabase functions deploy send-booking-confirmation
if %ERRORLEVEL% NEQ 0 (
    echo [FAILED] send-booking-confirmation deployment failed
    exit /b 1
)
echo [OK] send-booking-confirmation deployed
echo.

echo.
echo ========================================
echo [SUCCESS] All functions deployed!
echo ========================================
echo.
echo Next Steps:
echo.
echo 1. Set environment variables in Supabase Dashboard:
echo    - STRIPE_SECRET_KEY
echo    - STRIPE_WEBHOOK_SECRET
echo    - STRIPE_PLATFORM_FEE=0.15
echo.
echo 2. Configure webhook endpoint in Stripe Dashboard:
echo    URL: https://[your-project-ref].supabase.co/functions/v1/stripe-webhook
echo    Events: checkout.session.completed, payment_intent.succeeded,
echo            payment_intent.payment_failed, charge.refunded
echo.
echo 3. Test the payment flow with test cards
echo.
echo See docs/STRIPE_SETUP_GUIDE.md for detailed instructions
echo.

pause
