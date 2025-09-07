/**
 * Enhanced Logging System
 * Provides structured logging with multiple levels and destinations
 */

import winston from 'winston';

// Log levels
export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug'
}

// Log context interface
export interface LogContext {
  correlationId?: string;
  userId?: string;
  orderId?: string;
  functionName?: string;
  service?: string;
  timestamp?: string;
  [key: string]: any;
}

// Enhanced logger configuration
const logFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    return JSON.stringify({
      timestamp,
      level,
      message,
      service: 'petplantr-backend',
      environment: process.env.NODE_ENV || 'development',
      ...meta
    });
  })
);

// Create logger instance
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { 
    service: 'petplantr-backend',
    version: process.env.npm_package_version || '1.0.0'
  },
  transports: [
    // Console for all environments
    new winston.transports.Console({
      format: process.env.NODE_ENV === 'development' 
        ? winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        : logFormat
    })
  ]
});

// Enhanced logging methods
export class Logger {
  private context: LogContext;

  constructor(context: LogContext = {}) {
    this.context = {
      ...context,
      timestamp: new Date().toISOString()
    };
  }

  private log(level: LogLevel, message: string, meta: any = {}) {
    logger.log(level, message, {
      ...this.context,
      ...meta,
      timestamp: new Date().toISOString()
    });
  }

  error(message: string, error?: Error | any, meta: any = {}) {
    this.log(LogLevel.ERROR, message, {
      ...meta,
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } : error
    });
  }

  warn(message: string, meta: any = {}) {
    this.log(LogLevel.WARN, message, meta);
  }

  info(message: string, meta: any = {}) {
    this.log(LogLevel.INFO, message, meta);
  }

  debug(message: string, meta: any = {}) {
    this.log(LogLevel.DEBUG, message, meta);
  }

  // Performance logging
  performance(operation: string, duration: number, meta: any = {}) {
    this.info(`Performance: ${operation}`, {
      ...meta,
      operation,
      duration: `${duration}ms`,
      performanceMetric: true
    });
  }

  // Business event logging
  businessEvent(event: string, data: any = {}) {
    this.info(`Business Event: ${event}`, {
      ...data,
      eventType: event,
      businessEvent: true
    });
  }

  // Security event logging
  securityEvent(event: string, details: any = {}) {
    this.warn(`Security Event: ${event}`, {
      ...details,
      securityEvent: true,
      severity: 'HIGH'
    });
  }

  // Create child logger with additional context
  child(additionalContext: LogContext) {
    return new Logger({
      ...this.context,
      ...additionalContext
    });
  }
}

// Performance monitoring wrapper
export const withPerformanceLogging = <T extends any[], R>(
  operation: string,
  fn: (...args: T) => Promise<R>,
  logger: Logger
) => {
  return async (...args: T): Promise<R> => {
    const start = Date.now();
    try {
      const result = await fn(...args);
      const duration = Date.now() - start;
      logger.performance(operation, duration, { success: true });
      return result;
    } catch (error) {
      const duration = Date.now() - start;
      logger.performance(operation, duration, { success: false });
      logger.error(`${operation} failed`, error);
      throw error;
    }
  };
};

// Lambda function logger
export const createLambdaLogger = (
  functionName: string,
  correlationId?: string,
  userId?: string
) => {
  return new Logger({
    functionName,
    correlationId,
    userId,
    awsRegion: process.env.AWS_REGION,
    stage: process.env.STAGE || 'dev'
  });
};

// Export default logger instance
export default logger;
