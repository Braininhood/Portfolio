import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Calendar, Link, Unlink, RefreshCw, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface GoogleCalendarSyncProps {
  mentorId: string;
}

interface CalendarConnection {
  id: string;
  provider: string;
  sync_enabled: boolean;
  last_synced_at: string | null;
  calendar_id: string | null;
}

export const GoogleCalendarSync = ({ mentorId }: GoogleCalendarSyncProps) => {
  const [connection, setConnection] = useState<CalendarConnection | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadConnection();
    
    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const calendarConnected = urlParams.get('calendar_connected');
    if (calendarConnected === 'true') {
      toast({
        title: "Google Calendar connected",
        description: "Your calendar has been successfully linked",
      });
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      loadConnection();
    } else if (calendarConnected === 'false') {
      toast({
        title: "Connection failed",
        description: urlParams.get('error') || "Could not connect to Google Calendar",
        variant: "destructive",
      });
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [mentorId]);

  const loadConnection = async () => {
    try {
      const { data, error } = await (supabase
        .from("mentor_calendar_connections" as any)
        .select("*")
        .eq("mentor_id", mentorId)
        .maybeSingle() as any);

      if (error && error.code !== 'PGRST116') throw error;
      setConnection(data as CalendarConnection | null);
    } catch (error: any) {
      console.error("Error loading calendar connection:", error);
    } finally {
      setLoading(false);
    }
  };

  const connectGoogleCalendar = async () => {
    setConnecting(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      console.log("[GoogleCalendarSync] Session check:", { 
        hasSession: !!session, 
        userId: session?.user?.id,
        accessToken: session?.access_token ? 'present' : 'missing'
      });
      
      if (!session) {
        toast({
          title: "Authentication required",
          description: "Please log in to connect your calendar",
          variant: "destructive",
        });
        return;
      }

      console.log("[GoogleCalendarSync] Calling google-calendar-auth function...");
      
      // Call edge function to get OAuth URL
      const response = await supabase.functions.invoke('google-calendar-auth', {
        body: { 
          action: 'get_auth_url',
          mentorId,
          redirectUrl: window.location.href
        }
      });

      console.log("[GoogleCalendarSync] Raw response:", response);

      // Try to extract error details from the FunctionsHttpError
      if (response.error) {
        console.error("[GoogleCalendarSync] Error object:", response.error);
        
        // The error might have a context or message property
        let errorMessage = "Could not connect to Google Calendar";
        
        if (response.error.context) {
          console.log("[GoogleCalendarSync] Error context:", response.error.context);
        }
        
        // Try to get the response body if available
        if (response.error instanceof Error) {
          errorMessage = response.error.message;
        }
        
        throw new Error(errorMessage);
      }

      console.log("[GoogleCalendarSync] Function data:", response.data);

      if (response.data?.authUrl) {
        window.location.href = response.data.authUrl;
      } else {
        throw new Error("No auth URL returned");
      }
    } catch (error: any) {
      console.error("[GoogleCalendarSync] Error:", error);
      toast({
        title: "Connection failed",
        description: error.message || "Could not initiate Google Calendar connection",
        variant: "destructive",
      });
    } finally {
      setConnecting(false);
    }
  };

  const disconnectCalendar = async () => {
    try {
      const { error } = await (supabase
        .from("mentor_calendar_connections" as any)
        .delete()
        .eq("mentor_id", mentorId) as any);

      if (error) throw error;

      setConnection(null);
      toast({
        title: "Calendar disconnected",
        description: "Your Google Calendar has been unlinked",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const syncNow = async () => {
    setSyncing(true);
    try {
      const { data, error } = await supabase.functions.invoke('google-calendar-sync', {
        body: { 
          mentorId,
          action: 'sync'
        }
      });

      if (error) throw error;

      toast({
        title: "Sync complete",
        description: `Synced ${data?.eventsImported || 0} events from your calendar`,
      });

      loadConnection();
    } catch (error: any) {
      toast({
        title: "Sync failed",
        description: error.message || "Could not sync with Google Calendar",
        variant: "destructive",
      });
    } finally {
      setSyncing(false);
    }
  };

  const toggleSync = async (enabled: boolean) => {
    try {
      const { error } = await (supabase
        .from("mentor_calendar_connections" as any)
        .update({ sync_enabled: enabled })
        .eq("mentor_id", mentorId) as any);

      if (error) throw error;

      setConnection(prev => prev ? { ...prev, sync_enabled: enabled } : null);
      toast({
        title: enabled ? "Sync enabled" : "Sync disabled",
        description: enabled 
          ? "Your calendar will automatically sync" 
          : "Automatic sync has been turned off",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="p-4 sm:p-6">
        <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Calendar Sync
        </CardTitle>
        <CardDescription className="text-sm">
          Connect your Google Calendar to automatically sync your availability
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 space-y-4">
        {!connection ? (
          <>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Connect your Google Calendar to automatically import busy times and keep your availability up to date.
              </AlertDescription>
            </Alert>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={connectGoogleCalendar}
                disabled={connecting}
                className="flex items-center gap-2"
              >
                <Link className="h-4 w-4" />
                {connecting ? "Connecting..." : "Connect Google Calendar"}
              </Button>
            </div>

            <p className="text-xs text-muted-foreground">
              We'll only read your calendar events to block busy times. We never modify your personal calendar.
            </p>
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Calendar className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-sm">Google Calendar</p>
                  <p className="text-xs text-muted-foreground">
                    {connection.calendar_id || "Primary calendar"}
                  </p>
                </div>
              </div>
              <Badge variant={connection.sync_enabled ? "default" : "secondary"}>
                {connection.sync_enabled ? "Active" : "Paused"}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="sync-toggle" className="text-sm font-medium">
                  Automatic sync
                </Label>
                <p className="text-xs text-muted-foreground">
                  Keep availability updated with your calendar
                </p>
              </div>
              <Switch
                id="sync-toggle"
                checked={connection.sync_enabled}
                onCheckedChange={toggleSync}
              />
            </div>

            {connection.last_synced_at && (
              <p className="text-xs text-muted-foreground">
                Last synced: {new Date(connection.last_synced_at).toLocaleString()}
              </p>
            )}

            <div className="flex flex-wrap gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={syncNow}
                disabled={syncing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? "Syncing..." : "Sync Now"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={disconnectCalendar}
                className="text-destructive hover:text-destructive"
              >
                <Unlink className="h-4 w-4 mr-2" />
                Disconnect
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default GoogleCalendarSync;
