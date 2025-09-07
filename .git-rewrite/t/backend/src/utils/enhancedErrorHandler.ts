/**
 * Enhanced Error Handling System
 * Provides centralized error handling with proper logging and monitoring
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult, Context } from 'aws-lambda';

export interface ApiError extends Error {
  statusCode?: number;
  code?: string;
  details?: any;
  correlationId?: string;
}

export class ValidationError extends Error implements ApiError {
  statusCode = 400;
  code = 'VALIDATION_ERROR';
  
  constructor(message: string, public details?: any) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class BusinessLogicError extends Error implements ApiError {
  statusCode = 422;
  code = 'BUSINESS_LOGIC_ERROR';
  
  constructor(message: string, public details?: any) {
    super(message);
    this.name = 'BusinessLogicError';
  }
}

export class ExternalServiceError extends Error implements ApiError {
  statusCode = 502;
  code = 'EXTERNAL_SERVICE_ERROR';
  
  constructor(message: string, public details?: any) {
    super(message);
    this.name = 'ExternalServiceError';
  }
}

export class AuthenticationError extends Error implements ApiError {
  statusCode = 401;
  code = 'AUTHENTICATION_ERROR';
  
  constructor(message: string = 'Authentication required') {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends Error implements ApiError {
  statusCode = 403;
  code = 'AUTHORIZATION_ERROR';
  
  constructor(message: string = 'Insufficient permissions') {
    super(message);
    this.name = 'AuthorizationError';
  }
}

// Enhanced error handler for Lambda functions
export const handleLambdaError = (
  error: unknown,
  event: APIGatewayProxyEvent,
  context: Context
): APIGatewayProxyResult => {
  const correlationId = event.headers['x-correlation-id'] || context.awsRequestId;
  
  // Log error with context
  console.error('Lambda Error:', {
    error: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    correlationId,
    functionName: context.functionName,
    path: event.path,
    method: event.httpMethod,
    userAgent: event.headers?.['User-Agent'],
    sourceIp: event.requestContext?.identity?.sourceIp || 'unknown',
    timestamp: new Date().toISOString()
  });

  // Handle different error types
  if (error instanceof ValidationError) {
    return {
      statusCode: error.statusCode,
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      },
      body: JSON.stringify({
        success: false,
        error: {
          type: error.code,
          message: error.message,
          details: error.details
        },
        correlationId,
        timestamp: new Date().toISOString()
      })
    };
  }

  if (error instanceof BusinessLogicError) {
    return {
      statusCode: error.statusCode,
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      },
      body: JSON.stringify({
        success: false,
        error: {
          type: error.code,
          message: error.message,
          details: error.details
        },
        correlationId,
        timestamp: new Date().toISOString()
      })
    };
  }

  if (error instanceof ExternalServiceError) {
    return {
      statusCode: error.statusCode,
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      },
      body: JSON.stringify({
        success: false,
        error: {
          type: error.code,
          message: 'External service temporarily unavailable',
          retryAfter: 60
        },
        correlationId,
        timestamp: new Date().toISOString()
      })
    };
  }

  if (error instanceof AuthenticationError || error instanceof AuthorizationError) {
    return {
      statusCode: error.statusCode,
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': correlationId
      },
      body: JSON.stringify({
        success: false,
        error: {
          type: error.code,
          message: error.message
        },
        correlationId,
        timestamp: new Date().toISOString()
      })
    };
  }

  // Generic error handling
  const isDevelopment = process.env.NODE_ENV === 'development';
  const statusCode = 500;
  const message = isDevelopment 
    ? (error instanceof Error ? error.message : String(error))
    : 'Internal server error';

  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'X-Correlation-ID': correlationId
    },
    body: JSON.stringify({
      success: false,
      error: {
        type: 'INTERNAL_ERROR',
        message,
        ...(isDevelopment && error instanceof Error && { 
          stack: error.stack,
          details: error
        })
      },
      correlationId,
      timestamp: new Date().toISOString()
    })
  };
};

// Wrapper for Lambda functions with error handling
export const withErrorHandling = (
  handler: (event: APIGatewayProxyEvent, context: Context) => Promise<APIGatewayProxyResult>
) => {
  return async (event: APIGatewayProxyEvent, context?: Context): Promise<APIGatewayProxyResult> => {
    // Provide default context for testing
    const defaultContext: Context = {
      callbackWaitsForEmptyEventLoop: false,
      functionName: 'test-function',
      functionVersion: '$LATEST',
      invokedFunctionArn: 'arn:aws:lambda:us-east-1:123456789012:function:test-function',
      memoryLimitInMB: '128',
      awsRequestId: `test-${Date.now()}`,
      logGroupName: '/aws/lambda/test-function',
      logStreamName: '2025/07/28/[$LATEST]test',
      getRemainingTimeInMillis: () => 30000,
      done: () => {},
      fail: () => {},
      succeed: () => {}
    };

    const lambdaContext = context || defaultContext;

    try {
      return await handler(event, lambdaContext);
    } catch (error) {
      return handleLambdaError(error, event, lambdaContext);
    }
  };
};
