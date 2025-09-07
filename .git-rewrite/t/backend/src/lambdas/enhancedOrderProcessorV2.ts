/**
 * 🚀 Enhanced Production Order Processor with Full Service Integration
 * Advanced Lambda function with database, queue, security, monitoring, and error handling
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { logger } from '../utils/logger';
import { databaseService, Order, PrintJob } from '../services/databaseService';
import { queueService, JobPayload } from '../services/queueService';
import { securityService, AuthContext } from '../services/securityService';
import { errorHandler, ErrorContext } from '../services/errorHandlingService';

interface CreateOrderRequest {
  customerId: string;
  photoUrls: string[];
  preferences?: {
    size?: 'small' | 'medium' | 'large';
    material?: 'PLA' | 'ABS' | 'PETG';
    color?: string;
    priority?: number;
  };
}

interface UpdateOrderRequest {
  status?: Order['status'];
  printerId?: string;
  metadata?: Record<string, any>;
}

/**
 * 📋 Enhanced Order Processing Handler
 */
export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const startTime = Date.now();
  const requestId = event.requestContext?.requestId || `req-${Date.now()}`;
  
  // Extract context information
  const ipAddress = event.requestContext?.identity?.sourceIp || 'unknown';
  const userAgent = event.headers?.['User-Agent'] || 'unknown';
  const method = event.httpMethod;
  const path = event.path;

  logger.logRequest(method, path, { requestId, ipAddress, userAgent });

  try {
    // Security checks
    const authHeader = event.headers?.Authorization || event.headers?.authorization;
    if (!authHeader) {
      return createResponse(401, { error: 'Authorization header required' });
    }

    const token = authHeader.replace('Bearer ', '');
    const user = await securityService.validateToken(token);
    if (!user) {
      return createResponse(401, { error: 'Invalid or expired token' });
    }

    // Check if IP is blocked
    const isBlocked = await securityService.isIPBlocked(ipAddress);
    if (isBlocked) {
      return createResponse(403, { error: 'Access denied' });
    }

    // Rate limiting
    const rateLimitKey = `${user.userId}:${ipAddress}`;
    const withinLimit = await securityService.checkRateLimit(rateLimitKey);
    if (!withinLimit) {
      return createResponse(429, { error: 'Rate limit exceeded' });
    }

    // Create auth context for threat detection
    const authContext: AuthContext = {
      user,
      ipAddress,
      userAgent,
      requestId,
      timestamp: new Date().toISOString()
    };

    // Threat detection
    const threatDetection = await securityService.detectThreats(authContext, event);
    if (threatDetection.suspiciousActivity) {
      return createResponse(403, { error: 'Suspicious activity detected' });
    }

    // Route to appropriate handler
    let result: APIGatewayProxyResult;
    
    switch (method) {
      case 'GET':
        result = await handleGetRequest(event, user);
        break;
      case 'POST':
        result = await handlePostRequest(event, user);
        break;
      case 'PUT':
        result = await handlePutRequest(event, user);
        break;
      case 'DELETE':
        result = await handleDeleteRequest(event, user);
        break;
      default:
        result = createResponse(405, { error: 'Method not allowed' });
    }

    // Log response
    const duration = Date.now() - startTime;
    logger.logResponse(method, path, result.statusCode, duration, { requestId });

    // Record metrics
    await errorHandler.recordMetric('RequestDuration', duration, 'Milliseconds', {
      Method: method,
      StatusCode: result.statusCode.toString()
    });

    return result;

  } catch (error) {
    const duration = Date.now() - startTime;
    
    // Handle the error using our error service
    const errorContext: ErrorContext = {
      requestId,
      ipAddress,
      userAgent,
      functionName: 'enhancedOrderProcessor',
      endpoint: `${method} ${path}`,
      timestamp: new Date().toISOString(),
      environment: process.env.ENVIRONMENT || 'development',
      version: process.env.APP_VERSION || '1.0.0'
    };

    const errorReport = await errorHandler.handleError(
      error as Error,
      'BUSINESS_LOGIC',
      'HIGH',
      errorContext
    );

    logger.logResponse(method, path, 500, duration, { requestId, errorId: errorReport.id });

    return createResponse(500, { 
      error: errorReport.userMessage,
      errorId: errorReport.id
    });
  }
};

/**
 * 📥 Handle GET requests
 */
async function handleGetRequest(event: APIGatewayProxyEvent, user: any): Promise<APIGatewayProxyResult> {
  const path = event.path;
  const pathSegments = path.split('/').filter(Boolean);

  if (pathSegments.includes('orders')) {
    const orderId = pathSegments[pathSegments.indexOf('orders') + 1];
    
    if (orderId) {
      // Get specific order
      const hasPermission = await securityService.authorize(user, 'read', 'orders');
      if (!hasPermission) {
        return createResponse(403, { error: 'Insufficient permissions' });
      }

      const order = await databaseService.getOrder(orderId);
      if (!order) {
        return createResponse(404, { error: 'Order not found' });
      }

      // Check if user can access this order
      if (user.role !== 'admin' && order.customerId !== user.userId) {
        return createResponse(403, { error: 'Access denied' });
      }

      return createResponse(200, { order });
    } else {
      // List orders
      const hasPermission = await securityService.authorize(user, 'list', 'orders');
      if (!hasPermission) {
        return createResponse(403, { error: 'Insufficient permissions' });
      }

      let orders: Order[];
      if (user.role === 'admin') {
        // Admin can see all orders - implement pagination in real scenario
        orders = []; // Would get all orders with pagination
      } else {
        orders = await databaseService.getOrdersByCustomer(user.userId);
      }

      return createResponse(200, { orders, count: orders.length });
    }
  }

  return createResponse(404, { error: 'Endpoint not found' });
}

/**
 * 📤 Handle POST requests
 */
async function handlePostRequest(event: APIGatewayProxyEvent, user: any): Promise<APIGatewayProxyResult> {
  const path = event.path;
  
  if (path.includes('/orders')) {
    // Create new order
    const hasPermission = await securityService.authorize(user, 'create', 'orders');
    if (!hasPermission) {
      return createResponse(403, { error: 'Insufficient permissions' });
    }

    if (!event.body) {
      return createResponse(400, { error: 'Request body required' });
    }

    const request: CreateOrderRequest = JSON.parse(event.body);
    
    // Validate request
    const validation = validateCreateOrderRequest(request);
    if (!validation.isValid) {
      return createResponse(400, { error: validation.error });
    }

    // Create order
    const orderId = `order-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const order: Omit<Order, 'createdAt' | 'updatedAt'> = {
      orderId,
      customerId: request.customerId,
      status: 'pending',
      photoUrls: request.photoUrls,
      metadata: {
        preferences: request.preferences || {},
        createdBy: user.userId,
        userAgent: event.headers?.['User-Agent'] || 'unknown'
      }
    };

    const createdOrder = await databaseService.createOrder(order);

    // Queue for processing
    const jobPayload: JobPayload = {
      type: 'ORDER_PROCESSING',
      orderId: createdOrder.orderId,
      customerId: createdOrder.customerId,
      data: {
        photoUrls: createdOrder.photoUrls,
        preferences: request.preferences
      },
      priority: request.preferences?.priority || 5
    };

    await queueService.enqueue(jobPayload);

    // Send notification
    await queueService.sendNotification(
      'ORDER_CREATED',
      createdOrder.customerId,
      {
        orderId: createdOrder.orderId,
        status: createdOrder.status
      }
    );

    logger.logBusinessEvent('OrderCreated', {
      orderId: createdOrder.orderId,
      customerId: createdOrder.customerId,
      photoCount: createdOrder.photoUrls.length
    });

    return createResponse(201, { order: createdOrder });
  }

  if (path.includes('/orders/complete-modeling')) {
    // Complete AI modeling step
    const hasPermission = await securityService.authorize(user, 'update', 'orders');
    if (!hasPermission) {
      return createResponse(403, { error: 'Insufficient permissions' });
    }

    if (!event.body) {
      return createResponse(400, { error: 'Request body required' });
    }

    const { orderId, stlFileUrl, breedPredictions } = JSON.parse(event.body);
    
    // Update order status
    await databaseService.updateOrderStatus(orderId, 'modeling', {
      stlFileUrl,
      breedPredictions,
      modelingCompletedAt: new Date().toISOString()
    });

    // Create print job
    const printJob: Omit<PrintJob, 'createdAt' | 'updatedAt'> = {
      jobId: `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      orderId,
      status: 'queued',
      priority: 5,
      estimatedDuration: 180, // 3 hours
      metadata: {
        stlFileUrl,
        breedPredictions
      }
    };

    await databaseService.createPrintJob(printJob);

    // Queue for printing
    const jobPayload: JobPayload = {
      type: 'PRINT_JOB',
      orderId,
      data: {
        jobId: printJob.jobId,
        stlFileUrl,
        breedPredictions
      },
      priority: printJob.priority
    };

    await queueService.enqueue(jobPayload);

    logger.logBusinessEvent('ModelingCompleted', {
      orderId,
      jobId: printJob.jobId
    });

    return createResponse(200, { 
      message: 'Modeling completed successfully',
      jobId: printJob.jobId
    });
  }

  return createResponse(404, { error: 'Endpoint not found' });
}

/**
 * 🔄 Handle PUT requests
 */
async function handlePutRequest(event: APIGatewayProxyEvent, user: any): Promise<APIGatewayProxyResult> {
  const path = event.path;
  const pathSegments = path.split('/').filter(Boolean);
  
  if (pathSegments.includes('orders')) {
    const orderId = pathSegments[pathSegments.indexOf('orders') + 1];
    
    if (!orderId) {
      return createResponse(400, { error: 'Order ID required' });
    }

    const hasPermission = await securityService.authorize(user, 'update', 'orders');
    if (!hasPermission) {
      return createResponse(403, { error: 'Insufficient permissions' });
    }

    if (!event.body) {
      return createResponse(400, { error: 'Request body required' });
    }

    const request: UpdateOrderRequest = JSON.parse(event.body);
    
    // Get existing order to check permissions
    const existingOrder = await databaseService.getOrder(orderId);
    if (!existingOrder) {
      return createResponse(404, { error: 'Order not found' });
    }

    // Check if user can update this order
    if (user.role !== 'admin' && existingOrder.customerId !== user.userId) {
      return createResponse(403, { error: 'Access denied' });
    }

    // Update order
    if (request.status) {
      await databaseService.updateOrderStatus(orderId, request.status, request.metadata);
    }

    const updatedOrder = await databaseService.getOrder(orderId);

    logger.logBusinessEvent('OrderUpdated', {
      orderId,
      status: request.status,
      updatedBy: user.userId
    });

    return createResponse(200, { order: updatedOrder });
  }

  return createResponse(404, { error: 'Endpoint not found' });
}

/**
 * 🗑️ Handle DELETE requests
 */
async function handleDeleteRequest(event: APIGatewayProxyEvent, user: any): Promise<APIGatewayProxyResult> {
  // Only admins can delete orders
  if (user.role !== 'admin') {
    return createResponse(403, { error: 'Admin access required' });
  }

  return createResponse(405, { error: 'Delete operations not implemented' });
}

/**
 * ✅ Validate create order request
 */
function validateCreateOrderRequest(request: CreateOrderRequest): { isValid: boolean; error?: string } {
  if (!request.customerId) {
    return { isValid: false, error: 'Customer ID is required' };
  }

  if (!request.photoUrls || request.photoUrls.length === 0) {
    return { isValid: false, error: 'At least one photo URL is required' };
  }

  if (request.photoUrls.length > 10) {
    return { isValid: false, error: 'Maximum 10 photos allowed' };
  }

  // Validate photo URLs
  for (const url of request.photoUrls) {
    if (!isValidUrl(url)) {
      return { isValid: false, error: `Invalid photo URL: ${url}` };
    }
  }

  // Validate preferences
  if (request.preferences) {
    const { size, material, priority } = request.preferences;
    
    if (size && !['small', 'medium', 'large'].includes(size)) {
      return { isValid: false, error: 'Invalid size preference' };
    }
    
    if (material && !['PLA', 'ABS', 'PETG'].includes(material)) {
      return { isValid: false, error: 'Invalid material preference' };
    }
    
    if (priority && (priority < 1 || priority > 10)) {
      return { isValid: false, error: 'Priority must be between 1 and 10' };
    }
  }

  return { isValid: true };
}

/**
 * 🔗 Validate URL format
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return url.startsWith('http://') || url.startsWith('https://');
  } catch {
    return false;
  }
}

/**
 * 📦 Create standardized API response
 */
function createResponse(statusCode: number, body: any): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'X-Response-Time': new Date().toISOString()
    },
    body: JSON.stringify({
      ...body,
      timestamp: new Date().toISOString()
    })
  };
}
