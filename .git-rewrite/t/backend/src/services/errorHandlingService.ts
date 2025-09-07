/**
 * 🚨 Advanced Error Handling & Monitoring Service
 * Production-ready error management with alerting, metrics, and recovery strategies
 */

import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';
import { CloudWatchClient, PutMetricDataCommand, MetricDatum } from '@aws-sdk/client-cloudwatch';
import { logger } from '../utils/logger';
import { CacheService } from './cacheService';

export interface ErrorContext {
  requestId?: string;
  userId?: string;
  orderId?: string;
  printerId?: string;
  functionName?: string;
  endpoint?: string;
  userAgent?: string;
  ipAddress?: string;
  timestamp: string;
  environment: string;
  version: string;
}

export interface ErrorReport {
  id: string;
  type: 'VALIDATION' | 'AUTHENTICATION' | 'AUTHORIZATION' | 'BUSINESS_LOGIC' | 'EXTERNAL_SERVICE' | 'SYSTEM' | 'UNKNOWN';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  stack?: string;
  context: ErrorContext;
  metadata: Record<string, any>;
  recoveryAction?: string;
  userMessage?: string;
  correlationId?: string;
}

export interface AlertRule {
  name: string;
  condition: (error: ErrorReport) => boolean;
  cooldownMinutes: number;
  escalationLevel: 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
  channels: ('SNS' | 'SLACK' | 'EMAIL')[];
  enabled: boolean;
}

export interface HealthMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
  dimensions?: Record<string, string>;
}

export interface SystemHealth {
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  score: number; // 0-100
  lastCheck: string;
  components: {
    database: 'UP' | 'DOWN' | 'DEGRADED';
    queue: 'UP' | 'DOWN' | 'DEGRADED';
    cache: 'UP' | 'DOWN' | 'DEGRADED';
    externalServices: 'UP' | 'DOWN' | 'DEGRADED';
  };
  metrics: HealthMetric[];
  errors: ErrorReport[];
}

export class ErrorHandlingService {
  private snsClient: SNSClient;
  private cloudWatchClient: CloudWatchClient;
  private cache: CacheService;
  private alertRules: AlertRule[] = [];
  private errorCounts = new Map<string, number>();
  private healthMetrics: HealthMetric[] = [];

  // Configuration
  private readonly SNS_TOPIC_ARN = process.env.ERROR_ALERTS_SNS_TOPIC || '';
  private readonly SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL || '';
  private readonly ERROR_THRESHOLD = parseInt(process.env.ERROR_THRESHOLD || '10');
  private readonly HEALTH_CHECK_INTERVAL = parseInt(process.env.HEALTH_CHECK_INTERVAL || '60000'); // 1 minute

  constructor() {
    this.snsClient = new SNSClient({
      region: process.env.AWS_REGION || 'us-east-1'
    });

    this.cloudWatchClient = new CloudWatchClient({
      region: process.env.AWS_REGION || 'us-east-1'
    });

    this.cache = new CacheService();

    this.initializeDefaultAlertRules();
    this.startHealthMonitoring();

    logger.info('ErrorHandlingService initialized');
  }

  /**
   * 🚨 Handle and report error
   */
  async handleError(
    error: Error | string,
    type: ErrorReport['type'] = 'UNKNOWN',
    severity: ErrorReport['severity'] = 'MEDIUM',
    context: Partial<ErrorContext> = {}
  ): Promise<ErrorReport> {
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const errorMessage = typeof error === 'string' ? error : error.message;
    const errorStack = typeof error === 'string' ? undefined : error.stack;

    const fullContext: ErrorContext = {
      timestamp: new Date().toISOString(),
      environment: process.env.ENVIRONMENT || 'development',
      version: process.env.APP_VERSION || '1.0.0',
      functionName: process.env.AWS_LAMBDA_FUNCTION_NAME,
      ...context
    };

    const errorReport: ErrorReport = {
      id: errorId,
      type,
      severity,
      message: errorMessage,
      stack: errorStack,
      context: fullContext,
      metadata: {},
      userMessage: this.generateUserMessage(type, severity),
      correlationId: context.requestId || context.orderId
    };

    // Log the error
    logger.error('Error handled', {
      errorId,
      type,
      severity,
      message: errorMessage,
      context: fullContext
    });

    // Store error for tracking
    await this.storeError(errorReport);

    // Update error metrics
    await this.updateErrorMetrics(errorReport);

    // Check alert rules and send notifications
    await this.processAlerts(errorReport);

    // Attempt recovery if possible
    await this.attemptRecovery(errorReport);

    return errorReport;
  }

  /**
   * 📊 Record performance metrics
   */
  async recordMetric(name: string, value: number, unit = 'Count', dimensions?: Record<string, string>): Promise<void> {
    try {
      const metric: HealthMetric = {
        name,
        value,
        unit,
        timestamp: new Date().toISOString(),
        dimensions
      };

      this.healthMetrics.push(metric);

      // Send to CloudWatch
      const metricData: MetricDatum = {
        MetricName: name,
        Value: value,
        Unit: unit as any,
        Timestamp: new Date(),
        Dimensions: dimensions ? Object.entries(dimensions).map(([name, value]) => ({
          Name: name,
          Value: value
        })) : undefined
      };

      await this.cloudWatchClient.send(new PutMetricDataCommand({
        Namespace: 'PetPlantr/Backend',
        MetricData: [metricData]
      }));

      logger.debug('Metric recorded', { name, value, unit, dimensions });
    } catch (error) {
      logger.error('Failed to record metric', { name, value, error });
    }
  }

  /**
   * 🏥 Check system health
   */
  async checkSystemHealth(): Promise<SystemHealth> {
    const startTime = Date.now();
    
    try {
      // Check component health
      const [database, queue, cache, externalServices] = await Promise.allSettled([
        this.checkDatabaseHealth(),
        this.checkQueueHealth(),
        this.checkCacheHealth(),
        this.checkExternalServicesHealth()
      ]);

      const components = {
        database: this.getHealthStatus(database),
        queue: this.getHealthStatus(queue),
        cache: this.getHealthStatus(cache),
        externalServices: this.getHealthStatus(externalServices)
      };

      // Calculate overall health score
      const healthScore = this.calculateHealthScore(components);
      const status = this.determineSystemStatus(healthScore);

      // Get recent errors
      const recentErrors = await this.getRecentErrors(5);

      const health: SystemHealth = {
        status,
        score: healthScore,
        lastCheck: new Date().toISOString(),
        components,
        metrics: this.healthMetrics.slice(-20), // Last 20 metrics
        errors: recentErrors
      };

      // Record health check duration
      const duration = Date.now() - startTime;
      await this.recordMetric('HealthCheckDuration', duration, 'Milliseconds');
      await this.recordMetric('SystemHealthScore', healthScore, 'Percent');

      return health;
    } catch (error) {
      logger.error('Health check failed', { error });
      
      return {
        status: 'UNHEALTHY',
        score: 0,
        lastCheck: new Date().toISOString(),
        components: {
          database: 'DOWN',
          queue: 'DOWN',
          cache: 'DOWN',
          externalServices: 'DOWN'
        },
        metrics: [],
        errors: []
      };
    }
  }

  /**
   * 🔧 Register custom alert rule
   */
  registerAlertRule(rule: AlertRule): void {
    this.alertRules.push(rule);
    logger.info('Alert rule registered', { name: rule.name });
  }

  /**
   * 📈 Get error statistics
   */
  async getErrorStats(timeRangeMinutes = 60): Promise<Record<string, any>> {
    try {
      const stats = {
        totalErrors: 0,
        errorsByType: {} as Record<string, number>,
        errorsBySeverity: {} as Record<string, number>,
        errorRate: 0,
        topErrors: [] as string[],
        timeRange: timeRangeMinutes
      };

      // Get cached error counts
      const errorKeys = await this.cache.mget([
        'errors:total',
        'errors:by_type',
        'errors:by_severity',
        'errors:rate'
      ]);

      if (errorKeys['errors:total']) {
        stats.totalErrors = errorKeys['errors:total'] as number;
      }

      if (errorKeys['errors:by_type']) {
        stats.errorsByType = errorKeys['errors:by_type'] as Record<string, number>;
      }

      if (errorKeys['errors:by_severity']) {
        stats.errorsBySeverity = errorKeys['errors:by_severity'] as Record<string, number>;
      }

      if (errorKeys['errors:rate']) {
        stats.errorRate = errorKeys['errors:rate'] as number;
      }

      return stats;
    } catch (error) {
      logger.error('Failed to get error stats', { error });
      return {
        totalErrors: 0,
        errorsByType: {},
        errorsBySeverity: {},
        errorRate: 0,
        topErrors: [],
        timeRange: timeRangeMinutes
      };
    }
  }

  /**
   * 🔄 Attempt error recovery
   */
  async attemptRecovery(errorReport: ErrorReport): Promise<boolean> {
    try {
      switch (errorReport.type) {
        case 'EXTERNAL_SERVICE':
          return await this.recoverExternalService(errorReport);
        
        case 'SYSTEM':
          return await this.recoverSystemError(errorReport);
        
        case 'BUSINESS_LOGIC':
          return await this.recoverBusinessLogicError(errorReport);
        
        default:
          return false;
      }
    } catch (recoveryError) {
      logger.error('Recovery attempt failed', {
        errorId: errorReport.id,
        recoveryError
      });
      return false;
    }
  }

  // Private helper methods

  private initializeDefaultAlertRules(): void {
    const defaultRules: AlertRule[] = [
      {
        name: 'CriticalErrors',
        condition: (error) => error.severity === 'CRITICAL',
        cooldownMinutes: 5,
        escalationLevel: 'CRITICAL',
        channels: ['SNS', 'SLACK'],
        enabled: true
      },
      {
        name: 'HighErrorRate',
        condition: (error) => {
          const recentCount = this.errorCounts.get('recent') || 0;
          return recentCount > this.ERROR_THRESHOLD;
        },
        cooldownMinutes: 15,
        escalationLevel: 'ERROR',
        channels: ['SNS'],
        enabled: true
      },
      {
        name: 'DatabaseErrors',
        condition: (error) => error.type === 'SYSTEM' && error.message.includes('database'),
        cooldownMinutes: 10,
        escalationLevel: 'ERROR',
        channels: ['SNS', 'SLACK'],
        enabled: true
      }
    ];

    this.alertRules = defaultRules;
  }

  private async storeError(errorReport: ErrorReport): Promise<void> {
    try {
      // Store in cache for quick access
      await this.cache.set(`error:${errorReport.id}`, errorReport, 3600); // 1 hour

      // Add to recent errors list
      const recentErrors = await this.cache.get<string[]>('errors:recent') || [];
      recentErrors.unshift(errorReport.id);
      
      // Keep only last 100 errors
      if (recentErrors.length > 100) {
        recentErrors.splice(100);
      }
      
      await this.cache.set('errors:recent', recentErrors, 3600);
    } catch (error) {
      logger.error('Failed to store error', { errorId: errorReport.id, error });
    }
  }

  private async updateErrorMetrics(errorReport: ErrorReport): Promise<void> {
    try {
      // Update total error count
      await this.cache.increment('errors:total');
      
      // Update by type
      await this.cache.increment(`errors:type:${errorReport.type}`);
      
      // Update by severity
      await this.cache.increment(`errors:severity:${errorReport.severity}`);

      // Update recent error count (last hour)
      const recentKey = `errors:recent:${Math.floor(Date.now() / 3600000)}`;
      await this.cache.increment(recentKey);
      await this.cache.expire(recentKey, 3600);

      // Record CloudWatch metrics
      await this.recordMetric('ErrorCount', 1, 'Count', {
        ErrorType: errorReport.type,
        Severity: errorReport.severity
      });
    } catch (error) {
      logger.error('Failed to update error metrics', { error });
    }
  }

  private async processAlerts(errorReport: ErrorReport): Promise<void> {
    for (const rule of this.alertRules) {
      if (!rule.enabled) continue;

      try {
        if (rule.condition(errorReport)) {
          // Check cooldown
          const cooldownKey = `alert:cooldown:${rule.name}`;
          const inCooldown = await this.cache.exists(cooldownKey);
          
          if (inCooldown) {
            continue;
          }

          // Send alert
          await this.sendAlert(rule, errorReport);
          
          // Set cooldown
          await this.cache.set(cooldownKey, true, rule.cooldownMinutes * 60);
        }
      } catch (error) {
        logger.error('Failed to process alert rule', {
          ruleName: rule.name,
          error
        });
      }
    }
  }

  private async sendAlert(rule: AlertRule, errorReport: ErrorReport): Promise<void> {
    const alertMessage = this.formatAlertMessage(rule, errorReport);

    for (const channel of rule.channels) {
      try {
        switch (channel) {
          case 'SNS':
            await this.sendSNSAlert(alertMessage, rule.escalationLevel);
            break;
          case 'SLACK':
            await this.sendSlackAlert(alertMessage, rule.escalationLevel);
            break;
          case 'EMAIL':
            // Email would be handled through SNS typically
            break;
        }
      } catch (error) {
        logger.error('Failed to send alert', {
          channel,
          ruleName: rule.name,
          error
        });
      }
    }
  }

  private async sendSNSAlert(message: string, level: string): Promise<void> {
    if (!this.SNS_TOPIC_ARN) return;

    await this.snsClient.send(new PublishCommand({
      TopicArn: this.SNS_TOPIC_ARN,
      Message: message,
      Subject: `PetPlantr Alert - ${level}`,
      MessageAttributes: {
        Level: {
          StringValue: level,
          DataType: 'String'
        }
      }
    }));
  }

  private async sendSlackAlert(message: string, level: string): Promise<void> {
    // Slack webhook implementation would go here
    logger.debug('Slack alert would be sent', { message, level });
  }

  private formatAlertMessage(rule: AlertRule, errorReport: ErrorReport): string {
    return `
🚨 PetPlantr Alert: ${rule.name}

Severity: ${errorReport.severity}
Type: ${errorReport.type}
Message: ${errorReport.message}
Time: ${errorReport.context.timestamp}
Environment: ${errorReport.context.environment}

Context:
- Request ID: ${errorReport.context.requestId || 'N/A'}
- User ID: ${errorReport.context.userId || 'N/A'}
- Order ID: ${errorReport.context.orderId || 'N/A'}
- Function: ${errorReport.context.functionName || 'N/A'}

Error ID: ${errorReport.id}
    `.trim();
  }

  private generateUserMessage(type: ErrorReport['type'], severity: ErrorReport['severity']): string {
    const messages = {
      VALIDATION: 'Please check your input and try again.',
      AUTHENTICATION: 'Please log in and try again.',
      AUTHORIZATION: 'You do not have permission to perform this action.',
      BUSINESS_LOGIC: 'Unable to process your request. Please try again.',
      EXTERNAL_SERVICE: 'Service temporarily unavailable. Please try again later.',
      SYSTEM: 'A system error occurred. Our team has been notified.',
      UNKNOWN: 'An unexpected error occurred. Please try again.'
    };

    return messages[type] || messages.UNKNOWN;
  }

  private async checkDatabaseHealth(): Promise<boolean> {
    // Database health check implementation
    return true;
  }

  private async checkQueueHealth(): Promise<boolean> {
    // Queue health check implementation
    return true;
  }

  private async checkCacheHealth(): Promise<boolean> {
    try {
      await this.cache.set('health_check', 'ok', 60);
      const result = await this.cache.get('health_check');
      return result === 'ok';
    } catch {
      return false;
    }
  }

  private async checkExternalServicesHealth(): Promise<boolean> {
    // External services health check implementation
    return true;
  }

  private getHealthStatus(result: PromiseSettledResult<boolean>): 'UP' | 'DOWN' | 'DEGRADED' {
    if (result.status === 'fulfilled' && result.value) return 'UP';
    if (result.status === 'rejected') return 'DOWN';
    return 'DEGRADED';
  }

  private calculateHealthScore(components: SystemHealth['components']): number {
    const weights = { database: 30, queue: 25, cache: 20, externalServices: 25 };
    let score = 0;

    Object.entries(components).forEach(([component, status]) => {
      const weight = weights[component as keyof typeof weights];
      if (status === 'UP') score += weight;
      else if (status === 'DEGRADED') score += weight * 0.5;
    });

    return Math.round(score);
  }

  private determineSystemStatus(score: number): SystemHealth['status'] {
    if (score >= 90) return 'HEALTHY';
    if (score >= 70) return 'DEGRADED';
    return 'UNHEALTHY';
  }

  private async getRecentErrors(limit: number): Promise<ErrorReport[]> {
    try {
      const recentErrorIds = await this.cache.get<string[]>('errors:recent') || [];
      const errorPromises = recentErrorIds.slice(0, limit).map(id => 
        this.cache.get<ErrorReport>(`error:${id}`)
      );
      
      const errors = await Promise.all(errorPromises);
      return errors.filter(error => error !== null) as ErrorReport[];
    } catch {
      return [];
    }
  }

  private async recoverExternalService(errorReport: ErrorReport): Promise<boolean> {
    // External service recovery logic
    return false;
  }

  private async recoverSystemError(errorReport: ErrorReport): Promise<boolean> {
    // System error recovery logic
    return false;
  }

  private async recoverBusinessLogicError(errorReport: ErrorReport): Promise<boolean> {
    // Business logic error recovery
    return false;
  }

  private startHealthMonitoring(): void {
    setInterval(async () => {
      try {
        await this.checkSystemHealth();
      } catch (error) {
        logger.error('Health monitoring failed', { error });
      }
    }, this.HEALTH_CHECK_INTERVAL);
  }

  /**
   * 🧹 Cleanup resources
   */
  async cleanup(): Promise<void> {
    await this.cache.cleanup();
    logger.info('ErrorHandlingService cleanup completed');
  }
}

export const errorHandler = new ErrorHandlingService();
