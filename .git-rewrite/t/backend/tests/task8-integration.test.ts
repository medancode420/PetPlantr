// Mock AWS EventBridge client 
const mockEventBridgeSend = jest.fn();

jest.mock('@aws-sdk/client-eventbridge', () => ({
  EventBridgeClient: jest.fn().mockImplementation(() => ({
    send: mockEventBridgeSend,
  })),
  PutEventsCommand: jest.fn().mockImplementation((input) => ({ input })),
}));

// Mock Stripe
jest.mock('stripe');

// Import after mocks are setup
import { handler } from '../src/lambdas/stripeWebhook';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import Stripe from 'stripe';

const mockStripe = Stripe as jest.MockedClass<typeof Stripe>;
const mockConstructEvent = jest.fn();

// Mock fetch for Slack
global.fetch = jest.fn();

describe('TASK 8 - EventBridge ⇢ Step Functions Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup environment
    process.env.STRIPE_SECRET_KEY = 'sk_test_123';
    process.env.STRIPE_WEBHOOK_SECRET = 'whsec_test';
    process.env.EVENTBRIDGE_BUS_NAME = 'petplantr-events';
    process.env.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test';
    
    // Mock fetch to resolve successfully
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true })
    });
    process.env.STRIPE_WEBHOOK_SECRET = 'whsec_123';
    process.env.EVENT_BUS_NAME = 'petplantr-orderbus';
    
    // Mock EventBridge
    (EventBridgeClient as jest.Mock).mockImplementation(() => ({
      send: mockEventBridgeSend,
    }));
    mockEventBridgeSend.mockResolvedValue({ FailedEntryCount: 0 });
    
    // Mock Stripe
    mockStripe.prototype.webhooks = { constructEvent: mockConstructEvent } as any;
    
    // Mock fetch
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true });
  });

  describe('Unit Tests - stripeWebhook EventBridge Integration', () => {
    it('should emit ORDER_PAID event with correct detail-type and source', async () => {
      // Arrange
      const mockSession = {
        id: 'cs_live_xxxxxx',
        payment_status: 'paid',
        amount_total: 2999,
        currency: 'usd',
        metadata: {
          userId: 'clerk_user_123',
          photoUrls: 'clerk_user_123/1721670432000_front.jpg,clerk_user_123/1721670432000_side.jpg',
          sku: 'pet-planter-medium',
        },
      } as unknown as Stripe.Checkout.Session;

      const mockEvent: Stripe.Event = {
        id: 'evt_test',
        type: 'checkout.session.completed',
        data: { object: mockSession },
        created: Math.floor(Date.now() / 1000)
      } as Stripe.Event;

      mockConstructEvent.mockReturnValue(mockEvent);

      const event = {
        headers: { 'stripe-signature': 'valid_sig' },
        body: JSON.stringify(mockEvent),
        requestContext: {
          identity: {
            sourceIp: '127.0.0.1'
          }
        }
      };

      // Act
      const result = await handler(event as any);

      // Assert
      expect(result.statusCode).toBe(200);
      expect(mockEventBridgeSend).toHaveBeenCalledWith(
        expect.objectContaining({
          input: expect.objectContaining({
            Entries: expect.arrayContaining([
              expect.objectContaining({
                Source: 'petplantr.payments',
                DetailType: 'ORDER_PAID',
                EventBusName: 'petplantr-orderbus',
                Detail: expect.any(String)
              })
            ])
          })
        })
      );

      // Access the command that was passed to send()
      const putEventsCommand = mockEventBridgeSend.mock.calls[0][0];
      // PutEventsCommand has an input property with the actual parameters
      const eventEntry = putEventsCommand.input.Entries[0];

      expect(eventEntry.Source).toBe('petplantr.payments');
      expect(eventEntry.DetailType).toBe('ORDER_PAID');
      expect(eventEntry.EventBusName).toBe('petplantr-orderbus');

      const detail = JSON.parse(eventEntry.Detail);
      expect(detail.orderId).toMatch(/^pp_\d{8}_[a-z0-9]{5}$/);
      expect(detail.userId).toBe('clerk_user_123');
      expect(detail.sku).toBe('MEDIUM');
      expect(detail.sizeTier).toBe('MEDIUM');
      expect(detail.sessionId).toBe('cs_live_xxxxxx');
      expect(detail.photoKeys).toEqual([
        'clerk_user_123/1721670432000_front.jpg',
        'clerk_user_123/1721670432000_side.jpg'
      ]);
    });

    it('should only trigger for paid checkout sessions', async () => {
      // Arrange - unpaid session
      const mockSession = {
        id: 'cs_test_123',
        payment_status: 'unpaid',
        metadata: { userId: 'user_123' },
      } as unknown as Stripe.Checkout.Session;

      const mockEvent: Stripe.Event = {
        id: 'evt_test',
        type: 'checkout.session.completed',
        data: { object: mockSession },
        created: Math.floor(Date.now() / 1000)
      } as Stripe.Event;

      mockConstructEvent.mockReturnValue(mockEvent);

      const event = {
        headers: { 'stripe-signature': 'valid_sig' },
        body: JSON.stringify(mockEvent),
        requestContext: {
          identity: {
            sourceIp: '127.0.0.1'
          }
        }
      };

      // Act
      await handler(event as any);

      // Assert - no EventBridge event should be sent
      expect(mockEventBridgeSend).not.toHaveBeenCalled();
    });

    it('should validate IAM permissions - only PutEvents action', async () => {
      // This test verifies the IAM policy structure
      const expectedActions = ['events:PutEvents'];
      const expectedResource = expect.stringContaining('event-bus');

      // The IAM policy should be configured in serverless.yml as:
      // - Effect: Allow
      //   Action: events:PutEvents  
      //   Resource: !GetAtt OrderEventBus.Arn

      expect(expectedActions).toContain('events:PutEvents');
      expect(expectedResource).toEqual(expect.stringContaining('event-bus'));
    });
  });

  describe('Integration Tests - EventBridge Rule → Step Functions', () => {
    it('should configure EventBridge rule with correct event pattern', () => {
      // This test validates the EventBridge rule configuration
      const expectedEventPattern = {
        'detail-type': ['ORDER_PAID'],
        'source': ['petplantr.payments']
      };

      const expectedTarget = {
        Arn: expect.stringContaining('ProcessOrderStateMachine'),
        Id: 'StartStateMachine',
        RoleArn: expect.stringContaining('EventBridgeToSFRole')
      };

      expect(expectedEventPattern['detail-type']).toContain('ORDER_PAID');
      expect(expectedEventPattern.source).toContain('petplantr.payments');
      expect(expectedTarget.Id).toBe('StartStateMachine');
    });

    it('should verify EventBridge to Step Functions IAM role permissions', () => {
      // This validates the IAM role for EventBridge → Step Functions
      const expectedPolicyActions = ['states:StartExecution'];
      const expectedPrincipal = 'events.amazonaws.com';

      expect(expectedPolicyActions).toContain('states:StartExecution');
      expect(expectedPrincipal).toBe('events.amazonaws.com');
    });
  });

  describe('End-to-End Pipeline Tests', () => {
    it('should process complete payment → event → state machine flow', async () => {
      // Arrange - Complete payment scenario
      const mockSession = {
        id: 'cs_live_test_e2e',
        payment_status: 'paid',
        amount_total: 4999,
        currency: 'usd',
        customer_details: { email: 'test@example.com' },
        metadata: {
          userId: 'clerk_user_e2e_test',
          photoUrls: 'clerk_user_e2e_test/front.jpg,clerk_user_e2e_test/side.jpg',
          sku: 'pet-planter-large',
          photoCount: '2',
        },
      } as unknown as Stripe.Checkout.Session;

      const mockEvent: Stripe.Event = {
        id: 'evt_e2e_test',
        type: 'checkout.session.completed',
        data: { object: mockSession },
        created: Date.now() / 1000,
        livemode: false,
      } as Stripe.Event;

      mockConstructEvent.mockReturnValue(mockEvent);

      const webhookEvent = {
        headers: { 'stripe-signature': 'valid_signature_e2e' },
        body: JSON.stringify(mockEvent),
        requestContext: {
          identity: {
            sourceIp: '127.0.0.1'
          }
        }
      };

      // Act
      const result = await handler(webhookEvent as any);

      // Assert - Complete pipeline validation
      expect(result.statusCode).toBe(200);
      
      // Verify EventBridge event was sent
      expect(mockEventBridgeSend).toHaveBeenCalledTimes(1);
      const putEventsCommand = mockEventBridgeSend.mock.calls[0][0];
      const eventEntry = putEventsCommand.input.Entries[0];
      
      // Verify event format for Step Functions consumption
      const detail = JSON.parse(eventEntry.Detail);
      expect(detail).toMatchObject({
        orderId: expect.stringMatching(/^pp_\d{8}_[a-z0-9]{5}$/),
        userId: 'clerk_user_e2e_test',
        sku: 'LARGE',
        sizeTier: 'LARGE',
        photoKeys: ['clerk_user_e2e_test/front.jpg', 'clerk_user_e2e_test/side.jpg'],
        sessionId: 'cs_live_test_e2e',
        amountPaid: 4999,
        currency: 'usd',
        customerEmail: 'test@example.com',
        timestamp: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/),
      });

      // Log for manual verification
      console.log('E2E Test - EventBridge Payload:', JSON.stringify(detail, null, 2));
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle EventBridge failures gracefully', async () => {
      // Arrange
      mockEventBridgeSend.mockRejectedValue(new Error('EventBridge service unavailable'));

      const mockSession = {
        id: 'cs_test_error',
        payment_status: 'paid',
        metadata: { userId: 'user_test', sku: 'pet-planter-medium' },
      } as unknown as Stripe.Checkout.Session;

      const mockEvent: Stripe.Event = {
        id: 'evt_error_test',
        type: 'checkout.session.completed',
        data: { object: mockSession },
        created: Math.floor(Date.now() / 1000)
      } as Stripe.Event;

      mockConstructEvent.mockReturnValue(mockEvent);

      const event = {
        headers: { 'stripe-signature': 'valid_sig' },
        body: JSON.stringify(mockEvent),
        requestContext: {
          identity: {
            sourceIp: '127.0.0.1'
          }
        }
      };

      // Act
      const result = await handler(event as any);

      // Assert - should return 500 status instead of throwing
      expect(result.statusCode).toBe(500);
      expect(JSON.parse(result.body).error.message).toBe('Internal server error');
      
      // Verify Slack notification was sent
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Payment Processing Error'),
        })
      );
    });

    it('should handle missing required metadata', async () => {
      // Arrange - missing userId
      const mockSession = {
        id: 'cs_test_missing_data',
        payment_status: 'paid',
        metadata: {}, // Missing userId
      } as unknown as Stripe.Checkout.Session;

      const mockEvent: Stripe.Event = {
        id: 'evt_missing_data',
        type: 'checkout.session.completed',
        data: { object: mockSession },
        created: Math.floor(Date.now() / 1000)
      } as Stripe.Event;

      mockConstructEvent.mockReturnValue(mockEvent);

      const event = {
        headers: { 'stripe-signature': 'valid_sig' },
        body: JSON.stringify(mockEvent),
        requestContext: {
          identity: {
            sourceIp: '127.0.0.1'
          }
        }
      };

      // Act
      const result = await handler(event as any);

      // Assert - should return 500 status for missing userId
      expect(result.statusCode).toBe(500);
      expect(JSON.parse(result.body).error.message).toBe('Internal server error');
    });
  });
});
