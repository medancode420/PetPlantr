import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

/**
 * 🚀 Enhanced Order Processing Lambda
 * Integrates payment processing with automatic 3D printing farm assignment
 */

interface OrderDetails {
  orderId: string;
  customerId: string;
  customerEmail: string;
  customerName: string;
  petName: string;
  petBreed: string;
  photoUrls: string[];
  productType: 'basic' | 'premium' | 'custom';
  planterSize: 'small' | 'medium' | 'large';
  materialPreference: string;
  colorPreference: string;
  priority: number;
  estimatedDelivery: string;
  totalAmount: number;
  paymentStatus: 'pending' | 'completed' | 'failed';
  orderStatus: 'received' | 'processing' | 'modeling' | 'queued' | 'printing' | 'completed' | 'shipped';
  createdAt: string;
  updatedAt: string;
}

interface PrintJobRequest {
  jobId: string;
  customerId: string;
  customerEmail: string;
  petName: string;
  breed: string;
  stlFile: string;
  estimatedTime: number;
  materialType: string;
  materialColor: string;
  priority: number;
  complexity: number;
  qualityRequirements: 'standard' | 'high' | 'premium';
  deadline?: string;
}

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    const { httpMethod, path, body } = event;
    console.log(`🚀 Enhanced Order Processing: ${httpMethod} ${path}`);

    switch (httpMethod) {
      case 'POST':
        if (path.includes('/orders')) {
          return await createOrder(JSON.parse(body || '{}'));
        } else if (path.includes('/orders/complete-modeling')) {
          return await completeModeling(JSON.parse(body || '{}'));
        } else if (path.includes('/orders/update-status')) {
          return await updateOrderStatus(JSON.parse(body || '{}'));
        }
        break;
      case 'GET':
        if (path.includes('/orders/')) {
          const orderId = path.split('/').pop();
          return await getOrder(orderId!);
        } else if (path.includes('/orders')) {
          return await getOrders(event.queryStringParameters);
        }
        break;
      case 'PUT':
        if (path.includes('/orders/')) {
          const orderId = path.split('/').pop();
          return await updateOrder(orderId!, JSON.parse(body || '{}'));
        }
        break;
      default:
        return createResponse(405, { error: 'Method not allowed' });
    }

    return createResponse(404, { error: 'Endpoint not found' });

  } catch (error) {
    console.error('🚨 Order processing error:', error);
    return createResponse(500, { 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

async function createOrder(orderData: any): Promise<APIGatewayProxyResult> {
  try {
    const order: OrderDetails = {
      orderId: orderData.orderId || `order_${Date.now()}`,
      customerId: orderData.customerId,
      customerEmail: orderData.customerEmail,
      customerName: orderData.customerName,
      petName: orderData.petName,
      petBreed: orderData.petBreed,
      photoUrls: orderData.photoUrls || [],
      productType: orderData.productType || 'basic',
      planterSize: orderData.planterSize || 'medium',
      materialPreference: orderData.materialPreference || 'PLA',
      colorPreference: orderData.colorPreference || 'Natural',
      priority: calculatePriority(orderData.productType, orderData.rushOrder),
      estimatedDelivery: calculateEstimatedDelivery(orderData.productType),
      totalAmount: orderData.totalAmount,
      paymentStatus: orderData.paymentStatus || 'pending',
      orderStatus: 'received',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save order to database (in production)
    console.log(`📋 Created order: ${order.orderId} for ${order.petName}`);

    // If payment is already completed, start processing
    if (order.paymentStatus === 'completed') {
      await startOrderProcessing(order);
    }

    // Send customer confirmation email
    await sendOrderConfirmation(order);

    return createResponse(201, {
      message: 'Order created successfully',
      order,
      nextSteps: order.paymentStatus === 'completed' ? 
        'Order processing will begin shortly' : 
        'Awaiting payment confirmation'
    });

  } catch (error) {
    console.error('Error creating order:', error);
    return createResponse(500, { error: 'Failed to create order' });
  }
}

async function completeModeling(modelingData: any): Promise<APIGatewayProxyResult> {
  try {
    const { orderId, stlFileUrl, qualityScore, complexity } = modelingData;

    // Update order status
    const order = await getOrderById(orderId);
    if (!order) {
      return createResponse(404, { error: 'Order not found' });
    }

    order.orderStatus = 'queued';
    order.updatedAt = new Date().toISOString();

    // Create print job for farm manager
    const printJob: PrintJobRequest = {
      jobId: `${orderId}_print`,
      customerId: order.customerId,
      customerEmail: order.customerEmail,
      petName: order.petName,
      breed: order.petBreed,
      stlFile: stlFileUrl,
      estimatedTime: calculatePrintTime(order.planterSize, complexity),
      materialType: order.materialPreference,
      materialColor: order.colorPreference,
      priority: order.priority,
      complexity: complexity || 5,
      qualityRequirements: order.productType === 'premium' ? 'high' : 
                          order.productType === 'custom' ? 'premium' : 'standard',
      deadline: order.estimatedDelivery
    };

    // Submit to farm manager
    const farmResponse = await submitToPrintFarm(printJob);
    
    if (farmResponse.success) {
      // Notify customer of printing status
      await sendPrintingNotification(order, printJob);
      
      console.log(`🖨️ Order ${orderId} queued for printing`);
      return createResponse(200, {
        message: 'Modeling completed, print job created',
        orderId,
        printJobId: printJob.jobId,
        estimatedPrintTime: printJob.estimatedTime,
        farmStatus: farmResponse.data
      });
    } else {
      return createResponse(500, { 
        error: 'Failed to queue print job',
        details: farmResponse.error 
      });
    }

  } catch (error) {
    console.error('Error completing modeling:', error);
    return createResponse(500, { error: 'Failed to complete modeling' });
  }
}

async function updateOrderStatus(statusData: any): Promise<APIGatewayProxyResult> {
  try {
    const { orderId, newStatus, printProgress, qualityScore, completionNotes } = statusData;

    const order = await getOrderById(orderId);
    if (!order) {
      return createResponse(404, { error: 'Order not found' });
    }

    const previousStatus = order.orderStatus;
    order.orderStatus = newStatus;
    order.updatedAt = new Date().toISOString();

    // Handle status-specific actions
    switch (newStatus) {
      case 'printing':
        await sendStatusUpdate(order, 'Your pet planter is now being printed! 🖨️');
        break;
      
      case 'completed':
        if (qualityScore) {
          await recordQualityScore(orderId, qualityScore);
        }
        await sendStatusUpdate(order, 'Your pet planter printing is complete! ✅');
        await scheduleShipping(order);
        break;
      
      case 'shipped':
        await sendShippingNotification(order);
        break;
      
      case 'failed':
        await handlePrintFailure(order, completionNotes);
        break;
    }

    console.log(`📊 Order ${orderId} status: ${previousStatus} → ${newStatus}`);
    
    return createResponse(200, {
      message: 'Order status updated successfully',
      orderId,
      previousStatus,
      newStatus,
      order
    });

  } catch (error) {
    console.error('Error updating order status:', error);
    return createResponse(500, { error: 'Failed to update order status' });
  }
}

async function getOrder(orderId: string): Promise<APIGatewayProxyResult> {
  try {
    const order = await getOrderById(orderId);
    if (!order) {
      return createResponse(404, { error: 'Order not found' });
    }

    // Get associated print job status if available
    const printJobStatus = await getPrintJobStatus(`${orderId}_print`);

    return createResponse(200, {
      order,
      printJob: printJobStatus,
      timeline: generateOrderTimeline(order)
    });

  } catch (error) {
    console.error('Error getting order:', error);
    return createResponse(500, { error: 'Failed to get order' });
  }
}

async function getOrders(queryParams: any): Promise<APIGatewayProxyResult> {
  try {
    // Mock orders for demonstration
    const orders = await getOrdersByQuery(queryParams);

    return createResponse(200, {
      orders,
      pagination: {
        total: orders.length,
        page: parseInt(queryParams?.page || '1'),
        limit: parseInt(queryParams?.limit || '10')
      }
    });

  } catch (error) {
    console.error('Error getting orders:', error);
    return createResponse(500, { error: 'Failed to get orders' });
  }
}

async function updateOrder(orderId: string, updateData: any): Promise<APIGatewayProxyResult> {
  try {
    const order = await getOrderById(orderId);
    if (!order) {
      return createResponse(404, { error: 'Order not found' });
    }

    // Update order properties
    Object.assign(order, updateData);
    order.updatedAt = new Date().toISOString();

    // In production, this would update DynamoDB
    console.log(`📝 Updated order ${orderId}`);

    return createResponse(200, {
      message: 'Order updated successfully',
      order
    });

  } catch (error) {
    console.error('Error updating order:', error);
    return createResponse(500, { error: 'Failed to update order' });
  }
}

// Helper functions

function calculatePriority(productType: string, rushOrder?: boolean): number {
  let priority = 5; // Default priority
  
  if (rushOrder) priority = 1; // Highest priority
  else if (productType === 'premium') priority = 2;
  else if (productType === 'custom') priority = 3;
  
  return priority;
}

function calculateEstimatedDelivery(productType: string): string {
  const baseDeliveryDays = productType === 'custom' ? 10 : 
                          productType === 'premium' ? 7 : 5;
  
  const deliveryDate = new Date();
  deliveryDate.setDate(deliveryDate.getDate() + baseDeliveryDays);
  
  return deliveryDate.toISOString();
}

function calculatePrintTime(size: string, complexity: number): number {
  let baseTime = 2.5; // hours
  
  if (size === 'large') baseTime = 4.0;
  else if (size === 'small') baseTime = 1.5;
  
  // Adjust for complexity (1-10 scale)
  const complexityMultiplier = 1 + (complexity - 5) * 0.1;
  
  return baseTime * complexityMultiplier;
}

async function startOrderProcessing(order: OrderDetails): Promise<void> {
  try {
    // Trigger AI modeling pipeline
    console.log(`🤖 Starting AI modeling for order ${order.orderId}`);
    
    // In production, this would trigger the existing modeling pipeline
    // For now, simulate by updating status
    setTimeout(() => {
      order.orderStatus = 'modeling';
    }, 1000);

  } catch (error) {
    console.error('Error starting order processing:', error);
  }
}

async function submitToPrintFarm(printJob: PrintJobRequest): Promise<any> {
  try {
    // In production, this would call the farm manager API
    console.log(`🏭 Submitting print job to farm: ${printJob.jobId}`);
    
    // Mock successful submission
    return {
      success: true,
      data: {
        jobId: printJob.jobId,
        assignedPrinter: 'k1_max_02',
        estimatedCompletion: new Date(Date.now() + printJob.estimatedTime * 3600000).toISOString()
      }
    };

  } catch (error) {
    console.error('Error submitting to print farm:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

async function getPrintJobStatus(jobId: string): Promise<any> {
  // Mock print job status
  return {
    jobId,
    status: 'printing',
    progress: 67.5,
    assignedPrinter: 'k1_max_02',
    estimatedCompletion: new Date(Date.now() + 2 * 3600000).toISOString()
  };
}

async function getOrderById(orderId: string): Promise<OrderDetails | null> {
  // Mock order retrieval - in production, this would query DynamoDB
  return {
    orderId,
    customerId: 'cust_001',
    customerEmail: 'customer@example.com',
    customerName: 'Sarah Johnson',
    petName: 'Buddy',
    petBreed: 'Golden Retriever',
    photoUrls: ['/uploads/pet_photo_1.jpg'],
    productType: 'premium',
    planterSize: 'medium',
    materialPreference: 'PLA',
    colorPreference: 'Golden',
    priority: 2,
    estimatedDelivery: new Date(Date.now() + 7 * 24 * 3600000).toISOString(),
    totalAmount: 89.99,
    paymentStatus: 'completed',
    orderStatus: 'printing',
    createdAt: new Date(Date.now() - 2 * 24 * 3600000).toISOString(),
    updatedAt: new Date().toISOString()
  };
}

async function getOrdersByQuery(queryParams: any): Promise<OrderDetails[]> {
  // Mock orders list - in production, this would query DynamoDB with filters
  return [
    {
      orderId: 'order_001',
      customerId: 'cust_001',
      customerEmail: 'sarah@example.com',
      customerName: 'Sarah Johnson',
      petName: 'Buddy',
      petBreed: 'Golden Retriever',
      photoUrls: [],
      productType: 'premium',
      planterSize: 'medium',
      materialPreference: 'PLA',
      colorPreference: 'Golden',
      priority: 2,
      estimatedDelivery: new Date(Date.now() + 5 * 24 * 3600000).toISOString(),
      totalAmount: 89.99,
      paymentStatus: 'completed',
      orderStatus: 'printing',
      createdAt: new Date(Date.now() - 2 * 24 * 3600000).toISOString(),
      updatedAt: new Date().toISOString()
    }
  ];
}

async function sendOrderConfirmation(order: OrderDetails): Promise<void> {
  console.log(`📧 Sending order confirmation to ${order.customerEmail}`);
  // In production, this would use SES to send email
}

async function sendPrintingNotification(order: OrderDetails, printJob: PrintJobRequest): Promise<void> {
  console.log(`📧 Sending printing notification to ${order.customerEmail}`);
  // In production, this would send email with print details
}

async function sendStatusUpdate(order: OrderDetails, message: string): Promise<void> {
  console.log(`📧 Status update for ${order.customerEmail}: ${message}`);
  // In production, this would send email/SMS update
}

async function sendShippingNotification(order: OrderDetails): Promise<void> {
  console.log(`📦 Sending shipping notification to ${order.customerEmail}`);
  // In production, this would send shipping details
}

async function recordQualityScore(orderId: string, qualityScore: number): Promise<void> {
  console.log(`📊 Recording quality score ${qualityScore} for order ${orderId}`);
  // In production, this would update analytics
}

async function scheduleShipping(order: OrderDetails): Promise<void> {
  console.log(`📦 Scheduling shipping for order ${order.orderId}`);
  // In production, this would integrate with shipping service
}

async function handlePrintFailure(order: OrderDetails, notes?: string): Promise<void> {
  console.log(`❌ Handling print failure for order ${order.orderId}: ${notes}`);
  // In production, this would trigger retry or customer notification
}

function generateOrderTimeline(order: OrderDetails): any[] {
  return [
    {
      status: 'received',
      timestamp: order.createdAt,
      description: 'Order received and payment confirmed'
    },
    {
      status: 'modeling',
      timestamp: order.createdAt,
      description: 'AI modeling of your pet planter in progress'
    },
    {
      status: 'printing',
      timestamp: order.updatedAt,
      description: 'Your planter is being 3D printed'
    }
  ];
}

function createResponse(statusCode: number, body: any): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    },
    body: JSON.stringify(body)
  };
}
