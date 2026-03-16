/**
 * Minimal Deno type declarations so the IDE can type-check Edge Functions
 * when the Deno extension is not active. Runtime is always Deno (Supabase).
 */
declare namespace Deno {
  export const env: {
    get(key: string): string | undefined;
  };
}

declare module "https://deno.land/std@0.190.0/http/server.ts" {
  export function serve(
    handler: (req: Request) => Response | Promise<Response>
  ): void;
}

declare module "https://esm.sh/stripe@18.5.0" {
  export default class Stripe {
    constructor(key: string, options?: { apiVersion?: string });
    checkout: {
      sessions: {
        create(params: unknown): Promise<{ id: string; url: string | null }>;
      };
    };
    customers: { list(options: unknown): Promise<{ data: unknown[] }> };
  }
}

declare module "https://esm.sh/@supabase/supabase-js@2.57.2" {
  export function createClient(
    url: string,
    key: string,
    options?: { global?: { headers?: Record<string, string> } }
  ): {
    auth: { getUser(): Promise<{ data: { user: { id: string; email?: string } | null }; error: unknown }> };
    from(_table: string): any;
  };
}
