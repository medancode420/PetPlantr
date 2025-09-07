/**
 * 🎯 Advanced Queue Management System
 * Production-ready queue system with priority, retry logic, dead letter queues, and batch processing
 */

import { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand, GetQueueAttributesCommand } from '@aws-sdk/client-sqs';
import { logger } from '../utils/logger';
import { CacheService } from './cacheService';

export interface QueueConfig {
  region: string;
  queueUrl?: string;
  visibilityTimeout: number;
  maxReceiveCount: number;
  messageRetentionPeriod: number;
  delaySeconds: number;
}

export interface QueueMessage<T = any> {
  id: string;
  body: T;
  priority: number;
  retryCount: number;
  maxRetries: number;
  createdAt: string;
  scheduledFor?: string;
  metadata: Record<string, any>;
}

export interface JobPayload {
  type: 'ORDER_PROCESSING' | 'STL_GENERATION' | 'PRINT_JOB' | 'NOTIFICATION' | 'ANALYTICS';
  orderId?: string;
  printerId?: string;
  customerId?: string;
  data: Record<string, any>;
  priority: number;
  maxRetries?: number;
}

export interface QueueStats {
  totalMessages: number;
  visibleMessages: number;
  inFlightMessages: number;
  approximateAgeOfOldestMessage: number;
}

export type JobProcessor<T = any> = (message: QueueMessage<T>) => Promise<void>;

export class QueueService {
  private client: SQSClient;
  private cache: CacheService;
  private config: QueueConfig;
  private processors = new Map<string, JobProcessor>();
  private isProcessing = false;
  private processingInterval?: NodeJS.Timeout;

  // Queue URLs for different job types
  private readonly QUEUES = {
    HIGH_PRIORITY: process.env.HIGH_PRIORITY_QUEUE_URL || '',
    NORMAL_PRIORITY: process.env.NORMAL_PRIORITY_QUEUE_URL || '',
    LOW_PRIORITY: process.env.LOW_PRIORITY_QUEUE_URL || '',
    DEAD_LETTER: process.env.DEAD_LETTER_QUEUE_URL || '',
    NOTIFICATIONS: process.env.NOTIFICATIONS_QUEUE_URL || ''
  };

  constructor(config?: Partial<QueueConfig>) {
    this.config = {
      region: process.env.AWS_REGION || 'us-east-1',
      visibilityTimeout: 300, // 5 minutes
      maxReceiveCount: 3,
      messageRetentionPeriod: 1209600, // 14 days
      delaySeconds: 0,
      ...config
    };

    this.client = new SQSClient({
      region: this.config.region
    });

    this.cache = new CacheService();

    logger.info('QueueService initialized', {
      region: this.config.region,
      queues: Object.keys(this.QUEUES)
    });
  }

  /**
   * 📤 Send message to appropriate queue based on priority
   */
  async enqueue<T>(payload: JobPayload, delaySeconds = 0): Promise<string> {
    try {
      const message: QueueMessage<T> = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        body: payload as T,
        priority: payload.priority,
        retryCount: 0,
        maxRetries: payload.maxRetries || 3,
        createdAt: new Date().toISOString(),
        scheduledFor: delaySeconds > 0 ? new Date(Date.now() + delaySeconds * 1000).toISOString() : undefined,
        metadata: {
          source: 'petplantr-backend',
          environment: process.env.ENVIRONMENT || 'development'
        }
      };

      // Select queue based on priority
      const queueUrl = this.selectQueue(payload.priority);
      
      const command = new SendMessageCommand({
        QueueUrl: queueUrl,
        MessageBody: JSON.stringify(message),
        DelaySeconds: delaySeconds,
        MessageAttributes: {
          JobType: {
            StringValue: payload.type,
            DataType: 'String'
          },
          Priority: {
            StringValue: payload.priority.toString(),
            DataType: 'Number'
          },
          OrderId: {
            StringValue: payload.orderId || 'none',
            DataType: 'String'
          }
        }
      });

      const result = await this.client.send(command);
      
      logger.info('Message enqueued successfully', {
        messageId: result.MessageId,
        queueUrl,
        jobType: payload.type,
        priority: payload.priority,
        delaySeconds
      });

      // Update queue metrics in cache
      await this.updateQueueMetrics(queueUrl, 'enqueued');

      return result.MessageId || message.id;
    } catch (error) {
      logger.error('Failed to enqueue message', {
        payload,
        error
      });
      throw new Error(`Failed to enqueue message: ${error}`);
    }
  }

  /**
   * 📥 Receive and process messages from queue
   */
  async dequeue(queueUrl: string, maxMessages = 1): Promise<QueueMessage[]> {
    try {
      const command = new ReceiveMessageCommand({
        QueueUrl: queueUrl,
        MaxNumberOfMessages: Math.min(maxMessages, 10),
        VisibilityTimeout: this.config.visibilityTimeout,
        WaitTimeSeconds: 20, // Long polling
        MessageAttributeNames: ['All']
      });

      const result = await this.client.send(command);
      const messages = result.Messages || [];

      const queueMessages: QueueMessage[] = [];
      for (const sqsMessage of messages) {
        try {
          const message: QueueMessage = JSON.parse(sqsMessage.Body || '{}');
          message.metadata.receiptHandle = sqsMessage.ReceiptHandle;
          message.metadata.sqsMessageId = sqsMessage.MessageId;
          queueMessages.push(message);
        } catch (parseError) {
          logger.error('Failed to parse queue message', {
            messageId: sqsMessage.MessageId,
            error: parseError
          });
        }
      }

      if (queueMessages.length > 0) {
        logger.debug('Messages dequeued', {
          queueUrl,
          count: queueMessages.length
        });

        await this.updateQueueMetrics(queueUrl, 'dequeued', queueMessages.length);
      }

      return queueMessages;
    } catch (error) {
      logger.error('Failed to dequeue messages', {
        queueUrl,
        error
      });
      return [];
    }
  }

  /**
   * ✅ Acknowledge message processing (delete from queue)
   */
  async ack(queueUrl: string, message: QueueMessage): Promise<void> {
    try {
      const receiptHandle = message.metadata.receiptHandle;
      if (!receiptHandle) {
        throw new Error('No receipt handle found for message');
      }

      await this.client.send(new DeleteMessageCommand({
        QueueUrl: queueUrl,
        ReceiptHandle: receiptHandle
      }));

      logger.debug('Message acknowledged', {
        messageId: message.id,
        queueUrl
      });

      await this.updateQueueMetrics(queueUrl, 'acknowledged');
    } catch (error) {
      logger.error('Failed to acknowledge message', {
        messageId: message.id,
        queueUrl,
        error
      });
      throw error;
    }
  }

  /**
   * ❌ Move message to dead letter queue
   */
  async moveToDeadLetter(message: QueueMessage, reason: string): Promise<void> {
    try {
      // Add failure information
      message.metadata.failureReason = reason;
      message.metadata.failedAt = new Date().toISOString();
      message.metadata.originalQueue = message.metadata.queueUrl;

      await this.client.send(new SendMessageCommand({
        QueueUrl: this.QUEUES.DEAD_LETTER,
        MessageBody: JSON.stringify(message),
        MessageAttributes: {
          FailureReason: {
            StringValue: reason,
            DataType: 'String'
          },
          OriginalMessageId: {
            StringValue: message.id,
            DataType: 'String'
          }
        }
      }));

      logger.warn('Message moved to dead letter queue', {
        messageId: message.id,
        reason,
        retryCount: message.retryCount
      });

      await this.updateQueueMetrics(this.QUEUES.DEAD_LETTER, 'dead_letter');
    } catch (error) {
      logger.error('Failed to move message to dead letter queue', {
        messageId: message.id,
        reason,
        error
      });
    }
  }

  /**
   * 🔄 Retry failed message with exponential backoff
   */
  async retryMessage(message: QueueMessage, error: string): Promise<void> {
    message.retryCount++;
    
    if (message.retryCount >= message.maxRetries) {
      await this.moveToDeadLetter(message, `Max retries exceeded: ${error}`);
      return;
    }

    // Exponential backoff: 2^retryCount minutes
    const delaySeconds = Math.min(Math.pow(2, message.retryCount) * 60, 900); // Max 15 minutes
    
    message.metadata.lastError = error;
    message.metadata.lastRetryAt = new Date().toISOString();

    const queueUrl = this.selectQueue(message.priority);
    
    await this.client.send(new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: JSON.stringify(message),
      DelaySeconds: delaySeconds,
      MessageAttributes: {
        RetryCount: {
          StringValue: message.retryCount.toString(),
          DataType: 'Number'
        },
        IsRetry: {
          StringValue: 'true',
          DataType: 'String'
        }
      }
    }));

    logger.info('Message scheduled for retry', {
      messageId: message.id,
      retryCount: message.retryCount,
      delaySeconds,
      error
    });
  }

  /**
   * 📊 Get queue statistics
   */
  async getQueueStats(queueUrl: string): Promise<QueueStats> {
    try {
      const command = new GetQueueAttributesCommand({
        QueueUrl: queueUrl,
        AttributeNames: [
          'ApproximateNumberOfMessages',
          'ApproximateNumberOfMessagesNotVisible'
        ]
      });

      const result = await this.client.send(command);
      const attributes = result.Attributes || {};

      return {
        totalMessages: parseInt(attributes.ApproximateNumberOfMessages || '0'),
        visibleMessages: parseInt(attributes.ApproximateNumberOfMessages || '0'),
        inFlightMessages: parseInt(attributes.ApproximateNumberOfMessagesNotVisible || '0'),
        approximateAgeOfOldestMessage: 0 // Simplified since this attribute isn't available in all regions
      };
    } catch (error) {
      logger.error('Failed to get queue stats', { queueUrl, error });
      return {
        totalMessages: 0,
        visibleMessages: 0,
        inFlightMessages: 0,
        approximateAgeOfOldestMessage: 0
      };
    }
  }

  /**
   * 🔧 Register job processor for specific job type
   */
  registerProcessor<T>(jobType: string, processor: JobProcessor<T>): void {
    this.processors.set(jobType, processor);
    logger.info('Job processor registered', { jobType });
  }

  /**
   * 🚀 Start processing queues
   */
  async startProcessing(intervalMs = 5000): Promise<void> {
    if (this.isProcessing) {
      logger.warn('Queue processing already started');
      return;
    }

    this.isProcessing = true;
    logger.info('Starting queue processing', { intervalMs });

    this.processingInterval = setInterval(async () => {
      await this.processAllQueues();
    }, intervalMs);

    // Initial processing
    await this.processAllQueues();
  }

  /**
   * 🛑 Stop processing queues
   */
  stopProcessing(): void {
    if (this.processingInterval) {
      clearInterval(this.processingInterval);
      this.processingInterval = undefined;
    }
    
    this.isProcessing = false;
    logger.info('Queue processing stopped');
  }

  /**
   * 📬 Send notification to notification queue
   */
  async sendNotification(type: string, recipient: string, data: any): Promise<void> {
    const payload: JobPayload = {
      type: 'NOTIFICATION',
      customerId: recipient,
      data: {
        notificationType: type,
        recipient,
        ...data
      },
      priority: 5 // Medium priority for notifications
    };

    await this.enqueue(payload);
  }

  /**
   * 🎯 Bulk operations
   */
  async enqueueBatch<T>(payloads: JobPayload[]): Promise<string[]> {
    const results = await Promise.allSettled(
      payloads.map(payload => this.enqueue<T>(payload))
    );

    const messageIds: string[] = [];
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        messageIds.push(result.value);
      } else {
        logger.error('Failed to enqueue batch message', {
          index,
          payload: payloads[index],
          error: result.reason
        });
      }
    });

    return messageIds;
  }

  // Private helper methods

  private selectQueue(priority: number): string {
    if (priority >= 8) return this.QUEUES.HIGH_PRIORITY;
    if (priority >= 5) return this.QUEUES.NORMAL_PRIORITY;
    return this.QUEUES.LOW_PRIORITY;
  }

  private async processAllQueues(): Promise<void> {
    const queueUrls = [
      this.QUEUES.HIGH_PRIORITY,
      this.QUEUES.NORMAL_PRIORITY,
      this.QUEUES.LOW_PRIORITY
    ].filter(url => url); // Only process configured queues

    await Promise.all(
      queueUrls.map(queueUrl => this.processQueue(queueUrl))
    );
  }

  private async processQueue(queueUrl: string): Promise<void> {
    try {
      const messages = await this.dequeue(queueUrl, 5); // Process up to 5 messages at once
      
      await Promise.all(
        messages.map(message => this.processMessage(queueUrl, message))
      );
    } catch (error) {
      logger.error('Error processing queue', { queueUrl, error });
    }
  }

  private async processMessage(queueUrl: string, message: QueueMessage): Promise<void> {
    const jobType = message.body.type;
    const processor = this.processors.get(jobType);

    if (!processor) {
      logger.warn('No processor found for job type', { 
        jobType, 
        messageId: message.id 
      });
      await this.ack(queueUrl, message);
      return;
    }

    try {
      logger.debug('Processing message', {
        messageId: message.id,
        jobType,
        retryCount: message.retryCount
      });

      await processor(message);
      await this.ack(queueUrl, message);

      logger.info('Message processed successfully', {
        messageId: message.id,
        jobType
      });
    } catch (error) {
      logger.error('Message processing failed', {
        messageId: message.id,
        jobType,
        error
      });

      await this.retryMessage(message, String(error));
    }
  }

  private async updateQueueMetrics(queueUrl: string, operation: string, count = 1): Promise<void> {
    try {
      const key = `queue_metrics:${queueUrl}:${operation}`;
      await this.cache.increment(key, count);
    } catch (error) {
      // Don't fail the main operation for metrics
      logger.debug('Failed to update queue metrics', { queueUrl, operation, error });
    }
  }

  /**
   * 🧹 Cleanup resources
   */
  async cleanup(): Promise<void> {
    this.stopProcessing();
    await this.cache.cleanup();
    logger.info('QueueService cleanup completed');
  }
}

export const queueService = new QueueService();
