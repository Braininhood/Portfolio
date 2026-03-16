type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: unknown;
}

class Logger {
  private isDevelopment = import.meta.env.DEV;

  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const contextStr = context ? ` ${JSON.stringify(context)}` : '';
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${contextStr}`;
  }

  debug(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.debug(this.formatMessage('debug', message, context));
    }
  }

  info(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.info(this.formatMessage('info', message, context));
    }
  }

  warn(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.warn(this.formatMessage('warn', message, context));
    } else {
      // In production, send to error tracking service (Sentry, etc.)
      // this.sendToErrorTracking('warn', message, context);
    }
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    const errorContext = {
      ...context,
      error: error instanceof Error ? {
        message: error.message,
        stack: error.stack,
        name: error.name,
      } : error,
    };

    if (this.isDevelopment) {
      console.error(this.formatMessage('error', message, errorContext));
    } else {
      // In production, send to error tracking service (Sentry, etc.)
      // this.sendToErrorTracking('error', message, errorContext);
    }
  }

  // Future: Add Sentry integration
  // private sendToErrorTracking(level: LogLevel, message: string, context?: LogContext): void {
  //   if (typeof window !== 'undefined' && window.Sentry) {
  //     window.Sentry.captureMessage(message, {
  //       level: level as SentryLevel,
  //       extra: context,
  //     });
  //   }
  // }
}

export const logger = new Logger();
