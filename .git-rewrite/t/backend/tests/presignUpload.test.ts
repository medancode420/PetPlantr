import { APIGatewayProxyEvent } from 'aws-lambda'

// Mock AWS SDK before importing the handler
jest.mock('@aws-sdk/client-s3', () => ({
  S3Client: jest.fn().mockImplementation(() => ({})),
  PutObjectCommand: jest.fn().mockImplementation((input) => ({ input }))
}))

jest.mock('@aws-sdk/s3-request-presigner', () => ({
  getSignedUrl: jest.fn()
}))

import { handler } from '../src/lambdas/presignUpload'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'

const mockGetSignedUrl = getSignedUrl as jest.MockedFunction<typeof getSignedUrl>

describe('presignUpload Lambda', () => {
  const mockEvent: Partial<APIGatewayProxyEvent> = {
    httpMethod: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer user_test123'
    },
    body: JSON.stringify({
      fileName: 'pet-photo.jpg',
      fileType: 'jpeg',
      fileSize: 1024000 // 1MB
    })
  }

  beforeEach(() => {
    jest.clearAllMocks()
    process.env.UPLOAD_BUCKET = 'test-upload-bucket'
    process.env.AWS_REGION = 'us-east-1'
    
    mockGetSignedUrl.mockResolvedValue('https://s3.amazonaws.com/presigned-url')
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('handles CORS preflight requests', async () => {
    const corsEvent = {
      ...mockEvent,
      httpMethod: 'OPTIONS'
    }

    const result = await handler(corsEvent as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(200)
    expect(result.headers).toHaveProperty('Access-Control-Allow-Origin', '*')
    expect(result.headers).toHaveProperty('Access-Control-Allow-Methods', 'POST,OPTIONS')
    expect(result.body).toBe('')
  })

  it('returns 400 when request body is missing', async () => {
    const eventWithoutBody = {
      ...mockEvent,
      body: null
    }

    const result = await handler(eventWithoutBody as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(400)
    expect(JSON.parse(result.body)).toEqual({
      success: false,
      error: {
        type: 'VALIDATION_ERROR',
        message: 'Request body is required'
      },
      correlationId: expect.any(String),
      timestamp: expect.any(String)
    })
  })

  it('returns 401 when authorization header is missing', async () => {
    const eventWithoutAuth = {
      ...mockEvent,
      headers: {
        'Content-Type': 'application/json'
      }
    }

    const result = await handler(eventWithoutAuth as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(401)
    expect(JSON.parse(result.body)).toEqual({
      error: 'Authorization header is required'
    })
  })

  it('returns 401 when authorization token is invalid', async () => {
    const eventWithInvalidAuth = {
      ...mockEvent,
      headers: {
        ...mockEvent.headers,
        'Authorization': 'Bearer invalid-token'
      }
    }

    const result = await handler(eventWithInvalidAuth as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(401)
    expect(JSON.parse(result.body)).toEqual({
      error: 'Invalid authorization token'
    })
  })

  it('validates required fields in request body', async () => {
    const eventWithIncompleteBody = {
      ...mockEvent,
      body: JSON.stringify({
        fileName: 'test.jpg'
        // missing fileType and fileSize
      })
    }

    const result = await handler(eventWithIncompleteBody as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(400)
    expect(JSON.parse(result.body)).toEqual({
      success: false,
      error: {
        type: 'VALIDATION_ERROR',
        message: 'Input validation failed',
        details: {
          errorCount: 2,
          errors: expect.arrayContaining([
            expect.objectContaining({
              field: 'fileType',
              message: expect.stringContaining('required')
            }),
            expect.objectContaining({
              field: 'fileSize', 
              message: expect.stringContaining('required')
            })
          ])
        }
      },
      correlationId: expect.any(String),
      timestamp: expect.any(String)
    })
  })

  it('validates file type restrictions', async () => {
    const eventWithInvalidFileType = {
      ...mockEvent,
      body: JSON.stringify({
        fileName: 'document.pdf',
        fileType: 'pdf',
        fileSize: 1024000
      })
    }

    const result = await handler(eventWithInvalidFileType as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(400)
    const body = JSON.parse(result.body)
    expect(body.error.details.errors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          field: 'fileType',
          message: expect.stringContaining('must be one of [jpeg, jpg, png, webp]')
        })
      ])
    )
  })

  it('validates file size limits', async () => {
    const eventWithLargeFile = {
      ...mockEvent,
      body: JSON.stringify({
        fileName: 'large-photo.jpg',
        fileType: 'jpeg',
        fileSize: 15 * 1024 * 1024 // 15MB (over 10MB limit)
      })
    }

    const result = await handler(eventWithLargeFile as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(400)
    const body = JSON.parse(result.body)
    expect(body.error.details.errors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          field: 'fileSize',
          message: expect.stringContaining('File size must be less than 10MB')
        })
      ])
    )
  })

  it('generates presigned URL successfully for valid request', async () => {
    const result = await handler(mockEvent as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(200)
    
    const responseBody = JSON.parse(result.body)
    expect(responseBody).toHaveProperty('uploadUrl', 'https://s3.amazonaws.com/presigned-url')
    expect(responseBody).toHaveProperty('key')
    expect(responseBody).toHaveProperty('bucket', 'test-upload-bucket')
    expect(responseBody).toHaveProperty('expiresIn', 900)

    // Verify the key format includes userId and timestamp
    expect(responseBody.key).toMatch(/^user_test123\/\d+-[a-z0-9]+-pet-photo\.jpg$/)
  })

  it('calls S3 with correct parameters', async () => {
    await handler(mockEvent as APIGatewayProxyEvent)

    expect(mockGetSignedUrl).toHaveBeenCalledWith(
      expect.any(Object), // S3Client instance
      expect.objectContaining({
        input: expect.objectContaining({
          Bucket: 'test-upload-bucket',
          ContentType: 'image/jpeg',
          ACL: 'private'
        })
      }),
      { expiresIn: 900 }
    )

    // Verify the command parameters
    const commandCall = mockGetSignedUrl.mock.calls[0][1]
    expect(commandCall.input).toEqual(
      expect.objectContaining({
        Bucket: 'test-upload-bucket',
        ContentType: 'image/jpeg',
        ACL: 'private',
        Metadata: expect.objectContaining({
          userId: 'user_test123',
          originalFileName: 'pet-photo.jpg'
        })
      })
    )
  })

  it('handles different file types correctly', async () => {
    const fileTypes = ['jpeg', 'jpg', 'png', 'webp']
    
    for (const fileType of fileTypes) {
      const eventWithFileType = {
        ...mockEvent,
        body: JSON.stringify({
          fileName: `test.${fileType}`,
          fileType,
          fileSize: 1024000
        })
      }

      const result = await handler(eventWithFileType as APIGatewayProxyEvent)
      expect(result.statusCode).toBe(200)
      
      // Verify content type is set correctly
      const commandCall = mockGetSignedUrl.mock.calls[mockGetSignedUrl.mock.calls.length - 1][1] as any
      expect(commandCall.input.ContentType).toBe(`image/${fileType}`)
    }
  })

  it('sanitizes file names with special characters', async () => {
    const eventWithSpecialChars = {
      ...mockEvent,
      body: JSON.stringify({
        fileName: 'my pet photo #1 (cute).jpg',
        fileType: 'jpeg',
        fileSize: 1024000
      })
    }

    const result = await handler(eventWithSpecialChars as APIGatewayProxyEvent)
    expect(result.statusCode).toBe(200)
    
    const responseBody = JSON.parse(result.body)
    // Special characters should be replaced with underscores
    expect(responseBody.key).toMatch(/my_pet_photo__1__cute_\.jpg$/)
  })

  it('handles S3 errors gracefully', async () => {
    mockGetSignedUrl.mockRejectedValue(new Error('S3 service unavailable'))

    const result = await handler(mockEvent as APIGatewayProxyEvent)

    expect(result.statusCode).toBe(500)
    expect(JSON.parse(result.body)).toEqual({
      success: false,
      error: {
        type: 'INTERNAL_ERROR',
        message: 'Internal server error'
      },
      correlationId: expect.any(String),
      timestamp: expect.any(String)
    })
  })

  it('includes CORS headers in all responses', async () => {
    const result = await handler(mockEvent as APIGatewayProxyEvent)

    expect(result.headers).toHaveProperty('Access-Control-Allow-Origin', '*')
    expect(result.headers).toHaveProperty('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    expect(result.headers).toHaveProperty('Content-Type', 'application/json')
    expect(result.headers).toHaveProperty('X-Correlation-ID')
  })
})
