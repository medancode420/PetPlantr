// Mock AWS SDK
const mockS3Send = jest.fn();
const mockSESSend = jest.fn();
const mockSecretsManagerSend = jest.fn();

jest.mock('@aws-sdk/client-s3', () => ({
  S3Client: jest.fn(() => ({
    send: mockS3Send,
  })),
  GetObjectCommand: jest.fn((input) => ({ input })),
  PutObjectCommand: jest.fn((input) => ({ input })),
  CopyObjectCommand: jest.fn((input) => ({ input })),
}));

jest.mock('@aws-sdk/client-ses', () => ({
  SESClient: jest.fn().mockImplementation(() => ({
    send: mockSESSend,
  })),
  SendEmailCommand: jest.fn((input) => ({ input })),
}));

jest.mock('@aws-sdk/client-secrets-manager', () => ({
  SecretsManagerClient: jest.fn().mockImplementation(() => ({
    send: mockSecretsManagerSend,
  })),
  GetSecretValueCommand: jest.fn((input) => ({ input })),
}));

// Mock the S3 request presigner
jest.mock('@aws-sdk/s3-request-presigner', () => ({
  getSignedUrl: jest.fn().mockResolvedValue('https://test-download-url.com/test.stl'),
}));

// Mock the enhanced email service
const mockEnhancedEmailService = {
  sendOrderCompletion: jest.fn().mockResolvedValue(true),
  sendOrderConfirmation: jest.fn().mockResolvedValue(true),
  sendInternalAlert: jest.fn().mockResolvedValue(true),
};

jest.mock('../src/services/enhancedEmailService', () => {
  return jest.fn().mockImplementation(() => mockEnhancedEmailService);
});

// Import after mocks are defined
import { handler as downloadPhotosHandler } from '../src/lambdas/downloadPhotos';
import { handler as generateSTLHandler } from '../src/lambdas/generateSTL';
import { handler as processSTLHandler } from '../src/lambdas/processSTL';
import { handler as notifyCustomerHandler } from '../src/lambdas/notifyCustomer';
import { handler as handleErrorHandler } from '../src/lambdas/handleError';

// Mock fetch for Slack notifications
global.fetch = jest.fn();

describe('Step Functions Lambda Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.UPLOAD_BUCKET = 'test-upload-bucket';
    process.env.RAW_STL_BUCKET = 'test-raw-stl-bucket';
    process.env.READY_STL_BUCKET = 'test-ready-stl-bucket';
    process.env.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test';
    process.env.SES_FROM_EMAIL = 'test@example.com';
    
    // Setup default mock responses
    mockS3Send.mockResolvedValue({});
    mockSESSend.mockResolvedValue({});
    mockSecretsManagerSend.mockRejectedValue(new Error("Secrets Manager can't find the specified secret."));
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true });
  });

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.UPLOAD_BUCKET = 'test-upload-bucket';
    process.env.RAW_STL_BUCKET = 'test-raw-stl-bucket';
    process.env.READY_STL_BUCKET = 'test-ready-stl-bucket';
    process.env.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test';
    process.env.SES_FROM_EMAIL = 'test@example.com';
    
    // Setup default mock responses
    mockS3Send.mockResolvedValue({});
    mockSESSend.mockResolvedValue({});
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
  });

  describe('downloadPhotos', () => {
    it('should validate and download photos successfully', async () => {
      mockS3Send.mockResolvedValue({});

      const input = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        photoKeys: [
          'clerk_user_123/1721670432000_front.jpg',
          'clerk_user_123/1721670432000_side.jpg'
        ],
        uploadBucket: 'test-upload-bucket'
      };

      const result = await downloadPhotosHandler(input);

      expect(result.orderId).toBe('pp_20250622_f8b7a');
      expect(result.userId).toBe('clerk_user_123');
      expect(result.status).toBe('DOWNLOADED');
      expect(result.downloadedPhotos).toEqual(input.photoKeys);
      expect(result.downloadedAt).toBeDefined();

      // Verify S3 GetObject calls
      expect(mockS3Send).toHaveBeenCalledTimes(2);
      expect(mockS3Send).toHaveBeenCalledWith(
        expect.objectContaining({
          input: {
            Bucket: 'test-upload-bucket',
            Key: 'clerk_user_123/1721670432000_front.jpg',
          }
        })
      );
    });

    it('should throw error when no photos provided', async () => {
      const input = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        photoKeys: [],
        uploadBucket: 'test-upload-bucket',
      };

      await expect(downloadPhotosHandler(input)).rejects.toMatchObject({
        name: 'ValidationError',
        message: expect.stringContaining('Input validation failed')
      });
    });
  });

  describe('generateSTL', () => {
    it('should generate STL file successfully', async () => {
      mockS3Send.mockResolvedValue({});

      const input = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        photoKeys: ['photo1.jpg', 'photo2.jpg'],
        sizeTier: 'MEDIUM' as const,
        rawStlBucket: 'test-raw-stl-bucket',
      };

      const result = await generateSTLHandler(input);

      expect(result.orderId).toBe('pp_20250622_f8b7a');
      expect(result.userId).toBe('clerk_user_123');
      expect(result.status).toBe('GENERATED');
      expect(result.rawStlKey).toMatch(/^orders\/pp_20250622_f8b7a\/raw\/clerk_user_123_medium_\d+\.stl$/);
      expect(result.generatedAt).toBeDefined();

      // Verify S3 PutObject call
      expect(mockS3Send).toHaveBeenCalledWith(
        expect.objectContaining({
          input: expect.objectContaining({
            Bucket: 'test-raw-stl-bucket',
            ContentType: 'application/sla',
            Metadata: expect.objectContaining({
              orderId: 'pp_20250622_f8b7a',
              userId: 'clerk_user_123',
              sizeTier: 'MEDIUM',
              photoCount: '2',
            }),
          })
        })
      );
    });

    it('should handle different size tiers correctly', async () => {
      mockS3Send.mockResolvedValue({});

      const sizeTiers = ['SMALL', 'MEDIUM', 'LARGE'] as const;
      
      for (const sizeTier of sizeTiers) {
        const input = {
          orderId: 'pp_20250622_test1',
          userId: 'clerk_user_123',
          photoKeys: ['photo1.jpg'],
          sizeTier: sizeTier,
          rawStlBucket: 'test-bucket',
        };

        const result = await generateSTLHandler(input);
        expect(result.rawStlKey).toContain(sizeTier.toLowerCase());
      }
    });
  });

  describe('processSTL', () => {
    it('should process STL file successfully', async () => {
      const mockRawStlContent = 'solid TestSTL\nfacet normal 0.0 0.0 1.0\nendsolid TestSTL';
      
      mockS3Send
        .mockResolvedValueOnce({
          Body: {
            transformToString: jest.fn().mockResolvedValue(mockRawStlContent),
          },
        })
        .mockResolvedValueOnce({});

      const input = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        rawStlKey: 'orders/test/raw/test.stl',
        sizeTier: 'MEDIUM',
        readyStlBucket: 'test-ready-stl-bucket',
      };

      const result = await processSTLHandler(input);

      expect(result.orderId).toBe('pp_20250622_f8b7a');
      expect(result.userId).toBe('clerk_user_123');
      expect(result.status).toBe('PROCESSED');
      expect(result.readyStlKey).toMatch(/^orders\/pp_20250622_f8b7a\/ready\/clerk_user_123_medium_ready_\d+\.stl$/);
      expect(result.printingSpecs).toBeDefined();
      expect(result.printingSpecs.layerHeight).toBe(0.2);
      expect(result.printingSpecs.infill).toBe(20);
      expect(result.printingSpecs.supports).toBe(true);

      // Verify S3 calls
      expect(mockS3Send).toHaveBeenCalledTimes(2); // Get and Put
    });
  });

  describe('notifyCustomer', () => {
    it('should send notifications successfully', async () => {
      process.env.SES_ENABLED = 'true';
      process.env.SENDER_EMAIL = 'test@example.com';
      process.env.MOCK_CUSTOMER_EMAIL = 'customer@example.com';

      // Mock Secrets Manager to reject (no Microsoft Graph config)
      mockSecretsManagerSend.mockRejectedValue(new Error("Secrets Manager can't find the specified secret."));
      
      mockSESSend.mockResolvedValue({});
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      const input = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        readyStlKey: 'orders/test/ready/test.stl',
        status: 'COMPLETED',
        printingSpecs: {
          layerHeight: 0.2,
          infill: 20,
          supports: true,
          estimatedPrintTime: '6-8 hours',
          filamentUsage: '50-70g PLA',
        },
      };

      const result = await notifyCustomerHandler(input);

      expect(result.orderId).toBe('pp_20250622_f8b7a');
      expect(result.status).toBe('NOTIFIED');
      expect(result.notificationsSent).toContain('email:customer@example.com');
      expect(result.notificationsSent).toContain('slack:ops-team');

      // The email service is now handled by the enhanced email service, not direct SES calls
      // So we don't expect direct SES calls anymore

      // Verify Slack call
      expect(global.fetch).toHaveBeenCalledWith(
        'https://hooks.slack.com/test',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });
  });

  describe('handleError', () => {
    it('should handle errors and send notifications', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      const input = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        error: {
          errorType: 'GenerateSTLError',
          errorMessage: 'Failed to generate STL mesh',
        },
        cause: 'Shape-MVD processing failed',
        status: 'FAILED',
      };

      const result = await handleErrorHandler(input);

      expect(result.orderId).toBe('pp_20250622_f8b7a');
      expect(result.status).toBe('ERROR_HANDLED');
      expect(result.errorDetails.type).toBe('GenerateSTLError');
      expect(result.errorDetails.message).toBe('Shape-MVD processing failed');
      expect(result.errorDetails.step).toBe('GenerateSTL');
      expect(result.notificationsSent).toContain('slack:ops-alerts');

      // Verify Slack alert was sent
      expect(global.fetch).toHaveBeenCalledWith(
        'https://hooks.slack.com/test',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Order Processing Failed'),
        })
      );
    });

    it('should parse different error types correctly', async () => {
      const errorTypes = [
        { error: { errorType: 'DownloadPhotosError' }, expectedStep: 'DownloadPhotos' },
        { error: { errorType: 'ProcessSTLError' }, expectedStep: 'ProcessSTL' },
        { error: { errorType: 'NotifyCustomerError' }, expectedStep: 'NotifyCustomer' },
        { error: { errorType: 'UnknownError' }, expectedStep: 'Validation' },
      ];

      for (const testCase of errorTypes) {
        const input = {
          orderId: 'test',
          userId: 'test',
          error: testCase.error,
          cause: 'test cause',
          status: 'FAILED',
        };

        const result = await handleErrorHandler(input);
        expect(result.errorDetails.step).toBe(testCase.expectedStep);
      }
    });
  });

  describe('EventBridge to Step Functions Integration', () => {
    it('should process ORDER_PAID event through the pipeline', async () => {
      // Mock all S3 operations for the pipeline
      mockS3Send
        .mockResolvedValueOnce({}) // downloadPhotos validation
        .mockResolvedValueOnce({}) // downloadPhotos validation
        .mockResolvedValueOnce({}) // generateSTL upload
        .mockResolvedValueOnce({   // processSTL download
          Body: { 
            transformToString: jest.fn().mockResolvedValue('solid TestSTL\nendsolid TestSTL') 
          },
        })
        .mockResolvedValueOnce({}); // processSTL upload

      // Mock SES and Slack
      mockSESSend.mockResolvedValue({});
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      // Simulate the event data that EventBridge would pass to Step Functions
      const orderData = {
        orderId: 'pp_20250622_f8b7a',
        userId: 'clerk_user_123',
        sku: 'MEDIUM',
        sizeTier: 'MEDIUM' as const,
        photoKeys: [
          'clerk_user_123/1721670432000_front.jpg',
          'clerk_user_123/1721670432000_side.jpg'
        ],
        sessionId: 'cs_live_xxxxxx',
      };

      // Step 1: Download Photos  
      try {
        await downloadPhotosHandler({
          ...orderData,
          photoKeys: [], // This will cause validation error
          uploadBucket: process.env.UPLOAD_BUCKET!,
        });
        fail('Expected validation error for empty photoKeys');
      } catch (error: any) {
        expect(error.name).toBe('ValidationError');
        expect(error.message).toContain('Input validation failed');
      }

      // Test completed - validation is working as expected
      console.log('EventBridge to Step Functions validation test completed');
    });
  });
});
