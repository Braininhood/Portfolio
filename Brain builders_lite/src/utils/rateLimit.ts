/**
 * Client-Side Rate Limiting Utility
 * 
 * Prevents abuse by limiting the rate of actions a user can perform.
 * Uses localStorage to persist rate limit state across page refreshes.
 * 
 * Note: This is CLIENT-SIDE protection. For production, also implement
 * server-side rate limiting in Supabase Edge Functions.
 */

export interface RateLimitConfig {
  /** Maximum number of requests allowed */
  maxRequests: number;
  /** Time window in milliseconds */
  windowMs: number;
  /** Unique key for this rate limit (e.g., 'auth:login', 'message:send') */
  key: string;
}

interface RateLimitEntry {
  timestamps: number[];
  blockedUntil?: number;
}

/**
 * Rate Limiter class
 * Tracks request timestamps and enforces limits
 */
class RateLimiter {
  private storageKey = 'rate_limits';
  
  /**
   * Load rate limit data from localStorage
   */
  private load(): Record<string, RateLimitEntry> {
    try {
      const data = localStorage.getItem(this.storageKey);
      return data ? JSON.parse(data) : {};
    } catch {
      return {};
    }
  }
  
  /**
   * Save rate limit data to localStorage
   */
  private save(data: Record<string, RateLimitEntry>): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(data));
    } catch {
      // Silently fail if localStorage is full or unavailable
    }
  }
  
  /**
   * Clean up old timestamps outside the window
   */
  private cleanTimestamps(timestamps: number[], windowMs: number): number[] {
    const now = Date.now();
    const windowStart = now - windowMs;
    return timestamps.filter(time => time > windowStart);
  }
  
  /**
   * Check if a request is allowed under the rate limit
   * 
   * @param config Rate limit configuration
   * @returns { allowed: boolean, remaining: number, resetAt: Date | null }
   */
  check(config: RateLimitConfig): {
    allowed: boolean;
    remaining: number;
    resetAt: Date | null;
    waitMs: number;
  } {
    const now = Date.now();
    const allLimits = this.load();
    const entry = allLimits[config.key] || { timestamps: [] };
    
    // Check if currently blocked
    if (entry.blockedUntil && entry.blockedUntil > now) {
      return {
        allowed: false,
        remaining: 0,
        resetAt: new Date(entry.blockedUntil),
        waitMs: entry.blockedUntil - now,
      };
    }
    
    // Clean old timestamps
    entry.timestamps = this.cleanTimestamps(entry.timestamps, config.windowMs);
    
    // Check limit
    if (entry.timestamps.length >= config.maxRequests) {
      // Rate limit exceeded
      const oldestTimestamp = entry.timestamps[0];
      const resetAt = oldestTimestamp + config.windowMs;
      const waitMs = resetAt - now;
      
      return {
        allowed: false,
        remaining: 0,
        resetAt: new Date(resetAt),
        waitMs,
      };
    }
    
    // Allow request
    entry.timestamps.push(now);
    allLimits[config.key] = entry;
    this.save(allLimits);
    
    return {
      allowed: true,
      remaining: config.maxRequests - entry.timestamps.length,
      resetAt: null,
      waitMs: 0,
    };
  }
  
  /**
   * Block a key for a specific duration (used after failed auth attempts)
   * 
   * @param config Rate limit configuration
   * @param blockDurationMs How long to block (milliseconds)
   */
  block(config: RateLimitConfig, blockDurationMs: number): void {
    const now = Date.now();
    const allLimits = this.load();
    const entry = allLimits[config.key] || { timestamps: [] };
    
    entry.blockedUntil = now + blockDurationMs;
    entry.timestamps = []; // Clear timestamps on block
    
    allLimits[config.key] = entry;
    this.save(allLimits);
  }
  
  /**
   * Reset rate limit for a specific key
   */
  reset(key: string): void {
    const allLimits = this.load();
    delete allLimits[key];
    this.save(allLimits);
  }
  
  /**
   * Get current status without consuming a request
   */
  getStatus(config: RateLimitConfig): {
    remaining: number;
    resetAt: Date | null;
    isBlocked: boolean;
  } {
    const now = Date.now();
    const allLimits = this.load();
    const entry = allLimits[config.key] || { timestamps: [] };
    
    // Check if blocked
    if (entry.blockedUntil && entry.blockedUntil > now) {
      return {
        remaining: 0,
        resetAt: new Date(entry.blockedUntil),
        isBlocked: true,
      };
    }
    
    // Clean old timestamps
    const cleanTimestamps = this.cleanTimestamps(entry.timestamps, config.windowMs);
    const remaining = Math.max(0, config.maxRequests - cleanTimestamps.length);
    
    return {
      remaining,
      resetAt: cleanTimestamps[0] ? new Date(cleanTimestamps[0] + config.windowMs) : null,
      isBlocked: false,
    };
  }
}

// Singleton instance
export const rateLimiter = new RateLimiter();

/**
 * Pre-configured rate limit rules for common actions
 */
export const rateLimits = {
  // Authentication
  authLogin: {
    key: 'auth:login',
    maxRequests: 5,
    windowMs: 15 * 60 * 1000, // 15 minutes
  },
  authSignup: {
    key: 'auth:signup',
    maxRequests: 3,
    windowMs: 60 * 60 * 1000, // 1 hour
  },
  authPasswordReset: {
    key: 'auth:password_reset',
    maxRequests: 3,
    windowMs: 60 * 60 * 1000, // 1 hour
  },
  
  // Messages
  messageSend: {
    key: 'message:send',
    maxRequests: 10,
    windowMs: 60 * 1000, // 1 minute
  },
  messageSendHourly: {
    key: 'message:send:hourly',
    maxRequests: 100,
    windowMs: 60 * 60 * 1000, // 1 hour
  },
  
  // Bookings
  bookingCreate: {
    key: 'booking:create',
    maxRequests: 5,
    windowMs: 60 * 60 * 1000, // 1 hour
  },
  bookingCreateDaily: {
    key: 'booking:create:daily',
    maxRequests: 20,
    windowMs: 24 * 60 * 60 * 1000, // 24 hours
  },
  
  // Profile updates
  profileUpdate: {
    key: 'profile:update',
    maxRequests: 10,
    windowMs: 60 * 60 * 1000, // 1 hour
  },
  
  // API calls (general)
  apiGeneral: {
    key: 'api:general',
    maxRequests: 60,
    windowMs: 60 * 1000, // 1 minute
  },
} as const;

/**
 * Helper function to format wait time in human-readable format
 */
export function formatWaitTime(ms: number): string {
  const seconds = Math.ceil(ms / 1000);
  
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? 's' : ''}`;
  }
  
  const minutes = Math.ceil(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
  
  const hours = Math.ceil(minutes / 60);
  return `${hours} hour${hours !== 1 ? 's' : ''}`;
}

/**
 * Example usage:
 * 
 * ```typescript
 * import { rateLimiter, rateLimits, formatWaitTime } from '@/utils/rateLimit';
 * 
 * // Check if action is allowed
 * const result = rateLimiter.check(rateLimits.messageSend);
 * 
 * if (!result.allowed) {
 *   const waitTime = formatWaitTime(result.waitMs);
 *   toast.error(`Too many messages. Please wait ${waitTime}.`);
 *   return;
 * }
 * 
 * // Perform action
 * await sendMessage();
 * 
 * // Show remaining attempts
 * toast.success(`Message sent! You can send ${result.remaining} more messages.`);
 * ```
 */
