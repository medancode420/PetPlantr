/**
 * 🎨 Frontend Integration Service
 * Optimized API endpoints and real-time updates for frontend consumption
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, ScanCommand, GetCommand, PutCommand, UpdateCommand } from '@aws-sdk/lib-dynamodb';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import { logger } from '../utils/logger';

// Frontend-optimized data structures
interface FrontendOrder {
  id: string;
  customerId: string;
  customerEmail: string;
  petName: string;
  breed?: string;
  status: 'pending' | 'processing' | 'modeling' | 'printing' | 'completed' | 'failed';
  progress: {
    current: number;
    total: number;
    percentage: number;
    stage: string;
    estimatedCompletion?: string;
  };
  photos: {
    urls: string[];
    thumbnails: string[];
    count: number;
  };
  planter: {
    stlUrl?: string;
    previewUrl?: string;
    size: 'small' | 'medium' | 'large';
    material: 'PLA' | 'ABS' | 'PETG';
    color: string;
    quality: 'standard' | 'high' | 'premium';
  };
  pricing: {
    basePrice: number;
    materialCost: number;
    qualityUpgrade: number;
    total: number;
    currency: 'USD';
  };
  timeline: {
    ordered: string;
    aiProcessingStarted?: string;
    aiProcessingCompleted?: string;
    printingStarted?: string;
    printingCompleted?: string;
    shipped?: string;
    delivered?: string;
  };
  printer?: {
    id: string;
    name: string;
    status: string;
    progress: number;
  };
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
  metadata: {
    source: string;
    userAgent: string;
    ipAddress: string;
    createdAt: string;
    updatedAt: string;
  };
}

interface FrontendDashboard {
  user: {
    id: string;
    email: string;
    name: string;
    totalOrders: number;
    memberSince: string;
  };
  currentOrders: FrontendOrder[];
  recentActivity: Array<{
    id: string;
    type: 'order_created' | 'ai_completed' | 'printing_started' | 'order_completed';
    message: string;
    timestamp: string;
    orderId?: string;
  }>;
  statistics: {
    totalOrders: number;
    completedOrders: number;
    successRate: number;
    averageProcessingTime: string;
    favoriteBreed?: string;
  };
  farmStatus: {
    queuePosition?: number;
    estimatedWaitTime?: string;
    activePrinters: number;
    totalCapacity: number;
    utilizationRate: number;
  };
  recommendations: Array<{
    type: 'breed_suggestion' | 'material_upgrade' | 'size_optimization';
    title: string;
    description: string;
    actionUrl?: string;
  }>;
}

interface FrontendPrinterStatus {
  id: string;
  name: string;
  model: string;
  status: 'idle' | 'printing' | 'paused' | 'error' | 'offline' | 'maintenance';
  currentJob?: {
    id: string;
    customerName: string;
    petName: string;
    breed: string;
    progress: number;
    estimatedCompletion: string;
    timeRemaining: string;
  };
  capabilities: {
    materials: string[];
    maxSize: { x: number; y: number; z: number };
    quality: string[];
    speed: string;
  };
  statistics: {
    totalJobsCompleted: number;
    successRate: number;
    averageQuality: number;
    totalPrintTime: string;
    lastMaintenance: string;
  };
  realtime: {
    temperatureBed: number;
    temperatureNozzle: number;
    progress: number;
    layerCurrent: number;
    layerTotal: number;
    materialRemaining: number;
  };
}

interface WebSocketMessage {
  type: 'order_update' | 'printer_update' | 'farm_status' | 'notification';
  userId?: string;
  orderId?: string;
  printerId?: string;
  data: any;
  timestamp: string;
}

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION });
const docClient = DynamoDBDocumentClient.from(dynamoClient);
const eventBridge = new EventBridgeClient({ region: process.env.AWS_REGION });

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const startTime = Date.now();
  const { httpMethod, path, headers } = event;
  const userId = extractUserIdFromToken(headers.Authorization);

  logger.info('Frontend API request', {
    method: httpMethod,
    path,
    userId,
    userAgent: headers['User-Agent']
  });

  try {
    const pathSegments = path.split('/').filter(Boolean);
    const endpoint = pathSegments[2]; // /api/frontend/{endpoint}

    switch (httpMethod) {
      case 'GET':
        return await handleGetRequest(endpoint, pathSegments, event.queryStringParameters, userId);
      case 'POST':
        return await handlePostRequest(endpoint, pathSegments, JSON.parse(event.body || '{}'), userId);
      case 'PUT':
        return await handlePutRequest(endpoint, pathSegments, JSON.parse(event.body || '{}'), userId);
      default:
        return createFrontendResponse(405, { error: 'Method not allowed' });
    }
  } catch (error) {
    logger.error('Frontend API error', { error, path, method: httpMethod });
    return createFrontendResponse(500, {
      error: 'Internal server error',
      errorId: `err_${Date.now()}`,
      support: 'Contact support@petplantr.com'
    });
  }
};

async function handleGetRequest(
  endpoint: string,
  pathSegments: string[],
  queryParams: any,
  userId: string
): Promise<APIGatewayProxyResult> {
  switch (endpoint) {
    case 'dashboard':
      return await getDashboard(userId);
    case 'orders':
      const orderId = pathSegments[3];
      return orderId ? await getOrder(orderId, userId) : await getOrdersList(userId, queryParams);
    case 'printers':
      return await getPrintersForFrontend(queryParams?.live === 'true');
    case 'farm-status':
      return await getFarmStatusForFrontend();
    case 'notifications':
      return await getNotifications(userId);
    case 'analytics':
      return await getAnalytics(userId, queryParams?.timeframe || '30d');
    default:
      return createFrontendResponse(404, { error: 'Endpoint not found' });
  }
}

async function handlePostRequest(
  endpoint: string,
  pathSegments: string[],
  body: any,
  userId: string
): Promise<APIGatewayProxyResult> {
  switch (endpoint) {
    case 'orders':
      return await createOrderForFrontend(body, userId);
    case 'notifications':
      return await updateNotificationPreferences(body, userId);
    case 'feedback':
      return await submitFeedback(body, userId);
    case 'support':
      return await createSupportTicket(body, userId);
    default:
      return createFrontendResponse(404, { error: 'Endpoint not found' });
  }
}

async function handlePutRequest(
  endpoint: string,
  pathSegments: string[],
  body: any,
  userId: string
): Promise<APIGatewayProxyResult> {
  switch (endpoint) {
    case 'orders':
      const orderId = pathSegments[3];
      return await updateOrderForFrontend(orderId, body, userId);
    case 'profile':
      return await updateProfile(body, userId);
    default:
      return createFrontendResponse(404, { error: 'Endpoint not found' });
  }
}

async function getDashboard(userId: string): Promise<APIGatewayProxyResult> {
  try {
    // Get user profile
    const userResponse = await docClient.send(new GetCommand({
      TableName: process.env.USERS_TABLE || 'petplantr-users',
      Key: { userId }
    }));

    if (!userResponse.Item) {
      return createFrontendResponse(404, { error: 'User not found' });
    }

    const user = userResponse.Item;

    // Get current orders
    const ordersResponse = await docClient.send(new ScanCommand({
      TableName: process.env.ORDERS_TABLE || 'petplantr-orders',
      FilterExpression: 'customerId = :userId AND #status <> :completed',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':userId': userId,
        ':completed': 'completed'
      }
    }));

    const currentOrders = (ordersResponse.Items || []).map(transformOrderForFrontend);

    // Get recent activity
    const recentActivity = await getRecentActivity(userId);

    // Get statistics
    const statistics = await getUserStatistics(userId);

    // Get farm status
    const farmStatus = await getCurrentFarmStatus();

    // Get recommendations
    const recommendations = await getPersonalizedRecommendations(userId);

    const dashboard: FrontendDashboard = {
      user: {
        id: user.userId,
        email: user.email,
        name: user.name || user.email.split('@')[0],
        totalOrders: statistics.totalOrders,
        memberSince: user.createdAt
      },
      currentOrders,
      recentActivity,
      statistics,
      farmStatus,
      recommendations
    };

    return createFrontendResponse(200, { dashboard });

  } catch (error) {
    logger.error('Failed to get dashboard', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to load dashboard' });
  }
}

async function getOrder(orderId: string, userId: string): Promise<APIGatewayProxyResult> {
  try {
    const response = await docClient.send(new GetCommand({
      TableName: process.env.ORDERS_TABLE || 'petplantr-orders',
      Key: { orderId }
    }));

    if (!response.Item) {
      return createFrontendResponse(404, { error: 'Order not found' });
    }

    const order = response.Item;

    // Verify user ownership
    if (order.customerId !== userId) {
      return createFrontendResponse(403, { error: 'Access denied' });
    }

    const frontendOrder = transformOrderForFrontend(order);

    // Get printer details if assigned
    if (order.printerId) {
      const printerResponse = await docClient.send(new GetCommand({
        TableName: process.env.PRINTERS_TABLE || 'petplantr-printers',
        Key: { printerId: order.printerId }
      }));

      if (printerResponse.Item) {
        frontendOrder.printer = {
          id: printerResponse.Item.printerId,
          name: printerResponse.Item.name,
          status: printerResponse.Item.status,
          progress: printerResponse.Item.progress || 0
        };
      }
    }

    return createFrontendResponse(200, { order: frontendOrder });

  } catch (error) {
    logger.error('Failed to get order', { orderId, userId, error });
    return createFrontendResponse(500, { error: 'Failed to load order' });
  }
}

async function createOrderForFrontend(orderData: any, userId: string): Promise<APIGatewayProxyResult> {
  try {
    const orderId = `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Validate input
    const validation = validateOrderInput(orderData);
    if (!validation.isValid) {
      return createFrontendResponse(400, { 
        error: 'Validation failed',
        details: validation.errors 
      });
    }

    // Calculate pricing
    const pricing = calculatePricing(orderData);

    // Create order
    const order = {
      orderId,
      customerId: userId,
      customerEmail: orderData.customerEmail,
      petName: orderData.petName,
      status: 'pending',
      photoUrls: orderData.photos || [],
      preferences: {
        size: orderData.size || 'medium',
        material: orderData.material || 'PLA',
        color: orderData.color || 'brown',
        quality: orderData.quality || 'standard'
      },
      pricing,
      notifications: orderData.notifications || {
        email: true,
        sms: false,
        push: true
      },
      metadata: {
        source: 'frontend',
        userAgent: orderData.userAgent || 'unknown',
        ipAddress: orderData.ipAddress || 'unknown'
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    await docClient.send(new PutCommand({
      TableName: process.env.ORDERS_TABLE || 'petplantr-orders',
      Item: order
    }));

    // Emit order created event
    await eventBridge.send(new PutEventsCommand({
      Entries: [{
        Source: 'petplantr.frontend',
        DetailType: 'Order Created',
        Detail: JSON.stringify({
          orderId,
          customerId: userId,
          petName: orderData.petName,
          timestamp: new Date().toISOString()
        })
      }]
    }));

    // Send real-time update
    await sendWebSocketUpdate({
      type: 'order_update',
      userId,
      orderId,
      data: { status: 'pending', message: 'Order created successfully' },
      timestamp: new Date().toISOString()
    });

    // Log business event
    logger.logBusinessEvent('OrderCreated', {
      orderId,
      customerId: userId,
      petName: orderData.petName,
      totalPrice: pricing.total
    });

    const frontendOrder = transformOrderForFrontend(order);

    return createFrontendResponse(201, { 
      success: true,
      message: 'Order created successfully!',
      order: frontendOrder,
      nextSteps: [
        'AI will analyze your pet photos',
        'Custom 3D model will be generated',
        'Your planter will be printed',
        'Order will be shipped to you'
      ]
    });

  } catch (error) {
    logger.error('Failed to create order', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to create order' });
  }
}

async function getPrintersForFrontend(includeLive: boolean = false): Promise<APIGatewayProxyResult> {
  try {
    const response = await docClient.send(new ScanCommand({
      TableName: process.env.PRINTERS_TABLE || 'petplantr-printers'
    }));

    const printers = (response.Items || []).map(printer => {
      const frontendPrinter: FrontendPrinterStatus = {
        id: printer.printerId,
        name: printer.name,
        model: printer.model || 'Ender 3 Pro',
        status: printer.status,
        capabilities: {
          materials: ['PLA', 'ABS', 'PETG'],
          maxSize: { x: 220, y: 220, z: 250 },
          quality: ['standard', 'high', 'premium'],
          speed: 'moderate'
        },
        statistics: {
          totalJobsCompleted: printer.totalJobsCompleted || 0,
          successRate: printer.successRate || 100,
          averageQuality: printer.qualityScoreAvg || 95,
          totalPrintTime: formatDuration(printer.totalPrintTime || 0),
          lastMaintenance: printer.lastMaintenance || 'Unknown'
        },
        realtime: includeLive ? {
          temperatureBed: printer.temperatureBed || 0,
          temperatureNozzle: printer.temperatureNozzle || 0,
          progress: printer.progress || 0,
          layerCurrent: printer.layerCurrent || 0,
          layerTotal: printer.layerTotal || 0,
          materialRemaining: printer.materialRemaining || 100
        } : {
          temperatureBed: 0,
          temperatureNozzle: 0,
          progress: 0,
          layerCurrent: 0,
          layerTotal: 0,
          materialRemaining: 100
        }
      };

      // Add current job if printing
      if (printer.currentJob && printer.status === 'printing') {
        frontendPrinter.currentJob = {
          id: printer.currentJob,
          customerName: 'Customer', // Would get from job details
          petName: 'Pet', // Would get from job details
          breed: 'Unknown', // Would get from job details
          progress: printer.progress || 0,
          estimatedCompletion: printer.estimatedCompletion || 'Unknown',
          timeRemaining: calculateTimeRemaining(printer.progress, printer.estimatedCompletion)
        };
      }

      return frontendPrinter;
    });

    return createFrontendResponse(200, { 
      printers,
      summary: {
        total: printers.length,
        idle: printers.filter(p => p.status === 'idle').length,
        printing: printers.filter(p => p.status === 'printing').length,
        offline: printers.filter(p => p.status === 'offline').length,
        utilizationRate: Math.round((printers.filter(p => p.status === 'printing').length / printers.length) * 100)
      }
    });

  } catch (error) {
    logger.error('Failed to get printers for frontend', { error });
    return createFrontendResponse(500, { error: 'Failed to load printer status' });
  }
}

async function getFarmStatusForFrontend(): Promise<APIGatewayProxyResult> {
  try {
    // This would integrate with the existing farm status but optimize for frontend
    const farmStatus = {
      operational: true,
      capacity: {
        total: 8,
        active: 6,
        utilization: 75
      },
      queue: {
        size: 12,
        estimatedWaitTime: '2-4 hours',
        averageProcessingTime: '3.5 hours'
      },
      performance: {
        successRate: 97.5,
        averageQuality: 96.2,
        onTimeDelivery: 94.8
      },
      alerts: [
        {
          type: 'info',
          message: 'All printers operational',
          timestamp: new Date().toISOString()
        }
      ]
    };

    return createFrontendResponse(200, { farmStatus });

  } catch (error) {
    logger.error('Failed to get farm status for frontend', { error });
    return createFrontendResponse(500, { error: 'Failed to load farm status' });
  }
}

async function getOrdersList(userId: string, queryParams: any): Promise<APIGatewayProxyResult> {
  try {
    const response = await docClient.send(new ScanCommand({
      TableName: process.env.ORDERS_TABLE || 'petplantr-orders',
      FilterExpression: 'customerId = :userId',
      ExpressionAttributeValues: {
        ':userId': userId
      }
    }));

    const orders = (response.Items || []).map(transformOrderForFrontend);
    
    // Apply filters from query params
    let filteredOrders = orders;
    if (queryParams?.status) {
      filteredOrders = orders.filter(order => order.status === queryParams.status);
    }

    return createFrontendResponse(200, { 
      orders: filteredOrders,
      total: filteredOrders.length
    });

  } catch (error) {
    logger.error('Failed to get orders list', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to load orders' });
  }
}

async function getNotifications(userId: string): Promise<APIGatewayProxyResult> {
  try {
    // Mock implementation - would query notifications table
    const notifications = [
      {
        id: 'notif_1',
        type: 'order_update',
        title: 'Order Update',
        message: 'Your planter is now printing!',
        read: false,
        timestamp: new Date().toISOString()
      }
    ];

    return createFrontendResponse(200, { notifications });
  } catch (error) {
    logger.error('Failed to get notifications', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to load notifications' });
  }
}

async function getAnalytics(userId: string, timeframe: string): Promise<APIGatewayProxyResult> {
  try {
    // Mock implementation - would calculate analytics
    const analytics = {
      timeframe,
      orders: {
        total: 5,
        completed: 4,
        inProgress: 1,
        successRate: 100
      },
      spending: {
        total: 149.95,
        average: 29.99,
        currency: 'USD'
      },
      trends: {
        orderFrequency: 'monthly',
        favoriteSize: 'medium',
        favoriteMaterial: 'PLA'
      }
    };

    return createFrontendResponse(200, { analytics });
  } catch (error) {
    logger.error('Failed to get analytics', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to load analytics' });
  }
}

async function updateNotificationPreferences(body: any, userId: string): Promise<APIGatewayProxyResult> {
  try {
    // Update user notification preferences
    await docClient.send(new UpdateCommand({
      TableName: process.env.USERS_TABLE || 'petplantr-users',
      Key: { userId },
      UpdateExpression: 'SET notificationPreferences = :prefs, updatedAt = :timestamp',
      ExpressionAttributeValues: {
        ':prefs': body.preferences,
        ':timestamp': new Date().toISOString()
      }
    }));

    return createFrontendResponse(200, { 
      success: true,
      message: 'Notification preferences updated successfully'
    });
  } catch (error) {
    logger.error('Failed to update notification preferences', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to update preferences' });
  }
}

async function submitFeedback(body: any, userId: string): Promise<APIGatewayProxyResult> {
  try {
    const feedbackId = `feedback_${Date.now()}`;
    
    await docClient.send(new PutCommand({
      TableName: process.env.FEEDBACK_TABLE || 'petplantr-feedback',
      Item: {
        feedbackId,
        userId,
        type: body.type || 'general',
        rating: body.rating,
        message: body.message,
        orderId: body.orderId,
        createdAt: new Date().toISOString()
      }
    }));

    return createFrontendResponse(200, { 
      success: true,
      message: 'Thank you for your feedback!',
      feedbackId
    });
  } catch (error) {
    logger.error('Failed to submit feedback', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to submit feedback' });
  }
}

async function createSupportTicket(body: any, userId: string): Promise<APIGatewayProxyResult> {
  try {
    const ticketId = `ticket_${Date.now()}`;
    
    await docClient.send(new PutCommand({
      TableName: process.env.SUPPORT_TABLE || 'petplantr-support',
      Item: {
        ticketId,
        userId,
        subject: body.subject,
        message: body.message,
        priority: body.priority || 'normal',
        status: 'open',
        orderId: body.orderId,
        createdAt: new Date().toISOString()
      }
    }));

    return createFrontendResponse(200, { 
      success: true,
      message: 'Support ticket created. We\'ll get back to you soon!',
      ticketId
    });
  } catch (error) {
    logger.error('Failed to create support ticket', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to create support ticket' });
  }
}

async function updateOrderForFrontend(orderId: string, body: any, userId: string): Promise<APIGatewayProxyResult> {
  try {
    // Verify order ownership
    const orderResponse = await docClient.send(new GetCommand({
      TableName: process.env.ORDERS_TABLE || 'petplantr-orders',
      Key: { orderId }
    }));

    if (!orderResponse.Item || orderResponse.Item.customerId !== userId) {
      return createFrontendResponse(403, { error: 'Access denied' });
    }

    // Update allowed fields
    const allowedUpdates = ['notifications', 'deliveryAddress'];
    const updates: any = {};
    
    for (const field of allowedUpdates) {
      if (body[field] !== undefined) {
        updates[field] = body[field];
      }
    }

    if (Object.keys(updates).length === 0) {
      return createFrontendResponse(400, { error: 'No valid updates provided' });
    }

    updates.updatedAt = new Date().toISOString();

    const updateExpression = 'SET ' + Object.keys(updates).map(key => `${key} = :${key}`).join(', ');
    const expressionAttributeValues = Object.keys(updates).reduce((acc, key) => {
      acc[`:${key}`] = updates[key];
      return acc;
    }, {} as any);

    await docClient.send(new UpdateCommand({
      TableName: process.env.ORDERS_TABLE || 'petplantr-orders',
      Key: { orderId },
      UpdateExpression: updateExpression,
      ExpressionAttributeValues: expressionAttributeValues
    }));

    return createFrontendResponse(200, { 
      success: true,
      message: 'Order updated successfully'
    });
  } catch (error) {
    logger.error('Failed to update order', { orderId, userId, error });
    return createFrontendResponse(500, { error: 'Failed to update order' });
  }
}

async function updateProfile(body: any, userId: string): Promise<APIGatewayProxyResult> {
  try {
    const allowedUpdates = ['name', 'phone', 'address', 'preferences'];
    const updates: any = {};
    
    for (const field of allowedUpdates) {
      if (body[field] !== undefined) {
        updates[field] = body[field];
      }
    }

    if (Object.keys(updates).length === 0) {
      return createFrontendResponse(400, { error: 'No valid updates provided' });
    }

    updates.updatedAt = new Date().toISOString();

    const updateExpression = 'SET ' + Object.keys(updates).map(key => `${key} = :${key}`).join(', ');
    const expressionAttributeValues = Object.keys(updates).reduce((acc, key) => {
      acc[`:${key}`] = updates[key];
      return acc;
    }, {} as any);

    await docClient.send(new UpdateCommand({
      TableName: process.env.USERS_TABLE || 'petplantr-users',
      Key: { userId },
      UpdateExpression: updateExpression,
      ExpressionAttributeValues: expressionAttributeValues
    }));

    return createFrontendResponse(200, { 
      success: true,
      message: 'Profile updated successfully'
    });
  } catch (error) {
    logger.error('Failed to update profile', { userId, error });
    return createFrontendResponse(500, { error: 'Failed to update profile' });
  }
}

// Helper functions

function transformOrderForFrontend(order: any): FrontendOrder {
  return {
    id: order.orderId,
    customerId: order.customerId,
    customerEmail: order.customerEmail || 'unknown@example.com',
    petName: order.petName || 'Your Pet',
    breed: order.breedPredictions?.primary_breed,
    status: order.status,
    progress: calculateOrderProgress(order),
    photos: {
      urls: order.photoUrls || [],
      thumbnails: (order.photoUrls || []).map((url: string) => url.replace(/\.[^/.]+$/, '_thumb.jpg')),
      count: (order.photoUrls || []).length
    },
    planter: {
      stlUrl: order.stlFileUrl,
      previewUrl: order.previewImageUrl,
      size: order.preferences?.size || 'medium',
      material: order.preferences?.material || 'PLA',
      color: order.preferences?.color || 'brown',
      quality: order.preferences?.quality || 'standard'
    },
    pricing: order.pricing || {
      basePrice: 29.99,
      materialCost: 5.00,
      qualityUpgrade: 0,
      total: 34.99,
      currency: 'USD'
    },
    timeline: {
      ordered: order.createdAt,
      aiProcessingStarted: order.aiProcessingStarted,
      aiProcessingCompleted: order.aiProcessingCompleted,
      printingStarted: order.printingStarted,
      printingCompleted: order.printingCompleted,
      shipped: order.shippedAt,
      delivered: order.deliveredAt
    },
    notifications: order.notifications || {
      email: true,
      sms: false,
      push: true
    },
    metadata: {
      source: order.metadata?.source || 'unknown',
      userAgent: order.metadata?.userAgent || 'unknown',
      ipAddress: order.metadata?.ipAddress || 'unknown',
      createdAt: order.createdAt,
      updatedAt: order.updatedAt
    }
  };
}

function calculateOrderProgress(order: any): FrontendOrder['progress'] {
  const stages = ['pending', 'processing', 'modeling', 'printing', 'completed'];
  const currentStageIndex = stages.indexOf(order.status);
  const percentage = Math.round((currentStageIndex / (stages.length - 1)) * 100);

  return {
    current: currentStageIndex + 1,
    total: stages.length,
    percentage,
    stage: order.status,
    estimatedCompletion: order.estimatedCompletion
  };
}

function validateOrderInput(orderData: any): { isValid: boolean; errors?: string[] } {
  const errors: string[] = [];

  if (!orderData.petName || orderData.petName.trim().length === 0) {
    errors.push('Pet name is required');
  }

  if (!orderData.photos || !Array.isArray(orderData.photos) || orderData.photos.length === 0) {
    errors.push('At least one photo is required');
  }

  if (orderData.photos && orderData.photos.length > 10) {
    errors.push('Maximum 10 photos allowed');
  }

  const validSizes = ['small', 'medium', 'large'];
  if (orderData.size && !validSizes.includes(orderData.size)) {
    errors.push('Invalid size selection');
  }

  const validMaterials = ['PLA', 'ABS', 'PETG'];
  if (orderData.material && !validMaterials.includes(orderData.material)) {
    errors.push('Invalid material selection');
  }

  return {
    isValid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined
  };
}

function calculatePricing(orderData: any): FrontendOrder['pricing'] {
  let basePrice = 29.99;
  let materialCost = 5.00;
  let qualityUpgrade = 0;

  // Size pricing
  if (orderData.size === 'large') {
    basePrice += 10.00;
    materialCost += 3.00;
  } else if (orderData.size === 'small') {
    basePrice -= 5.00;
    materialCost -= 2.00;
  }

  // Material pricing
  if (orderData.material === 'ABS') {
    materialCost += 2.00;
  } else if (orderData.material === 'PETG') {
    materialCost += 4.00;
  }

  // Quality pricing
  if (orderData.quality === 'high') {
    qualityUpgrade = 10.00;
  } else if (orderData.quality === 'premium') {
    qualityUpgrade = 20.00;
  }

  return {
    basePrice,
    materialCost,
    qualityUpgrade,
    total: basePrice + materialCost + qualityUpgrade,
    currency: 'USD'
  };
}

async function getRecentActivity(userId: string): Promise<FrontendDashboard['recentActivity']> {
  // Mock implementation - would query activity log
  return [
    {
      id: 'activity_1',
      type: 'order_created',
      message: 'New order created for Buddy',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      orderId: 'order_123'
    },
    {
      id: 'activity_2',
      type: 'ai_completed',
      message: 'AI processing completed for Max',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      orderId: 'order_122'
    }
  ];
}

async function getUserStatistics(userId: string): Promise<FrontendDashboard['statistics']> {
  // Mock implementation - would aggregate from orders
  return {
    totalOrders: 5,
    completedOrders: 4,
    successRate: 100,
    averageProcessingTime: '4.2 hours',
    favoriteBreed: 'Golden Retriever'
  };
}

async function getCurrentFarmStatus(): Promise<FrontendDashboard['farmStatus']> {
  // Mock implementation - would get from farm management
  return {
    queuePosition: 3,
    estimatedWaitTime: '2-3 hours',
    activePrinters: 6,
    totalCapacity: 8,
    utilizationRate: 75
  };
}

async function getPersonalizedRecommendations(userId: string): Promise<FrontendDashboard['recommendations']> {
  // Mock implementation - would use ML for personalization
  return [
    {
      type: 'material_upgrade',
      title: 'Upgrade to Premium Quality',
      description: 'Get 20% better surface finish with our premium printing option',
      actionUrl: '/upgrade'
    }
  ];
}

async function sendWebSocketUpdate(message: WebSocketMessage): Promise<void> {
  // This would integrate with API Gateway WebSocket API
  logger.info('WebSocket update sent', { message });
}

function extractUserIdFromToken(authHeader?: string): string {
  // Mock implementation - would decode JWT
  return 'user_123';
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

function calculateTimeRemaining(progress: number, estimatedCompletion: string): string {
  // Mock calculation
  return '1h 23m';
}

function createFrontendResponse(statusCode: number, body: any): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Cache-Control': statusCode === 200 ? 'public, max-age=60' : 'no-cache',
      'X-API-Version': '2.0',
      'X-Response-Time': new Date().toISOString()
    },
    body: JSON.stringify({
      success: statusCode < 400,
      timestamp: new Date().toISOString(),
      ...body
    })
  };
}
