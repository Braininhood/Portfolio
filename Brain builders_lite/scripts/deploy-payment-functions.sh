#!/bin/bash

# Stripe Payment & Payout System Deployment Script
# This script deploys all necessary Supabase Edge Functions for the payment system

echo "🚀 Deploying Brain Bulders Payment System Edge Functions..."
echo ""

echo "ℹ️  Using npx supabase (no global installation required)"
echo ""

# Function to deploy and check status
deploy_function() {
    local func_name=$1
    echo "📦 Deploying $func_name..."
    
    if npx supabase functions deploy $func_name; then
        echo "✅ $func_name deployed successfully"
    else
        echo "❌ Failed to deploy $func_name"
        exit 1
    fi
    echo ""
}

# Deploy all payment-related functions
echo "=== Payment Checkout Functions ==="
deploy_function "create-booking"
deploy_function "create-product-checkout"
deploy_function "verify-product-purchase"

echo "=== Webhook Handler ==="
deploy_function "stripe-webhook"

echo "=== Stripe Connect Functions ==="
deploy_function "create-stripe-connect-account"
deploy_function "stripe-connect-onboarding"
deploy_function "stripe-connect-status"

echo "=== Confirmation Functions ==="
deploy_function "send-booking-confirmation"

echo ""
echo "✅ All functions deployed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Set environment variables in Supabase Dashboard:"
echo "   - STRIPE_SECRET_KEY"
echo "   - STRIPE_WEBHOOK_SECRET"
echo "   - STRIPE_PLATFORM_FEE=0.15"
echo ""
echo "2. Configure webhook endpoint in Stripe Dashboard:"
echo "   URL: https://[your-project-ref].supabase.co/functions/v1/stripe-webhook"
echo "   Events: checkout.session.completed, payment_intent.succeeded, payment_intent.payment_failed, charge.refunded"
echo ""
echo "3. Test the payment flow with test cards"
echo ""
echo "📚 See docs/STRIPE_SETUP_GUIDE.md for detailed instructions"
