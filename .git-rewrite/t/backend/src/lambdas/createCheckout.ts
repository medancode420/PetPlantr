import Stripe from 'stripe';
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { withErrorHandling, ValidationError } from '../utils/enhancedErrorHandler';
import { logger } from '../utils/enhancedLogger';
import { validateInput, lambdaSchemas } from '../utils/validation';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

interface CartItem {
  sku: 'SMALL' | 'MEDIUM' | 'LARGE' | 'BUNDLE';
  quantity: number;
}

interface CheckoutRequest {
  userId: string;
  items: CartItem[];
}

const createCheckoutHandler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  const requestId = event.requestContext?.requestId || 'unknown';
  const correlationId = `checkout_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  
  logger.info('CreateCheckout Lambda invoked', {
    correlationId,
    requestId,
    httpMethod: event.httpMethod,
    userAgent: event.headers?.['User-Agent']
  });

  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json',
    'X-Correlation-ID': correlationId,
  };

  // Handle preflight CORS
  if (event.httpMethod === 'OPTIONS') {
    logger.debug('CORS preflight request handled', { correlationId });
    return {
      statusCode: 200,
      headers,
      body: '',
    };
  }

  if (!event.body) {
    logger.warn('Missing request body', { correlationId });
    throw new ValidationError('Request body is required');
  }

  // Parse and validate request body
  let requestData: CheckoutRequest;
  try {
    requestData = JSON.parse(event.body);
  } catch (error) {
    logger.warn('Invalid JSON in request body', { correlationId, error });
    throw new ValidationError('Invalid JSON format');
  }

  // Validate using Joi schema
  const validatedData = validateInput(requestData, lambdaSchemas.createCheckout);
  const { userId, items } = validatedData;

  logger.info('Processing checkout request', {
    correlationId,
    userId,
    itemCount: items.length,
    skus: items.map((item: CartItem) => item.sku)
  });

  // Validate and map SKUs to Stripe Price IDs
  const lineItems: Stripe.Checkout.SessionCreateParams.LineItem[] = [];
  
  for (const item of items) {
    const priceId = getPriceIdFromSku(item.sku);
    if (!priceId) {
      logger.error('Invalid SKU or missing price configuration', {
        correlationId,
        sku: item.sku
      });
      throw new ValidationError(`Invalid SKU or missing price configuration: ${item.sku}`);
    }

    lineItems.push({
      price: priceId,
      quantity: item.quantity,
    });
  }

  // Create Stripe checkout session
  logger.debug('Creating Stripe checkout session', {
    correlationId,
    lineItemsCount: lineItems.length
  });

  const session = await stripe.checkout.sessions.create({
    payment_method_types: ['card'],
    line_items: lineItems,
    mode: 'payment',
    success_url: `${process.env.FRONTEND_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.FRONTEND_URL}/upload`,
    metadata: {
      userId,
      itemCount: items.length.toString(),
      items: JSON.stringify(items),
      correlationId,
    },
  });

  logger.info('Checkout session created successfully', {
    correlationId,
    sessionId: session.id,
    userId,
    totalAmount: session.amount_total
  });

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({
      success: true,
      url: session.url,
      sessionId: session.id,
      correlationId,
      timestamp: new Date().toISOString()
    }),
  };
};

function getPriceIdFromSku(sku: string): string | null {
  const priceEnvKey = `STRIPE_PRICE_${sku}`;
  return process.env[priceEnvKey] || null;
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
export const handler = withErrorHandling(createCheckoutHandler);
