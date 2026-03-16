/**
 * Environment Variable Validation
 * 
 * Validates that all required environment variables are present.
 * Throws an error on app startup if any are missing, preventing
 * runtime errors and security issues.
 */

// Required environment variables for the application to run
const REQUIRED_ENV_VARS = {
  // Supabase (critical for app to function)
  VITE_SUPABASE_URL: 'Supabase project URL',
  VITE_SUPABASE_PUBLISHABLE_KEY: 'Supabase publishable/anon key',
} as const;

// Optional but recommended environment variables (client-side only)
// Vite exposes only VITE_* to the client; use VITE_STRIPE_PUBLISHABLE_KEY for Stripe
const RECOMMENDED_ENV_VARS = {
  VITE_STRIPE_PUBLISHABLE_KEY: 'Stripe publishable key (for payments)',
} as const;

interface ValidationResult {
  isValid: boolean;
  missing: string[];
  missingDescriptions: string[];
  warnings: string[];
}

/**
 * Validates environment variables
 * @returns ValidationResult with details about missing/invalid vars
 */
export function validateEnvironment(): ValidationResult {
  const missing: string[] = [];
  const missingDescriptions: string[] = [];
  const warnings: string[] = [];

  // Check required variables
  for (const [key, description] of Object.entries(REQUIRED_ENV_VARS)) {
    const value = import.meta.env[key];
    
    if (!value || value === `placeholder-${key.toLowerCase().replace(/_/g, '-')}`) {
      missing.push(key);
      missingDescriptions.push(`${key}: ${description}`);
    }
  }

  // Check recommended variables
  for (const [key, description] of Object.entries(RECOMMENDED_ENV_VARS)) {
    const value = import.meta.env[key];
    
    if (!value) {
      warnings.push(`Optional: ${key} - ${description}`);
    }
  }

  // Special validation: AI keys are server-side only (not exposed to browser)
  // This is correct and expected - they're used in Edge Functions
  const hasOpenAI = import.meta.env.OPENAI_API_KEY;
  const hasGemini = import.meta.env.GOOGLE_GEMINI_API_KEY;
  
  if (!hasOpenAI && !hasGemini) {
    console.info(
      'ℹ️ AI API keys (OPENAI_API_KEY, GOOGLE_GEMINI_API_KEY) are configured server-side ' +
      'in Edge Functions and are not exposed to the browser for security. This is expected.'
    );
  }

  return {
    isValid: missing.length === 0,
    missing,
    missingDescriptions,
    warnings,
  };
}

/**
 * Validates environment and throws error if invalid
 * Call this at app startup to fail fast
 */
export function validateEnvironmentOrThrow(): void {
  const result = validateEnvironment();

  if (!result.isValid) {
    const errorMessage = [
      '❌ Missing Required Environment Variables',
      '',
      'The following environment variables are required but not set:',
      ...result.missingDescriptions.map(desc => `  • ${desc}`),
      '',
      '📝 How to fix:',
      '  1. Copy .env.example to .env',
      '  2. Fill in the missing values',
      '  3. Restart the development server',
      '',
      'For more details, see .env.example file.',
    ].join('\n');

    throw new Error(errorMessage);
  }

  // Log warnings (non-critical)
  if (result.warnings.length > 0) {
    console.warn('⚠️ Environment Variable Warnings:');
    result.warnings.forEach(warning => {
      console.warn(`  • ${warning}`);
    });
  }
}

/**
 * Type-safe access to validated environment variables
 * Note: AI API keys (OPENAI_API_KEY, GOOGLE_GEMINI_API_KEY) are server-side only
 * and configured in Supabase Edge Functions for security
 */
export const env = {
  // Supabase
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL as string,
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string,
  
  // Stripe (optional) - Vite exposes only VITE_* to client
  stripePublishableKey: (import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? import.meta.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY) as string | undefined,
  
  // App settings
  appUrl: import.meta.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
  mode: import.meta.env.MODE,
} as const;

/**
 * Check if a specific feature is available based on env vars
 */
export const features = {
  payments: !!env.stripePublishableKey,
  // AI features are available server-side in Edge Functions
  // Check there using process.env.OPENAI_API_KEY or process.env.GOOGLE_GEMINI_API_KEY
} as const;
