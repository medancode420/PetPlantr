/**
 * 🗄️ Database Service Layer
 * Production-ready database integration with DynamoDB
 * Handles all database operations with error handling, retries, and caching
 */

import { DynamoDBClient, DynamoDBClientConfig } from '@aws-sdk/client-dynamodb';
import {
  DynamoDBDocumentClient,
  GetCommand,
  PutCommand,
  UpdateCommand,
  DeleteCommand,
  QueryCommand,
  ScanCommand,
  BatchGetCommand,
  BatchWriteCommand,
  TransactWriteCommand
} from '@aws-sdk/lib-dynamodb';
import { logger } from '../utils/logger';
import { CacheService } from './cacheService';

export interface DatabaseConfig {
  region: string;
  endpoint?: string;
  maxRetries: number;
  timeout: number;
}

export interface Order {
  orderId: string;
  customerId: string;
  status: 'pending' | 'processing' | 'modeling' | 'printing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
  photoUrls: string[];
  breedPredictions?: any;
  stlFileUrl?: string;
  printerId?: string;
  farmId?: string;
  metadata: Record<string, any>;
}

export interface Printer {
  printerId: string;
  name: string;
  status: 'idle' | 'printing' | 'maintenance' | 'offline';
  farmId: string;
  capabilities: {
    materials: string[];
    maxSize: { x: number; y: number; z: number };
    resolution: number;
  };
  performance: {
    successRate: number;
    avgPrintTime: number;
    totalJobs: number;
  };
  currentJob?: string;
  lastMaintenance: string;
  createdAt: string;
  updatedAt: string;
}

export interface PrintJob {
  jobId: string;
  orderId: string;
  printerId?: string;
  status: 'queued' | 'assigned' | 'printing' | 'completed' | 'failed';
  priority: number;
  estimatedDuration: number;
  actualDuration?: number;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}

export class DatabaseService {
  private client: DynamoDBDocumentClient;
  private cache: CacheService;
  private config: DatabaseConfig;

  // Table names
  private readonly ORDERS_TABLE = process.env.ORDERS_TABLE || 'petplantr-orders';
  private readonly PRINTERS_TABLE = process.env.PRINTERS_TABLE || 'petplantr-printers';
  private readonly JOBS_TABLE = process.env.JOBS_TABLE || 'petplantr-jobs';
  private readonly ANALYTICS_TABLE = process.env.ANALYTICS_TABLE || 'petplantr-analytics';

  constructor(config?: Partial<DatabaseConfig>) {
    this.config = {
      region: process.env.AWS_REGION || 'us-east-1',
      maxRetries: 3,
      timeout: 5000,
      ...config
    };

    const clientConfig: DynamoDBClientConfig = {
      region: this.config.region,
      maxAttempts: this.config.maxRetries
    };

    if (this.config.endpoint) {
      clientConfig.endpoint = this.config.endpoint;
    }

    const dynamoClient = new DynamoDBClient(clientConfig);
    this.client = DynamoDBDocumentClient.from(dynamoClient);
    this.cache = new CacheService();

    logger.info('DatabaseService initialized', { 
      region: this.config.region,
      endpoint: this.config.endpoint 
    });
  }

  // 📝 Order Operations
  async createOrder(order: Omit<Order, 'createdAt' | 'updatedAt'>): Promise<Order> {
    const now = new Date().toISOString();
    const fullOrder: Order = {
      ...order,
      createdAt: now,
      updatedAt: now
    };

    try {
      await this.client.send(new PutCommand({
        TableName: this.ORDERS_TABLE,
        Item: fullOrder,
        ConditionExpression: 'attribute_not_exists(orderId)'
      }));

      // Invalidate related cache
      await this.cache.delete(`orders:${order.customerId}`);
      
      logger.info('Order created successfully', { orderId: order.orderId });
      return fullOrder;
    } catch (error) {
      logger.error('Failed to create order', { orderId: order.orderId, error });
      throw new Error(`Failed to create order: ${error}`);
    }
  }

  async getOrder(orderId: string): Promise<Order | null> {
    // Check cache first
    const cacheKey = `order:${orderId}`;
    const cached = await this.cache.get<Order>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const result = await this.client.send(new GetCommand({
        TableName: this.ORDERS_TABLE,
        Key: { orderId }
      }));

      if (!result.Item) {
        return null;
      }

      const order = result.Item as Order;
      // Cache for 5 minutes
      await this.cache.set(cacheKey, order, 300);
      
      return order;
    } catch (error) {
      logger.error('Failed to get order', { orderId, error });
      throw new Error(`Failed to get order: ${error}`);
    }
  }

  async updateOrderStatus(orderId: string, status: Order['status'], metadata?: Record<string, any>): Promise<void> {
    const now = new Date().toISOString();
    
    try {
      const updateExpression = 'SET #status = :status, updatedAt = :updatedAt';
      const expressionAttributeNames = { '#status': 'status' };
      const expressionAttributeValues: Record<string, any> = {
        ':status': status,
        ':updatedAt': now
      };

      if (metadata) {
        Object.entries(metadata).forEach(([key, value], index) => {
          const attrName = `#meta${index}`;
          const attrValue = `:meta${index}`;
          updateExpression.concat(`, metadata.${attrName} = ${attrValue}`);
          (expressionAttributeNames as any)[attrName] = key;
          expressionAttributeValues[attrValue] = value;
        });
      }

      await this.client.send(new UpdateCommand({
        TableName: this.ORDERS_TABLE,
        Key: { orderId },
        UpdateExpression: updateExpression,
        ExpressionAttributeNames: expressionAttributeNames,
        ExpressionAttributeValues: expressionAttributeValues,
        ConditionExpression: 'attribute_exists(orderId)'
      }));

      // Invalidate cache
      await this.cache.delete(`order:${orderId}`);
      
      logger.info('Order status updated', { orderId, status });
    } catch (error) {
      logger.error('Failed to update order status', { orderId, status, error });
      throw new Error(`Failed to update order status: ${error}`);
    }
  }

  async getOrdersByCustomer(customerId: string, limit = 50): Promise<Order[]> {
    const cacheKey = `orders:${customerId}`;
    const cached = await this.cache.get<Order[]>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const result = await this.client.send(new QueryCommand({
        TableName: this.ORDERS_TABLE,
        IndexName: 'CustomerIndex',
        KeyConditionExpression: 'customerId = :customerId',
        ExpressionAttributeValues: {
          ':customerId': customerId
        },
        Limit: limit,
        ScanIndexForward: false // Most recent first
      }));

      const orders = (result.Items || []) as Order[];
      // Cache for 2 minutes
      await this.cache.set(cacheKey, orders, 120);
      
      return orders;
    } catch (error) {
      logger.error('Failed to get orders by customer', { customerId, error });
      throw new Error(`Failed to get orders by customer: ${error}`);
    }
  }

  // 🖨️ Printer Operations
  async createPrinter(printer: Omit<Printer, 'createdAt' | 'updatedAt'>): Promise<Printer> {
    const now = new Date().toISOString();
    const fullPrinter: Printer = {
      ...printer,
      createdAt: now,
      updatedAt: now
    };

    try {
      await this.client.send(new PutCommand({
        TableName: this.PRINTERS_TABLE,
        Item: fullPrinter,
        ConditionExpression: 'attribute_not_exists(printerId)'
      }));

      // Invalidate farm cache
      await this.cache.delete(`farm:${printer.farmId}:printers`);
      
      logger.info('Printer created successfully', { printerId: printer.printerId });
      return fullPrinter;
    } catch (error) {
      logger.error('Failed to create printer', { printerId: printer.printerId, error });
      throw new Error(`Failed to create printer: ${error}`);
    }
  }

  async getPrinter(printerId: string): Promise<Printer | null> {
    const cacheKey = `printer:${printerId}`;
    const cached = await this.cache.get<Printer>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const result = await this.client.send(new GetCommand({
        TableName: this.PRINTERS_TABLE,
        Key: { printerId }
      }));

      if (!result.Item) {
        return null;
      }

      const printer = result.Item as Printer;
      await this.cache.set(cacheKey, printer, 300);
      
      return printer;
    } catch (error) {
      logger.error('Failed to get printer', { printerId, error });
      throw new Error(`Failed to get printer: ${error}`);
    }
  }

  async getPrintersByFarm(farmId: string): Promise<Printer[]> {
    const cacheKey = `farm:${farmId}:printers`;
    const cached = await this.cache.get<Printer[]>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const result = await this.client.send(new QueryCommand({
        TableName: this.PRINTERS_TABLE,
        IndexName: 'FarmIndex',
        KeyConditionExpression: 'farmId = :farmId',
        ExpressionAttributeValues: {
          ':farmId': farmId
        }
      }));

      const printers = (result.Items || []) as Printer[];
      await this.cache.set(cacheKey, printers, 180);
      
      return printers;
    } catch (error) {
      logger.error('Failed to get printers by farm', { farmId, error });
      throw new Error(`Failed to get printers by farm: ${error}`);
    }
  }

  async updatePrinterStatus(printerId: string, status: Printer['status'], currentJob?: string): Promise<void> {
    const now = new Date().toISOString();
    
    try {
      const updateExpression = 'SET #status = :status, updatedAt = :updatedAt';
      const expressionAttributeNames = { '#status': 'status' };
      const expressionAttributeValues: Record<string, any> = {
        ':status': status,
        ':updatedAt': now
      };

      if (currentJob !== undefined) {
        updateExpression.concat(', currentJob = :currentJob');
        expressionAttributeValues[':currentJob'] = currentJob;
      }

      await this.client.send(new UpdateCommand({
        TableName: this.PRINTERS_TABLE,
        Key: { printerId },
        UpdateExpression: updateExpression,
        ExpressionAttributeNames: expressionAttributeNames,
        ExpressionAttributeValues: expressionAttributeValues,
        ConditionExpression: 'attribute_exists(printerId)'
      }));

      // Invalidate related caches
      const printer = await this.getPrinter(printerId);
      if (printer) {
        await Promise.all([
          this.cache.delete(`printer:${printerId}`),
          this.cache.delete(`farm:${printer.farmId}:printers`)
        ]);
      }
      
      logger.info('Printer status updated', { printerId, status, currentJob });
    } catch (error) {
      logger.error('Failed to update printer status', { printerId, status, error });
      throw new Error(`Failed to update printer status: ${error}`);
    }
  }

  // 🎯 Job Operations
  async createPrintJob(job: Omit<PrintJob, 'createdAt' | 'updatedAt'>): Promise<PrintJob> {
    const now = new Date().toISOString();
    const fullJob: PrintJob = {
      ...job,
      createdAt: now,
      updatedAt: now
    };

    try {
      await this.client.send(new PutCommand({
        TableName: this.JOBS_TABLE,
        Item: fullJob,
        ConditionExpression: 'attribute_not_exists(jobId)'
      }));

      // Invalidate queue cache
      await this.cache.delete('jobs:queue');
      
      logger.info('Print job created successfully', { jobId: job.jobId });
      return fullJob;
    } catch (error) {
      logger.error('Failed to create print job', { jobId: job.jobId, error });
      throw new Error(`Failed to create print job: ${error}`);
    }
  }

  async getQueuedJobs(limit = 100): Promise<PrintJob[]> {
    const cacheKey = 'jobs:queue';
    const cached = await this.cache.get<PrintJob[]>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const result = await this.client.send(new QueryCommand({
        TableName: this.JOBS_TABLE,
        IndexName: 'StatusIndex',
        KeyConditionExpression: '#status = :status',
        ExpressionAttributeNames: { '#status': 'status' },
        ExpressionAttributeValues: {
          ':status': 'queued'
        },
        Limit: limit,
        ScanIndexForward: true // Oldest first (FIFO)
      }));

      const jobs = (result.Items || []) as PrintJob[];
      await this.cache.set(cacheKey, jobs, 30); // Short cache for queue
      
      return jobs;
    } catch (error) {
      logger.error('Failed to get queued jobs', { error });
      throw new Error(`Failed to get queued jobs: ${error}`);
    }
  }

  // 📊 Analytics Operations
  async recordAnalytics(eventType: string, data: Record<string, any>): Promise<void> {
    const analyticsRecord = {
      recordId: `${eventType}-${Date.now()}-${Math.random()}`,
      eventType,
      timestamp: new Date().toISOString(),
      data
    };

    try {
      await this.client.send(new PutCommand({
        TableName: this.ANALYTICS_TABLE,
        Item: analyticsRecord
      }));

      logger.debug('Analytics recorded', { eventType, recordId: analyticsRecord.recordId });
    } catch (error) {
      logger.error('Failed to record analytics', { eventType, error });
      // Don't throw - analytics failures shouldn't break the main flow
    }
  }

  // 🔄 Transaction Operations
  async assignJobToPrinter(jobId: string, printerId: string): Promise<void> {
    const now = new Date().toISOString();

    try {
      await this.client.send(new TransactWriteCommand({
        TransactItems: [
          {
            Update: {
              TableName: this.JOBS_TABLE,
              Key: { jobId },
              UpdateExpression: 'SET #status = :assigned, printerId = :printerId, updatedAt = :updatedAt',
              ExpressionAttributeNames: { '#status': 'status' },
              ExpressionAttributeValues: {
                ':assigned': 'assigned',
                ':printerId': printerId,
                ':updatedAt': now
              },
              ConditionExpression: '#status = :queued'
            }
          },
          {
            Update: {
              TableName: this.PRINTERS_TABLE,
              Key: { printerId },
              UpdateExpression: 'SET #status = :printing, currentJob = :jobId, updatedAt = :updatedAt',
              ExpressionAttributeNames: { '#status': 'status' },
              ExpressionAttributeValues: {
                ':printing': 'printing',
                ':jobId': jobId,
                ':updatedAt': now
              },
              ConditionExpression: '#status = :idle'
            }
          }
        ]
      }));

      // Invalidate caches
      await Promise.all([
        this.cache.delete(`job:${jobId}`),
        this.cache.delete(`printer:${printerId}`),
        this.cache.delete('jobs:queue')
      ]);

      logger.info('Job assigned to printer', { jobId, printerId });
    } catch (error) {
      logger.error('Failed to assign job to printer', { jobId, printerId, error });
      throw new Error(`Failed to assign job to printer: ${error}`);
    }
  }

  // 🧹 Cleanup and Maintenance
  async cleanup(): Promise<void> {
    await this.cache.cleanup();
    logger.info('DatabaseService cleanup completed');
  }
}

export const databaseService = new DatabaseService();
