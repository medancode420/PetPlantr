import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda'
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { withErrorHandling, ValidationError } from '../utils/enhancedErrorHandler'
import { logger } from '../utils/enhancedLogger'
import { validateInput, lambdaSchemas } from '../utils/validation'

const s3Client = new S3Client({ region: process.env.AWS_REGION })

interface PresignRequest {
  fileName: string
  fileType: string
  fileSize: number
}

const presignUploadHandler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  const correlationId = `presign_${Date.now()}_${Math.random().toString(36).slice(2)}`
  
  logger.info('Presign upload request', {
    correlationId,
    httpMethod: event.httpMethod,
    userAgent: event.headers?.['User-Agent'],
    sourceIp: event.requestContext?.identity?.sourceIp
  });

  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json',
    'X-Correlation-ID': correlationId
  }

  // Handle preflight CORS
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: '',
    }
  }

  // Validate request body
  if (!event.body) {
    throw new ValidationError('Request body is required')
  }

  let requestData: PresignRequest
  try {
    requestData = JSON.parse(event.body)
  } catch (error) {
    throw new ValidationError('Invalid JSON in request body')
  }

  // Validate using Joi schema
  const validatedData = validateInput(requestData, lambdaSchemas.presignUpload)

  const { fileName, fileType, fileSize } = validatedData

  // Extract user ID from authorization header (Clerk JWT)
  const authHeader = event.headers.Authorization || event.headers.authorization
  if (!authHeader) {
    return {
      statusCode: 401,
      headers,
      body: JSON.stringify({
        error: 'Authorization header is required',
      }),
    }
  }

  // For now, we'll extract userId from a simple format
  // In production, you'd validate the Clerk JWT properly
  const userId = extractUserIdFromAuth(authHeader)
  if (!userId) {
    return {
      statusCode: 401,
      headers,
      body: JSON.stringify({
        error: 'Invalid authorization token',
      }),
    }
  }

  // Generate unique key with timestamp and random suffix
  const timestamp = Date.now()
  const randomSuffix = Math.random().toString(36).substring(2, 8)
  const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9.-]/g, '_')
  const key = `${userId}/${timestamp}-${randomSuffix}-${sanitizedFileName}`

  // Create the S3 command
  const command = new PutObjectCommand({
    Bucket: process.env.UPLOAD_BUCKET!,
    Key: key,
    ContentType: `image/${fileType}`,
    ACL: 'private',
    Metadata: {
      userId,
      originalFileName: fileName,
      uploadedAt: new Date().toISOString(),
    },
  })

  // Generate presigned URL (15 minutes expiry)
  const presignedUrl = await getSignedUrl(s3Client, command, { 
    expiresIn: 900 // 15 minutes
  })

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({
      uploadUrl: presignedUrl,
      key,
      bucket: process.env.UPLOAD_BUCKET,
      expiresIn: 900,
    }),
  }

}

// Simple function to extract userId from auth header
// In production, use proper Clerk JWT validation
function extractUserIdFromAuth(authHeader: string): string | null {
  try {
    // Remove 'Bearer ' prefix if present
    const token = authHeader.replace(/^Bearer\s+/i, '')
    
    // For demo purposes, we'll accept a simple format like "user_123"
    // In production, decode and validate the Clerk JWT
    if (token.startsWith('user_')) {
      return token
    }
    
    // If it's a JWT, you'd decode it here
    // const decoded = jwt.verify(token, clerkPublicKey)
    // return decoded.sub
    
    return null
  } catch (error) {
    console.error('Error extracting user ID:', error)
    return null
  }
}

export const handler = withErrorHandling(presignUploadHandler)
