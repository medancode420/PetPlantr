// Mock console.log to avoid noise in tests
jest.spyOn(console, 'log').mockImplementation(() => {});
jest.spyOn(console, 'error').mockImplementation(() => {});

// Mock AWS SDK
jest.mock('@aws-sdk/client-sns', () => {
  const mockSend = jest.fn();
  return {
    SNSClient: jest.fn(() => ({
      send: mockSend,
    })),
    PublishCommand: jest.fn(),
    __mockSend: mockSend,
  };
});

import { handler } from '../src/lambdas/notifyPrinter';

describe('notifyPrinter Lambda', () => {
  const mockSNS = require('@aws-sdk/client-sns');
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockSNS.__mockSend.mockClear();
    process.env.PRINT_QUEUE_TOPIC_ARN = 'arn:aws:sns:us-east-1:123456789012:print-queue-topic';
    process.env.REGION = 'us-east-1';
    process.env.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/TEST';
  });

  it('should return correct output format', async () => {
    const event = {
      orderId: 'pp_20250128_abc12',
      userId: 'user-456',
      readyStlKey: 'orders/pp_20250128_abc12/processed.stl',
      sizeTier: 'MEDIUM'
    };

    mockSNS.__mockSend.mockResolvedValueOnce({
      MessageId: 'test-message-id'
    });

    const result = await handler(event);

    expect(result.orderId).toBe('pp_20250128_abc12');
    expect(result.printJobId).toMatch(/^print-pp_20250128_abc12-/);
    expect(result.status).toBe('QUEUED');
    expect(result.queuedAt).toBeDefined();
  });

  it('should handle missing required fields', async () => {
    const event = {
      orderId: 'pp_20250128_abc789',
      userId: 'user-123',
      // Missing readyStlKey
      sizeTier: 'A'
    };

    try {
      await handler(event as any);
      fail('Expected handler to throw error');
    } catch (error: any) {
      expect(error.message).toContain('Invalid input data');
      expect(error.name).toBe('ValidationError');
    }
  });

  it('should handle missing environment variables', async () => {
    delete process.env.PRINT_QUEUE_TOPIC_ARN;

    const event = {
      orderId: 'pp_20250128_abc12',
      userId: 'user-456',
      readyStlKey: 'orders/pp_20250128_abc12/processed.stl',
      sizeTier: 'MEDIUM'
    };

    try {
      await handler(event);
      fail('Expected handler to throw error');
    } catch (error: any) {
      expect(error.message).toContain('PRINT_QUEUE_TOPIC_ARN environment variable not set');
      expect(error.name).toBe('ValidationError');
    }
  });
});
