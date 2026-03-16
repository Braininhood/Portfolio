import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink,
  CreditCard,
  DollarSign,
  Clock,
  Globe
} from "lucide-react";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface StripeConnectSetupProps {
  mentorId: string;
}

interface ConnectStatus {
  exists: boolean;
  accountId?: string;
  onboardingCompleted: boolean;
  chargesEnabled: boolean;
  payoutsEnabled: boolean;
  requirements?: any;
  payoutSchedule?: any;
}

const CONNECT_UNAVAILABLE_KEY = "gcreators_connect_unavailable";

// Human-readable labels for Stripe requirement field names
const REQUIREMENT_LABELS: Record<string, string> = {
  "business.profile.mcc": "Business category (Merchant Category Code)",
  "business.profile.url": "Business website",
  "external_account": "Bank account details",
  "individual.address.city": "City",
  "individual.address.line1": "Address line 1",
  "individual.address.line2": "Address line 2",
  "individual.address.postal_code": "Postal / ZIP code",
  "individual.address.state": "State / Province / Region",
  "individual.dob.day": "Date of birth (day)",
  "individual.dob.month": "Date of birth (month)",
  "individual.dob.year": "Date of birth (year)",
  "individual.email": "Email address",
  "individual.first_name": "First name",
  "individual.last_name": "Last name",
  "individual.phone": "Phone number",
  "individual.ssn_last_4": "Last 4 digits of SSN (US only)",
  "individual.id_number": "ID number (if required)",
  "settings.payments.statement_descriptor": "Statement descriptor (appears on bank statement)",
  "tos_acceptance.date": "Terms of service acceptance",
  "tos_acceptance.ip": "Terms of service acceptance",
};

const formatRequirement = (req: string): string =>
  REQUIREMENT_LABELS[req] ?? req.replace(/[._]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

// Stripe Connect Express supported countries (ISO 3166-1 alpha-2)
const PAYOUT_COUNTRIES: { code: string; name: string }[] = [
  { code: "GB", name: "United Kingdom" },
  { code: "US", name: "United States" },
  { code: "IE", name: "Ireland" },
  { code: "DE", name: "Germany" },
  { code: "FR", name: "France" },
  { code: "ES", name: "Spain" },
  { code: "IT", name: "Italy" },
  { code: "NL", name: "Netherlands" },
  { code: "BE", name: "Belgium" },
  { code: "AT", name: "Austria" },
  { code: "CH", name: "Switzerland" },
  { code: "PL", name: "Poland" },
  { code: "SE", name: "Sweden" },
  { code: "NO", name: "Norway" },
  { code: "DK", name: "Denmark" },
  { code: "FI", name: "Finland" },
  { code: "PT", name: "Portugal" },
  { code: "CA", name: "Canada" },
  { code: "AU", name: "Australia" },
  { code: "NZ", name: "New Zealand" },
  { code: "JP", name: "Japan" },
  { code: "SG", name: "Singapore" },
  { code: "HK", name: "Hong Kong" },
  { code: "MX", name: "Mexico" },
  { code: "BR", name: "Brazil" },
];

export const StripeConnectSetup = ({ mentorId }: StripeConnectSetupProps) => {
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState("GB");
  const [status, setStatus] = useState<ConnectStatus | null>(null);
  const [platformConnectUnavailable, setPlatformConnectUnavailable] = useState(() =>
    typeof sessionStorage !== "undefined" ? sessionStorage.getItem(CONNECT_UNAVAILABLE_KEY) === "1" : false
  );
  const { toast } = useToast();

  useEffect(() => {
    checkConnectStatus();
  }, [mentorId]);

  // Refetch when returning from Stripe onboarding; show clear success or info message
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const setupComplete = params.get("setup") === "complete";
    const isRefresh = params.get("refresh") === "true";
    if (!setupComplete && !isRefresh) return;

    let cancelled = false;
    (async () => {
      const data = await checkConnectStatus();
      if (cancelled) return;

      if (setupComplete) {
        if (data?.onboardingCompleted && data?.chargesEnabled && data?.payoutsEnabled) {
          toast({
            title: "All set!",
            description: "Payout setup is complete. You can receive payments from bookings and product sales.",
            variant: "default",
          });
        } else {
          toast({
            title: "Almost there",
            description: "We're verifying your details. If you just finished the form, status may update in a moment.",
            variant: "default",
          });
        }
      } else if (isRefresh) {
        toast({
          title: "Back on dashboard",
          description: "You can continue payout setup whenever you're ready.",
          variant: "default",
        });
      }

      params.delete("setup");
      params.delete("refresh");
      const qs = params.toString();
      const newUrl = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const checkConnectStatus = async (): Promise<ConnectStatus | null> => {
    setLoading(true);
    try {
      // Same auth flow as create-booking (refresh then pass token immediately)
      const { data: { session }, error: refreshErr } = await supabase.auth.refreshSession();
      if (refreshErr || !session?.access_token) {
        toast({
          title: "Session expired",
          description: "Please sign in again to view payout setup.",
          variant: "destructive",
        });
        setLoading(false);
        return null;
      }

      const { data, error } = await supabase.functions.invoke("stripe-connect-status", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (error) {
        const status = (error as { context?: Response })?.context?.status;
        if (status === 401) {
          toast({
            title: "Session expired",
            description: "Please sign in again to view payout setup.",
            variant: "destructive",
          });
          setLoading(false);
          return null;
        }
        throw error;
      }

      // Stale Stripe account was auto-cleared — treat as fresh start
      if (data?._cleared) {
        setStatus({ exists: false, onboardingCompleted: false, chargesEnabled: false, payoutsEnabled: false });
        toast({ title: "Stripe account reset", description: "Your previous Stripe account was no longer valid. Please set up a new one." });
        return null;
      }
      setStatus(data);
      return data ?? null;
    } catch (error: any) {
      if (error?.message?.includes("sign in again")) {
        toast({
          title: "Session expired",
          description: "Please sign in again to continue.",
          variant: "destructive",
        });
        setLoading(false);
        return null;
      }
      console.error("[STRIPE-CONNECT-SETUP] Error checking status:", error);
      setStatus({ exists: false, onboardingCompleted: false, chargesEnabled: false, payoutsEnabled: false });
      toast({
        title: "Error",
        description: error?.message || "Failed to check payout setup status. You can still try setting up.",
        variant: "destructive",
      });
      return null;
    } finally {
      setLoading(false);
    }
  };

  const getAuthHeaders = async (): Promise<{ Authorization: string }> => {
    const { data: { session }, error: refreshErr } = await supabase.auth.refreshSession();
    if (refreshErr || !session?.access_token) {
      throw new Error("Please sign in again to continue.");
    }
    return { Authorization: `Bearer ${session.access_token}` };
  };

  const handleCreateAccount = async () => {
    setCreating(true);
    try {
      const headers = await getAuthHeaders();

      // Step 1: Create Stripe Connect account (with user's country choice)
      const { data: accountData, error: accountError } = await supabase.functions.invoke(
        "create-stripe-connect-account",
        { headers, body: { country: selectedCountry } }
      );


      if (accountError) {
        const ctx = (accountError as { context?: { status?: number; json?: () => Promise<{ error?: string; details?: string }> } }).context;
        let msg = accountError.message;
        if (typeof ctx?.json === "function") {
          try {
            const body = await ctx.json();
            if (body?.error) msg = body.details ? `${body.error}: ${body.details}` : body.error;
          } catch {
            // ignore
          }
        }
        throw new Error(msg);
      }

      console.log("[STRIPE-CONNECT-SETUP] Account created:", accountData);

      // Step 2: Get onboarding link
      const { data: onboardingData, error: onboardingError } = await supabase.functions.invoke(
        "stripe-connect-onboarding",
        { headers }
      );

      if (onboardingError) {
        const ctx = (onboardingError as { context?: { status?: number; json?: () => Promise<{ error?: string; details?: string; _cleared?: boolean }> } }).context;
        let msg = onboardingError.message;
        let cleared = false;
        if (typeof ctx?.json === "function") {
          try {
            const body = await ctx.json();
            if (body?._cleared) cleared = true;
            if (body?.error) msg = body.details ? `${body.error}: ${body.details}` : body.error;
          } catch {
            // ignore
          }
        }
        if (cleared) {
          setCreating(false);
          setStatus({ exists: false, onboardingCompleted: false, chargesEnabled: false, payoutsEnabled: false });
          toast({ title: "Stripe account reset", description: "Please click 'Set Up Payouts' to create a new account." });
          await checkConnectStatus();
          return;
        }
        throw new Error(msg);
      }

      // Redirect to Stripe onboarding
      if (onboardingData?.url) {
        window.location.href = onboardingData.url;
      } else {
        throw new Error("No onboarding URL returned");
      }
    } catch (error: any) {
      console.error("[STRIPE-CONNECT-SETUP] Error:", error);
      const msg = error?.message ?? "Failed to start payout setup";
      const isConnectNotEnabled = typeof msg === "string" && (msg.includes("signed up for Connect") || msg.includes("connect"));
      if (isConnectNotEnabled) {
        setPlatformConnectUnavailable(true);
        try {
          sessionStorage.setItem(CONNECT_UNAVAILABLE_KEY, "1");
        } catch {
          // ignore
        }
      }
      toast({
        title: "Setup Failed",
        description: isConnectNotEnabled
          ? "Payouts are not yet available: the platform must enable Stripe Connect first. Contact support or try again later."
          : msg,
        variant: "destructive",
      });
      setCreating(false);
    }
  };

  const handleResetAccount = async () => {
    setCreating(true);
    try {
      const headers = await getAuthHeaders();
      const { error } = await supabase.functions.invoke("stripe-connect-reset", { headers });
      if (error) throw new Error(error.message);
      toast({
        title: "Account reset",
        description: "You can now set up payouts again. Choose your country before starting.",
        variant: "default",
      });
      await checkConnectStatus();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to reset",
        variant: "destructive",
      });
    } finally {
      setCreating(false);
    }
  };

  const handleContinueOnboarding = async () => {
    setCreating(true);
    try {
      const headers = await getAuthHeaders();
      const { data, error } = await supabase.functions.invoke("stripe-connect-onboarding", {
        headers,
      });

      if (error) {
        const ctx = (error as { context?: { json?: () => Promise<{ error?: string; details?: string }> } }).context;
        let msg = error.message;
        if (typeof ctx?.json === "function") {
          try {
            const body = await ctx.json();
            if (body?.error) msg = body.details ? `${body.error}: ${body.details}` : body.error;
          } catch {
            // ignore
          }
        }
        throw new Error(msg);
      }

      if (data?.url) {
        window.location.href = data.url;
      } else {
        throw new Error("No onboarding URL returned");
      }
    } catch (error: any) {
      console.error("[STRIPE-CONNECT-SETUP] Error:", error);
      toast({
        title: "Error",
        description: error?.message || "Failed to continue onboarding",
        variant: "destructive",
      });
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Account fully set up
  if (status?.onboardingCompleted && status?.chargesEnabled && status?.payoutsEnabled) {
    return (
      <Card className="border-green-500/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <CardTitle className="text-xl">Payouts Enabled</CardTitle>
                <CardDescription>Your account is ready to receive payments</CardDescription>
              </div>
            </div>
            <Badge variant="default" className="bg-green-500">
              Active
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Charges Enabled</p>
                <p className="text-xs text-muted-foreground">Can accept payments</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
              <DollarSign className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Payouts Enabled</p>
                <p className="text-xs text-muted-foreground">Can receive transfers</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
              <Clock className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">Schedule</p>
                <p className="text-xs text-muted-foreground">
                  {status?.payoutSchedule?.interval || "Weekly"}
                </p>
              </div>
            </div>
          </div>

          <Alert>
            <CreditCard className="h-4 w-4" />
            <AlertDescription>
              Your earnings will be automatically transferred to your bank account according to your payout schedule.
              Platform fee (15%) and Stripe fees (2.9% + $0.30) are deducted automatically. Your bank account was verified by Stripe when you set up payouts.
            </AlertDescription>
          </Alert>

          <div className="pt-2 rounded-lg border border-border bg-muted/50 p-4">
            <p className="text-sm font-medium mb-1">Changing your bank account</p>
            <p className="text-sm text-muted-foreground">
              For security, bank details can only be updated with the help of support. This reduces the risk of payout errors and fraud. To request a change, contact support.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Account exists but onboarding incomplete
  if (status?.exists && !status?.onboardingCompleted) {
    return (
      <Card className="border-yellow-500/20">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-500/10 rounded-lg">
              <AlertCircle className="h-6 w-6 text-yellow-500" />
            </div>
            <div>
              <CardTitle className="text-xl">Complete Payout Setup</CardTitle>
              <CardDescription>Finish connecting your bank account to receive payments</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Your payout account is incomplete. Complete the setup to start receiving earnings from bookings and product sales.
            </AlertDescription>
          </Alert>

          {status?.requirements && status.requirements.currently_due?.length > 0 && (
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
              <p className="text-sm font-semibold mb-3 text-foreground">Information needed to complete setup</p>
              <ul className="grid gap-2 sm:grid-cols-2 text-sm text-muted-foreground">
                {status.requirements.currently_due.map((req: string) => (
                  <li key={req} className="flex items-start gap-2">
                    <span className="text-amber-600 mt-0.5">•</span>
                    <span>{formatRequirement(req)}</span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-muted-foreground mt-3">
                You will provide these when you continue to Stripe&apos;s secure form.
              </p>
            </div>
          )}

          <Button
            onClick={handleContinueOnboarding}
            disabled={creating}
            size="lg"
            className="w-full"
          >
            {creating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Opening Stripe...
              </>
            ) : (
              <>
                <ExternalLink className="mr-2 h-5 w-5" />
                Continue Setup
              </>
            )}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Wrong country? Stripe cannot change country after creation.{" "}
            <button
              type="button"
              onClick={handleResetAccount}
              disabled={creating}
              className="underline hover:text-foreground font-medium"
            >
              Start over with different country
            </button>
          </p>
        </CardContent>
      </Card>
    );
  }

  // Platform hasn't enabled Connect yet – show clear message so user doesn't keep clicking
  if (platformConnectUnavailable) {
    return (
      <Card className="border-amber-500/30">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <AlertCircle className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <CardTitle className="text-xl">Payout Setup Not Available Yet</CardTitle>
              <CardDescription>Connect must be enabled on the platform before you can add your bank account</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="default" className="bg-amber-500/10 border-amber-500/30">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <AlertDescription>
              Payout setup is temporarily unavailable. The platform needs to enable Stripe Connect first. Once that’s done, you’ll be able to connect your bank account here. Contact support if you need help or try again later.
            </AlertDescription>
          </Alert>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setPlatformConnectUnavailable(false);
                try {
                  sessionStorage.removeItem(CONNECT_UNAVAILABLE_KEY);
                } catch {
                  // ignore
                }
                checkConnectStatus();
              }}
            >
              Try again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // No account exists - initial setup
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <DollarSign className="h-6 w-6 text-primary" />
          </div>
          <div>
            <CardTitle className="text-xl">Set Up Payouts</CardTitle>
            <CardDescription>Connect your bank account to receive earnings</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <CreditCard className="h-4 w-4" />
          <AlertDescription>
            To receive payments from bookings and product sales, you need to connect your bank account through Stripe.
            Stripe will collect and verify your bank details; this one-time setup takes about 5 minutes. For security, bank account changes after setup can only be made with support.
          </AlertDescription>
        </Alert>

        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Payout country
          </Label>
          <Select value={selectedCountry} onValueChange={setSelectedCountry}>
            <SelectTrigger>
              <SelectValue placeholder="Select your country" />
            </SelectTrigger>
            <SelectContent>
              {PAYOUT_COUNTRIES.map((c) => (
                <SelectItem key={c.code} value={c.code}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Stripe will show the correct forms (bank, tax, etc.) for your country
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="mt-1 p-1.5 bg-primary/10 rounded-full">
              <CheckCircle2 className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">Secure Setup</p>
              <p className="text-sm text-muted-foreground">
                Powered by Stripe, the industry standard for secure payments
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-1 p-1.5 bg-primary/10 rounded-full">
              <CheckCircle2 className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">Automatic Transfers</p>
              <p className="text-sm text-muted-foreground">
                Earnings are transferred to your bank account automatically
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-1 p-1.5 bg-primary/10 rounded-full">
              <CheckCircle2 className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">Transparent Fees</p>
              <p className="text-sm text-muted-foreground">
                15% platform fee + Stripe fees (2.9% + $0.30 per transaction)
              </p>
            </div>
          </div>
        </div>

        <Button
          onClick={handleCreateAccount}
          disabled={creating}
          size="lg"
          className="w-full"
        >
          {creating ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Setting up...
            </>
          ) : (
            <>
              <ExternalLink className="mr-2 h-5 w-5" />
              Set Up Payouts with Stripe
            </>
          )}
        </Button>

        <p className="text-xs text-muted-foreground text-center">
          You'll be redirected to Stripe to securely connect your bank account
        </p>
      </CardContent>
    </Card>
  );
};
