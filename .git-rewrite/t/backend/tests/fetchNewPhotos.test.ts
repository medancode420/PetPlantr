import { handler } from '../src/lambdas/fetchNewPhotos'
import { Context, EventBridgeEvent } from 'aws-lambda'

// Mock AWS SDK v2 (which the function actually uses)
jest.mock('aws-sdk', () => ({
  S3: jest.fn().mockImplementation(() => ({
    putObject: jest.fn().mockReturnValue({ 
      promise: jest.fn().mockResolvedValue({}) 
    }),
  })),
}))

// Mock Stripe
jest.mock('stripe', () => {
  const mockChargesList = jest.fn()
  return jest.fn().mockImplementation(() => ({
    charges: {
      list: mockChargesList,
    },
  }))
})

import Stripe from 'stripe'
import AWS from 'aws-sdk'

describe('fetchNewPhotos Lambda', () => {
  let mockContext: Context
  let mockChargesList: jest.Mock

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Set up environment variables for improved function
    process.env.STRIPE_SECRET_KEY = 'sk_test_123'
    process.env.S3_DATASET_BUCKET = 'test-dataset-bucket'
    
    // Get the mock through the Stripe constructor
    const StripeConstructor = Stripe as jest.MockedClass<typeof Stripe>
    const stripeInstance = new StripeConstructor('sk_test_123', { apiVersion: '2023-10-16' })
    mockChargesList = (stripeInstance as any).charges.list
    
    // Mock Lambda context
    mockContext = {
      callbackWaitsForEmptyEventLoop: false,
      functionName: 'test-function',
      functionVersion: '1',
      invokedFunctionArn: 'arn:aws:lambda:us-east-1:123456789012:function:test-function',
      memoryLimitInMB: '128',
      awsRequestId: 'test-request-id',
      logGroupName: '/aws/lambda/test-function',
      logStreamName: '2023/01/01/[$LATEST]test-stream',
      getRemainingTimeInMillis: () => 30000,
      done: jest.fn(),
      fail: jest.fn(),
      succeed: jest.fn(),
    }
  })
  
  afterEach(() => {
    // Clean up environment variables
    delete process.env.STRIPE_SECRET_KEY
    delete process.env.S3_DATASET_BUCKET
  })

  const createMockEvent = (startDate: string, endDate: string): EventBridgeEvent<'New Consented Order', { startDate: string; endDate: string; batchSize?: number }> => ({
    id: 'test-event-id',
    version: '0',
    account: '123456789012',
    time: new Date().toISOString(),
    region: 'us-east-1',
    resources: [],
    source: 'petplantr.continuous-learning',
    'detail-type': 'New Consented Order',
    detail: { startDate, endDate, batchSize: 50 }
  })

  it('should fetch consented photos from recent orders', async () => {
    // Mock Stripe to return orders with consent
    mockChargesList.mockResolvedValue({
      data: [
        {
          id: 'ch_test_123',
          created: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
          payment_intent: {
            id: 'pi_test_123',
            metadata: {
              improvement_consent: 'true',
              photo_url: 'https://example.com/photo1.jpg',
              pet_name: 'Buddy',
              photo_quality_score: '8.5',
              consent_timestamp: new Date().toISOString(),
              print_size: 'medium',
              print_color: 'standard',
              plant_type: 'succulent',
              drainage: 'true'
            }
          }
        }
      ]
    })

    // S3 operations are already mocked to resolve

    const startDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    const endDate = new Date().toISOString()
    const event = createMockEvent(startDate, endDate)

    const result = await handler(event, mockContext)

    expect(result.totalPhotos).toBeGreaterThanOrEqual(0)
    expect(result.validPhotos).toBeGreaterThanOrEqual(0)
    expect(mockChargesList).toHaveBeenCalled()
  })

  it('should skip orders without consent', async () => {
    // Mock Stripe to return orders without consent
    mockChargesList.mockResolvedValue({
      data: [
        {
          id: 'ch_test_456',
          created: Math.floor(Date.now() / 1000) - 3600,
          payment_intent: {
            id: 'pi_test_456',
            metadata: {
              improvement_consent: 'false',
              photo_url: 'https://example.com/photo3.jpg',
              pet_name: 'Max'
            }
          }
        }
      ]
    })

    const startDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    const endDate = new Date().toISOString()
    const event = createMockEvent(startDate, endDate)

    const result = await handler(event, mockContext)

    expect(result.totalPhotos).toBe(0)
    expect(result.validPhotos).toBe(0)
  })

  it('should handle Stripe API errors gracefully', async () => {
    mockChargesList.mockRejectedValue(new Error('Stripe API error'))

    const startDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    const endDate = new Date().toISOString()
    const event = createMockEvent(startDate, endDate)

    await expect(handler(event, mockContext)).rejects.toThrow('Stripe API error')
  })
})
