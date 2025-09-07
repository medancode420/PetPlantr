import { handler } from '../src/lambdas/stripeWebhook';
import { APIGatewayProxyEvent } from 'aws-lambda';
import Stripe from 'stripe';

// Mock Stripe and AWS SDK before any imports
jest.mock('stripe', () => {
  const mockConstructEvent = jest.fn();
  return jest.fn().mockImplementation(() => ({
    webhooks: {
      constructEvent: mockConstructEvent,
    },
  }));
});

jest.mock('@aws-sdk/client-eventbridge', () => {
  const mockSend = jest.fn();
  return {
    EventBridgeClient: jest.fn().mockImplementation(() => ({
      send: mockSend,
    })),
    PutEventsCommand: jest.fn().mockImplementation((params) => params),
  };
});

// Mock fetch for Slack alerts
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  status: 200,
} as Response);

// Import the mocked modules
import { EventBridgeClient } from '@aws-sdk/client-eventbridge';

describe('stripeWebhook Lambda', () => {
  let mockConstructEvent: jest.Mock;
  let mockSend: jest.Mock;

  beforeAll(() => {
    // Set up environment variables
    process.env = {
      ...process.env,
      STRIPE_SECRET_KEY: 'sk_test_123',
      STRIPE_WEBHOOK_SECRET: 'whsec_test_123',
      EVENT_BUS_NAME: 'petplantr-test',
      SLACK_WEBHOOK_URL: 'https://hooks.slack.com/test',
    };

    // Get the mocked functions
    const MockedStripe = Stripe as jest.MockedClass<typeof Stripe>;
    const mockStripeInstance = new MockedStripe('test') as any;
    mockConstructEvent = mockStripeInstance.webhooks.constructEvent;

    const MockedEventBridge = EventBridgeClient as jest.MockedClass<typeof EventBridgeClient>;
    const mockEventBridgeInstance = new MockedEventBridge({}) as any;
    mockSend = mockEventBridgeInstance.send;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset AWS SDK mock to success
    mockSend.mockResolvedValue({
      FailedEntryCount: 0,
      Entries: [{ EventId: 'test-event-id' }],
    });
  });

  const createMockEvent = (
    body: string,
    signature: string = 'valid_signature'
  ): APIGatewayProxyEvent => ({
    httpMethod: 'POST',
    body,
    headers: {
      'stripe-signature': signature,
    },
    multiValueHeaders: {},
    isBase64Encoded: false,
    path: '/api/stripe/webhook',
    pathParameters: null,
    queryStringParameters: null,
    multiValueQueryStringParameters: null,
    stageVariables: null,
    requestContext: {
      identity: {
        sourceIp: '127.0.0.1'
      }
    } as any,
    resource: '',
  });

  const mockStripeEvent = (type: string, sessionData: any): Stripe.Event => ({
    id: 'evt_test_123',
    object: 'event',
    api_version: '2023-10-16',
    created: Date.now(),
    data: {
      object: sessionData,
    },
    livemode: false,
    pending_webhooks: 1,
    request: {
      id: 'req_test_123',
      idempotency_key: null,
    },
    type: type as any,
  });

  describe('Request validation', () => {
    it('should return 400 when signature is missing', async () => {
      const event = createMockEvent('test body', '');
      event.headers = {}; // Remove signature header
      
      const result = await handler(event);

      expect(result.statusCode).toBe(400);
      const body = JSON.parse(result.body);
      expect(body.error.message).toBe('Missing stripe signature');
      expect(body.error.type).toBe('VALIDATION_ERROR');
    });

    it('should return 400 when body is missing', async () => {
      const event = createMockEvent('', 'signature');
      event.body = null;
      
      const result = await handler(event);

      expect(result.statusCode).toBe(400);
      const body = JSON.parse(result.body);
      expect(body.error.message).toBe('Missing request body');
      expect(body.error.type).toBe('VALIDATION_ERROR');
    });

    it('should return 400 when signature verification fails', async () => {
      const mockError = new Error('Invalid signature');
      mockError.name = 'StripeSignatureVerificationError';
      mockConstructEvent.mockImplementationOnce(() => {
        throw mockError;
      });

      const event = createMockEvent('test body', 'invalid_signature');
      const result = await handler(event);

      expect(result.statusCode).toBe(400);
      const body = JSON.parse(result.body);
      expect(body.error.message).toBe('Invalid signature');
      expect(body.error.type).toBe('VALIDATION_ERROR');
    });
  });

  describe('Event handling', () => {
    it('should handle checkout.session.completed successfully', async () => {
      const sessionData = {
        id: 'cs_test_123',
        payment_status: 'paid',
        amount_total: 2999,
        currency: 'usd',
        customer_details: {
          email: 'test@example.com',
        },
        metadata: {
          userId: 'user_123',
          itemCount: '2',
          items: JSON.stringify([
            { sku: 'SMALL', quantity: 1 },
            { sku: 'MEDIUM', quantity: 1 },
          ]),
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.received).toBe(true);

      // Verify EventBridge was called
      expect(mockSend).toHaveBeenCalledWith(
        expect.objectContaining({
          Entries: [
            expect.objectContaining({
              Source: 'petplantr.payments',
              DetailType: 'ORDER_PAID',
              EventBusName: 'petplantr-test',
              Detail: expect.stringContaining('"sessionId":"cs_test_123"'),
            }),
          ],
        })
      );
    });

    it('should ignore non-paid checkout sessions', async () => {
      const sessionData = {
        id: 'cs_test_123',
        payment_status: 'unpaid',
        metadata: {
          userId: 'user_123',
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(200);
      // EventBridge should not be called for unpaid sessions
      expect(mockSend).not.toHaveBeenCalled();
    });

    it('should ignore non-target event types', async () => {
      const stripeEvent = mockStripeEvent('payment_intent.created', {});
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.received).toBe(true);

      // EventBridge should not be called for other event types
      expect(mockSend).not.toHaveBeenCalled();
    });
  });

  describe('Error handling', () => {
    it('should return 500 when EventBridge fails', async () => {
      const sessionData = {
        id: 'cs_test_123',
        payment_status: 'paid',
        metadata: {
          userId: 'user_123',
          itemCount: '1',
          items: JSON.stringify([{ sku: 'SMALL', quantity: 1 }]),
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      // Mock EventBridge failure
      mockSend.mockRejectedValueOnce(new Error('EventBridge error'));

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(500);
      const body = JSON.parse(result.body);
      expect(body.error.message).toBe('Internal server error');
      expect(body.error.type).toBe('INTERNAL_ERROR');

      // Verify Slack alert was sent
      expect(fetch).toHaveBeenCalledWith(
        'https://hooks.slack.com/test',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('should handle missing userId in metadata', async () => {
      const sessionData = {
        id: 'cs_test_123',
        payment_status: 'paid',
        metadata: {
          // Missing userId
          itemCount: '1',
          items: JSON.stringify([{ sku: 'SMALL', quantity: 1 }]),
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(500);
      const body = JSON.parse(result.body);
      expect(body.error.message).toBe('Internal server error');
      expect(body.error.type).toBe('INTERNAL_ERROR');
    });
  });

  describe('EventBridge integration', () => {
    it('should send correct event payload to EventBridge', async () => {
      const sessionData = {
        id: 'cs_test_123',
        payment_status: 'paid',
        amount_total: 1599,
        currency: 'usd',
        customer_details: {
          email: 'customer@example.com',
        },
        metadata: {
          userId: 'user_456',
          itemCount: '1',
          items: JSON.stringify([{ sku: 'SMALL', quantity: 1 }]),
          sku: 'pet-planter-small', // Use actual SKU that maps to SMALL
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      await handler(event);

      // Extract the Detail from the EventBridge call
      const eventBridgeCall = mockSend.mock.calls[0][0];
      const detail = JSON.parse(eventBridgeCall.Entries[0].Detail);

      expect(detail).toEqual({
        orderId: expect.stringMatching(/^pp_\d{8}_[a-z0-9]{5}$/),
        sessionId: 'cs_test_123',
        userId: 'user_456',
        sku: 'SMALL',
        sizeTier: 'SMALL',
        photoKeys: [],
        amountPaid: 1599,
        currency: 'usd',
        customerEmail: 'customer@example.com',
        timestamp: expect.any(String),
      });
    });

    it('should emit ORDER_PAID event with correct schema when payment succeeds', async () => {
      const sessionData = {
        id: 'cs_live_12345',
        payment_status: 'paid',
        amount_total: 2500,
        currency: 'usd',
        customer_details: {
          email: 'customer@example.com',
        },
        metadata: {
          userId: 'clerk_user_123',
          photoUrls: 'clerk_user_123/1721670432000_front.jpg,clerk_user_123/1721670432000_side.jpg',
          sku: 'pet-planter-medium',
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(200);

      // Verify EventBridge was called with correct event structure
      expect(mockSend).toHaveBeenCalledWith(
        expect.objectContaining({
          Entries: [
            expect.objectContaining({
              Source: 'petplantr.payments',
              DetailType: 'ORDER_PAID',
              EventBusName: 'petplantr-test',
            }),
          ],
        })
      );

      // Parse the detail to verify the schema matches TASK 8 requirements
      const putEventsCall = mockSend.mock.calls.find(call => 
        call[0]?.Entries?.[0]?.DetailType === 'ORDER_PAID'
      );
      expect(putEventsCall).toBeDefined();

      const eventDetail = JSON.parse(putEventsCall[0].Entries[0].Detail);
      
      // Verify required fields from TASK 8 schema
      expect(eventDetail).toHaveProperty('orderId');
      expect(eventDetail.orderId).toMatch(/^pp_\d{8}_[a-z0-9]{5}$/);
      expect(eventDetail).toHaveProperty('userId', 'clerk_user_123');
      expect(eventDetail).toHaveProperty('sku', 'MEDIUM');
      expect(eventDetail).toHaveProperty('sizeTier', 'MEDIUM');
      expect(eventDetail).toHaveProperty('sessionId', 'cs_live_12345');
      expect(eventDetail).toHaveProperty('photoKeys');
      expect(eventDetail.photoKeys).toEqual([
        'clerk_user_123/1721670432000_front.jpg',
        'clerk_user_123/1721670432000_side.jpg'
      ]);
      
      // Verify additional metadata
      expect(eventDetail).toHaveProperty('amountPaid', 2500);
      expect(eventDetail).toHaveProperty('currency', 'usd');
      expect(eventDetail).toHaveProperty('customerEmail', 'customer@example.com');
      expect(eventDetail).toHaveProperty('timestamp');
    });

    it('should handle missing photoUrls gracefully', async () => {
      const sessionData = {
        id: 'cs_live_12345',
        payment_status: 'paid',
        metadata: {
          userId: 'clerk_user_123',
          sku: 'pet-planter-small',
          // photoUrls missing
        },
      };

      const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
      mockConstructEvent.mockReturnValue(stripeEvent);

      const event = createMockEvent(JSON.stringify(stripeEvent));
      const result = await handler(event);

      expect(result.statusCode).toBe(200);

      const putEventsCall = mockSend.mock.calls.find(call => 
        call[0]?.Entries?.[0]?.DetailType === 'ORDER_PAID'
      );
      const eventDetail = JSON.parse(putEventsCall[0].Entries[0].Detail);
      
      expect(eventDetail.photoKeys).toEqual([]);
      expect(eventDetail.sku).toBe('SMALL');
      expect(eventDetail.sizeTier).toBe('SMALL');
    });

    it('should map SKUs to correct size tiers', async () => {
      const testCases = [
        { sku: 'pet-planter-basic', expectedSizeTier: 'SMALL' },
        { sku: 'pet-planter-small', expectedSizeTier: 'SMALL' },
        { sku: 'pet-planter-medium', expectedSizeTier: 'MEDIUM' },
        { sku: 'pet-planter-large', expectedSizeTier: 'LARGE' },
        { sku: 'unknown-sku', expectedSizeTier: 'MEDIUM' }, // default
      ];

      for (const testCase of testCases) {
        // Clear previous mocks
        mockSend.mockClear();

        const sessionData = {
          id: 'cs_live_12345',
          payment_status: 'paid',
          metadata: {
            userId: 'clerk_user_123',
            sku: testCase.sku,
          },
        };

        const stripeEvent = mockStripeEvent('checkout.session.completed', sessionData);
        mockConstructEvent.mockReturnValue(stripeEvent);

        const event = createMockEvent(JSON.stringify(stripeEvent));
        await handler(event);

        const putEventsCall = mockSend.mock.calls.find(call => 
          call[0]?.Entries?.[0]?.DetailType === 'ORDER_PAID'
        );
        const eventDetail = JSON.parse(putEventsCall[0].Entries[0].Detail);
        
        expect(eventDetail.sku).toBe(testCase.expectedSizeTier);
        expect(eventDetail.sizeTier).toBe(testCase.expectedSizeTier);
      }
    });
  });
});
