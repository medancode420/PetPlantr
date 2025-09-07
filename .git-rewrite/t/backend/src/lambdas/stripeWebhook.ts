import Stripe from 'stripe';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import EnhancedEmailService from '../services/enhancedEmailService';
import { withErrorHandling, ValidationError, ExternalServiceError } from '../utils/enhancedErrorHandler';
import { logger } from '../utils/enhancedLogger';
import { validateInput, lambdaSchemas } from '../utils/validation';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

const eventBridge = new EventBridgeClient({ region: 'us-east-1' });
const emailService = new EnhancedEmailService();

const stripeWebhookHandler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  const requestId = event.requestContext?.requestId || 'unknown';
  const correlationId = `webhook_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  
  logger.info('Stripe webhook received', {
    correlationId,
    requestId,
    userAgent: event.headers?.['User-Agent'],
    sourceIp: event.requestContext?.identity?.sourceIp
  });

  const headers = {
    'Content-Type': 'application/json',
    'X-Correlation-ID': correlationId,
  };

  const signature = event.headers['stripe-signature'] || event.headers['Stripe-Signature'];
  
  if (!signature) {
    logger.warn('Missing Stripe signature', { correlationId });
    throw new ValidationError('Missing stripe signature');
  }

  if (!event.body) {
    logger.warn('Missing request body', { correlationId });
    throw new ValidationError('Missing request body');
  }

  // Verify webhook signature
  let stripeEvent: Stripe.Event;
  try {
    stripeEvent = stripe.webhooks.constructEvent(
      event.body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (error) {
    logger.error('Webhook signature verification failed', { 
      correlationId, 
      error: error instanceof Error ? error.message : String(error) 
    });
    throw new ValidationError('Invalid signature');
  }

  logger.info('Received Stripe event', {
    correlationId,
    eventType: stripeEvent.type,
    eventId: stripeEvent.id
  });

  // Validate webhook event structure
  const validatedEvent = validateInput(stripeEvent, lambdaSchemas.stripeWebhook);

  // Handle checkout session completed
  if (stripeEvent.type === 'checkout.session.completed') {
    const session = stripeEvent.data.object as Stripe.Checkout.Session;
    
    if (session.payment_status === 'paid') {
      await handlePaymentSuccess(session, correlationId);
    } else {
      logger.warn('Payment not completed', {
        correlationId,
        sessionId: session.id,
        paymentStatus: session.payment_status
      });
    }
  }

  logger.info('Webhook processed successfully', {
    correlationId,
    eventType: stripeEvent.type
  });

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ 
      success: true,
      received: true,
      correlationId,
      timestamp: new Date().toISOString()
    }),
  };
};

async function handlePaymentSuccess(session: Stripe.Checkout.Session, correlationId?: string): Promise<void> {
  try {
    logger.info('Processing payment success', {
      correlationId,
      sessionId: session.id,
      paymentStatus: session.payment_status
    });

    const metadata = session.metadata || {};
    const { userId, photoUrls, photoCount } = metadata;
    
    if (!userId) {
      throw new Error('Missing userId in session metadata');
    }

    // Parse photo URLs from metadata
    const photoKeys = photoUrls ? photoUrls.split(',').map(url => {
      // Extract S3 key from full URL or return as-is if already a key
      const match = url.match(/([^\/]+\/[^\/]+\.(jpg|jpeg|png|webp))$/i);
      return match ? match[1] : url;
    }) : [];

    // Determine SKU and size tier from line items or metadata
    // For now, we'll use the SKU from metadata or default to basic
    const sku = metadata.sku || 'pet-planter-basic';
    const sizeTier = getSizeTierFromSku(sku);

    // Generate order ID
    const orderId = `pp_${new Date().toISOString().split('T')[0].replace(/-/g, '')}_${Math.random().toString(36).substr(2, 5)}`;

    // Create the ORDER_PAID event with the specified schema
    const eventDetail = {
      orderId,
      userId,
      sku: sizeTier, // Use size tier as SKU (SMALL, MEDIUM, LARGE)
      sizeTier,
      photoKeys,
      sessionId: session.id,
      amountPaid: session.amount_total || 0,
      currency: session.currency || 'usd',
      customerEmail: session.customer_details?.email,
      timestamp: new Date().toISOString(),
    };

    const putEventsCommand = new PutEventsCommand({
      Entries: [
        {
          Source: 'petplantr.payments',
          DetailType: 'ORDER_PAID',
          Detail: JSON.stringify(eventDetail),
          EventBusName: process.env.EVENT_BUS_NAME,
          Time: new Date(),
        },
      ],
    });

    const result = await eventBridge.send(putEventsCommand);
    console.log('EventBridge result:', result);

    // Send order confirmation email via Microsoft Graph
    if (session.customer_details?.email) {
      try {
        const customerName = session.customer_details.name || 'Valued Customer';
        const orderDetails = {
          orderId,
          userId,
          photoCount: photoKeys.length,
          sizeTier,
          amount: session.amount_total || 0
        };

        const emailSent = await emailService.sendOrderConfirmation(
          { email: session.customer_details.email, name: customerName },
          orderDetails
        );

        if (emailSent) {
          console.log(`Order confirmation email sent to ${session.customer_details.email}`);
          
          // Send internal notification to Daniel about new order
          await emailService.sendInternalAlert(
            `New Order Received: #${orderId}`,
            `New PetPlantr order received from ${customerName} (${session.customer_details.email}). Processing ${photoKeys.length} photos for ${sizeTier} size planter.`,
            'normal',
            orderDetails
          );
        }
      } catch (emailError) {
        console.error('Failed to send order confirmation email:', emailError);
        // Don't fail the webhook if email fails
      }
    }

    // Log successful payment
    console.log('Payment processed successfully:', {
      orderId,
      sessionId: session.id,
      userId,
      sizeTier,
      photoCount: photoKeys.length,
      amount: session.amount_total,
    });

  } catch (error) {
    console.error('Error handling payment success:', error);
    
    // Send error to Slack
    if (process.env.SLACK_WEBHOOK_URL) {
      await sendSlackAlert(`Payment Processing Error: ${error}`);
    }
    
    throw error; // Re-throw to trigger retry logic
  }
}

// Helper function to determine size tier from SKU
function getSizeTierFromSku(sku: string): string {
  // Map SKUs to size tiers
  const skuToSizeMap: Record<string, string> = {
    'pet-planter-basic': 'SMALL',
    'pet-planter-small': 'SMALL', 
    'pet-planter-medium': 'MEDIUM',
    'pet-planter-large': 'LARGE',
  };
  
  return skuToSizeMap[sku] || 'MEDIUM'; // Default to MEDIUM
}

async function sendSlackAlert(message: string): Promise<void> {
  try {
    if (!process.env.SLACK_WEBHOOK_URL) return;
    
    const response = await fetch(process.env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: `🚨 PetPlantr Alert: ${message}`,
        channel: '#ops-alerts',
      }),
    });
    
    if (!response.ok) {
      console.error('Failed to send Slack alert:', response.status);
    }
  } catch (error) {
    console.error('Slack alert error:', error);
  }
}

// Export the handler wrapped with error handling
export const handler = withErrorHandling(stripeWebhookHandler);
