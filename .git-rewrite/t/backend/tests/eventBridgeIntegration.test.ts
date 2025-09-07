// Mock functions first
const mockSend = jest.fn();
const mockConstructEvent = jest.fn();

// Mock EventBridge
jest.mock('@aws-sdk/client-eventbridge', () => ({
  EventBridgeClient: jest.fn(() => ({
    send: mockSend,
  })),
  PutEventsCommand: jest.fn((input) => ({ input })),
}));

// Mock Stripe
jest.mock('stripe', () => {
  return jest.fn().mockImplementation(() => ({
    webhooks: {
      constructEvent: mockConstructEvent,
    },
  }));
});

import { handler } from '../src/lambdas/stripeWebhook';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import Stripe from 'stripe';

// Mock environment variables
process.env.STRIPE_SECRET_KEY = 'sk_test_123';
process.env.STRIPE_WEBHOOK_SECRET = 'whsec_123';
process.env.EVENT_BUS_NAME = 'petplantr-test-bus';

describe('EventBridge Integration Tests for TASK 8', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock EventBridge client responses
    mockSend.mockResolvedValue({ FailedEntryCount: 0 });

    // Set environment variables
    process.env.STRIPE_SECRET_KEY = 'sk_test_123';
    process.env.STRIPE_WEBHOOK_SECRET = 'whsec_123';
    process.env.EVENT_BUS_NAME = 'petplantr-test-bus';
  });

  it('should emit ORDER_PAID event with exact schema for TASK 8', async () => {
    // Setup: Mock successful webhook verification
    const mockSession = {
      id: 'cs_live_xxxxxx',
      payment_status: 'paid',
      amount_total: 2999,
      currency: 'usd',
      customer_details: {
        email: 'customer@example.com',
      },
      metadata: {
        userId: 'clerk_user_123',
        photoUrls: 'clerk_user_123/1721670432000_front.jpg,clerk_user_123/1721670432000_side.jpg',
        sku: 'pet-planter-medium',
        photoCount: '2',
      },
    } as unknown as Stripe.Checkout.Session;

    const mockStripeEvent = {
      id: 'evt_test_123',
      type: 'checkout.session.completed',
      data: { object: mockSession },
      created: 1640995200,
      livemode: false,
      object: 'event',
      api_version: '2023-10-16',
      pending_webhooks: 1,
      request: null,
    } as unknown as Stripe.Event;

    mockConstructEvent.mockReturnValue(mockStripeEvent);

    // Execute
    const event = {
      headers: { 'stripe-signature': 'valid_signature' },
      body: JSON.stringify(mockStripeEvent),
      requestContext: {
        identity: {
          sourceIp: '127.0.0.1'
        }
      }
    };

    await handler(event as any);

    // Verify: EventBridge was called with exact TASK 8 schema
    expect(mockSend).toHaveBeenCalledTimes(1);
    
    const putEventsCall = mockSend.mock.calls[0][0];
    const eventEntry = putEventsCall.input.Entries[0];

    // Verify event structure matches TASK 8 requirements
    expect(eventEntry.Source).toBe('petplantr.payments');
    expect(eventEntry.DetailType).toBe('ORDER_PAID');
    expect(eventEntry.EventBusName).toBe('petplantr-test-bus');

    // Parse and verify the detail payload
    const detail = JSON.parse(eventEntry.Detail);
    
    // Verify required fields from TASK 8 schema
    expect(detail).toMatchObject({
      orderId: expect.stringMatching(/^pp_\d{8}_[a-z0-9]{5}$/),
      userId: 'clerk_user_123',
      sku: 'MEDIUM', // Size tier mapped from metadata
      sizeTier: 'MEDIUM',
      photoKeys: [
        'clerk_user_123/1721670432000_front.jpg',
        'clerk_user_123/1721670432000_side.jpg'
      ],
      sessionId: 'cs_live_xxxxxx',
    });

    // Verify additional metadata is preserved
    expect(detail.amountPaid).toBe(2999);
    expect(detail.currency).toBe('usd');
    expect(detail.customerEmail).toBe('customer@example.com');
    expect(detail.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/);
  });

  it('should map different SKUs to correct size tiers', async () => {
    const testCases = [
      { sku: 'pet-planter-small', expectedSizeTier: 'SMALL' },
      { sku: 'pet-planter-medium', expectedSizeTier: 'MEDIUM' },
      { sku: 'pet-planter-large', expectedSizeTier: 'LARGE' },
      { sku: 'unknown-sku', expectedSizeTier: 'MEDIUM' }, // Default
    ];

    for (const testCase of testCases) {
      jest.clearAllMocks();

      const mockSession = {
        id: 'cs_test_123',
        payment_status: 'paid',
        metadata: {
          userId: 'clerk_user_123',
          photoUrls: 'user123/photo1.jpg',
          sku: testCase.sku,
        },
      } as unknown as Stripe.Checkout.Session;

      const mockStripeEvent = {
        id: 'evt_test_123',
        type: 'checkout.session.completed',
        data: { object: mockSession },
        created: Math.floor(Date.now() / 1000)
      } as unknown as Stripe.Event;

      mockConstructEvent.mockReturnValue(mockStripeEvent);

      const event = {
        headers: { 'stripe-signature': 'valid_signature' },
        body: JSON.stringify(mockStripeEvent),
        requestContext: {
          identity: {
            sourceIp: '127.0.0.1'
          }
        }
      };

      await handler(event as any);

      const putEventsCall = mockSend.mock.calls[0][0];
      const detail = JSON.parse(putEventsCall.input.Entries[0].Detail);

      expect(detail.sku).toBe(testCase.expectedSizeTier);
      expect(detail.sizeTier).toBe(testCase.expectedSizeTier);
    }
  });

  it('should handle missing photo URLs gracefully', async () => {
    const mockSession = {
      id: 'cs_test_123',
      payment_status: 'paid',
      metadata: {
        userId: 'clerk_user_123',
        sku: 'pet-planter-medium',
        // photoUrls missing
      },
    } as unknown as Stripe.Checkout.Session;

    const mockStripeEvent = {
      id: 'evt_test_123',
      type: 'checkout.session.completed',
      data: { object: mockSession },
      created: Math.floor(Date.now() / 1000)
    } as unknown as Stripe.Event;

    mockConstructEvent.mockReturnValue(mockStripeEvent);

    const event = {
      headers: { 'stripe-signature': 'valid_signature' },
      body: JSON.stringify(mockStripeEvent),
      requestContext: {
        identity: {
          sourceIp: '127.0.0.1'
        }
      }
    };

    await handler(event as any);

    const putEventsCall = mockSend.mock.calls[0][0];
    const detail = JSON.parse(putEventsCall.input.Entries[0].Detail);

    expect(detail.photoKeys).toEqual([]);
  });

  it('should generate unique order IDs for each payment', async () => {
    const mockSession = {
      id: 'cs_test_123',
      payment_status: 'paid',
      metadata: {
        userId: 'clerk_user_123',
        sku: 'pet-planter-medium',
      },
    } as unknown as Stripe.Checkout.Session;

    const mockStripeEvent = {
      id: 'evt_test_123',
      type: 'checkout.session.completed',
      data: { object: mockSession },
      created: Math.floor(Date.now() / 1000)
    } as unknown as Stripe.Event;

    mockConstructEvent.mockReturnValue(mockStripeEvent);

    const event = {
      headers: { 'stripe-signature': 'valid_signature' },
      body: JSON.stringify(mockStripeEvent),
      requestContext: {
        identity: {
          sourceIp: '127.0.0.1'
        }
      }
    };

    // Call twice to verify unique IDs
    await handler(event as any);
    await handler(event as any);

    expect(mockSend).toHaveBeenCalledTimes(2);

    const call1Detail = JSON.parse(mockSend.mock.calls[0][0].input.Entries[0].Detail);
    const call2Detail = JSON.parse(mockSend.mock.calls[1][0].input.Entries[0].Detail);

    expect(call1Detail.orderId).not.toBe(call2Detail.orderId);
    expect(call1Detail.orderId).toMatch(/^pp_\d{8}_[a-z0-9]{5}$/);
    expect(call2Detail.orderId).toMatch(/^pp_\d{8}_[a-z0-9]{5}$/);
  });
});
