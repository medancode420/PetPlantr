/**
 * 📝 Enhanced Logger Service
 * Production-ready logging with structured data, different levels, and external integrations
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
  requestId?: string;
  userId?: string;
  orderId?: string;
  printerId?: string;
  error?: Error;
}

export interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableCloudWatch: boolean;
  enableStructured: boolean;
  serviceName: string;
  environment: string;
}

class Logger {
  private config: LoggerConfig;
  private logLevels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
    fatal: 4
  };

  constructor(config?: Partial<LoggerConfig>) {
    this.config = {
      level: (process.env.LOG_LEVEL as LogLevel) || 'info',
      enableConsole: process.env.ENABLE_CONSOLE_LOGGING !== 'false',
      enableCloudWatch: process.env.ENABLE_CLOUDWATCH_LOGGING === 'true',
      enableStructured: process.env.ENABLE_STRUCTURED_LOGGING !== 'false',
      serviceName: process.env.SERVICE_NAME || 'petplantr-backend',
      environment: process.env.ENVIRONMENT || 'development',
      ...config
    };
  }

  private shouldLog(level: LogLevel): boolean {
    return this.logLevels[level] >= this.logLevels[this.config.level];
  }

  private formatMessage(level: LogLevel, message: string, context?: Record<string, any>): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context
    };

    // Extract common fields from context
    if (context) {
      if (context.requestId) entry.requestId = context.requestId;
      if (context.userId) entry.userId = context.userId;
      if (context.orderId) entry.orderId = context.orderId;
      if (context.printerId) entry.printerId = context.printerId;
      if (context.error instanceof Error) entry.error = context.error;
    }

    return entry;
  }

  private output(entry: LogEntry): void {
    if (!this.shouldLog(entry.level)) return;

    if (this.config.enableConsole) {
      if (this.config.enableStructured) {
        console.log(JSON.stringify({
          ...entry,
          service: this.config.serviceName,
          environment: this.config.environment
        }));
      } else {
        const timestamp = entry.timestamp;
        const level = entry.level.toUpperCase().padEnd(5);
        const message = entry.message;
        const context = entry.context ? JSON.stringify(entry.context) : '';
        
        console.log(`[${timestamp}] ${level} ${message} ${context}`);
      }
    }

    // CloudWatch integration would go here
    if (this.config.enableCloudWatch) {
      // TODO: Implement CloudWatch logging
    }
  }

  debug(message: string, context?: Record<string, any>): void {
    const entry = this.formatMessage('debug', message, context);
    this.output(entry);
  }

  info(message: string, context?: Record<string, any>): void {
    const entry = this.formatMessage('info', message, context);
    this.output(entry);
  }

  warn(message: string, context?: Record<string, any>): void {
    const entry = this.formatMessage('warn', message, context);
    this.output(entry);
  }

  error(message: string, context?: Record<string, any>): void {
    const entry = this.formatMessage('error', message, context);
    this.output(entry);
  }

  fatal(message: string, context?: Record<string, any>): void {
    const entry = this.formatMessage('fatal', message, context);
    this.output(entry);
  }

  // Performance logging
  time(label: string): void {
    console.time(label);
  }

  timeEnd(label: string, context?: Record<string, any>): void {
    console.timeEnd(label);
    this.debug(`Timer completed: ${label}`, context);
  }

  // Request logging
  logRequest(method: string, path: string, context?: Record<string, any>): void {
    this.info(`${method} ${path}`, {
      type: 'request',
      method,
      path,
      ...context
    });
  }

  logResponse(method: string, path: string, statusCode: number, duration: number, context?: Record<string, any>): void {
    this.info(`${method} ${path} - ${statusCode} (${duration}ms)`, {
      type: 'response',
      method,
      path,
      statusCode,
      duration,
      ...context
    });
  }

  // Error logging with stack traces
  logError(error: Error, context?: Record<string, any>): void {
    this.error(error.message, {
      ...context,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      }
    });
  }

  // Business event logging
  logBusinessEvent(eventType: string, data: Record<string, any>): void {
    this.info(`Business Event: ${eventType}`, {
      type: 'business_event',
      eventType,
      data
    });
  }

  // Security event logging
  logSecurityEvent(eventType: string, severity: 'low' | 'medium' | 'high' | 'critical', data: Record<string, any>): void {
    this.warn(`Security Event: ${eventType}`, {
      type: 'security_event',
      eventType,
      severity,
      data
    });
  }

  // Performance metrics logging
  logMetrics(metrics: Record<string, number>, context?: Record<string, any>): void {
    this.info('Performance Metrics', {
      type: 'metrics',
      metrics,
      ...context
    });
  }
}

// Export singleton instance
export const logger = new Logger();

// Export class for custom instances
export { Logger };
