/**
 * Input Validation System
 * Provides comprehensive validation for Lambda inputs using Joi
 */

import Joi from 'joi';
import { ValidationError } from './enhancedErrorHandler';

// Common validation schemas
export const commonSchemas = {
  orderId: Joi.string().pattern(/^pp_\d{8}_[a-z0-9]{5}$/).required()
    .messages({
      'string.pattern.base': 'Order ID must follow format pp_YYYYMMDD_xxxxx'
    }),
  
  userId: Joi.string().min(1).max(100).required()
    .messages({
      'string.empty': 'User ID is required',
      'string.max': 'User ID must be less than 100 characters'
    }),
  
  email: Joi.string().email().required()
    .messages({
      'string.email': 'Must be a valid email address'
    }),
  
  sizeTier: Joi.string().valid('SMALL', 'MEDIUM', 'LARGE').required()
    .messages({
      'any.only': 'Size tier must be SMALL, MEDIUM, or LARGE'
    }),
  
  photoKeys: Joi.array().items(
    Joi.string().pattern(/^[a-zA-Z0-9_\/\-\.]+\.(jpg|jpeg|png)$/i)
  ).min(1).max(10).required()
    .messages({
      'array.min': 'At least 1 photo is required',
      'array.max': 'Maximum 10 photos allowed',
      'string.pattern.base': 'Photo keys must be valid file paths with jpg/jpeg/png extension'
    }),
  
  sessionId: Joi.string().pattern(/^cs_(live|test)_[a-zA-Z0-9]+$/).required()
    .messages({
      'string.pattern.base': 'Session ID must be a valid Stripe session ID'
    }),
  
  timestamp: Joi.date().iso().required()
    .messages({
      'date.format': 'Timestamp must be in ISO format'
    }),
  
  dateString: Joi.string().isoDate().required()
    .messages({
      'string.isoDate': 'Date must be in ISO format (YYYY-MM-DD)'
    }),
  
  batchSize: Joi.number().integer().min(1).max(1000).default(100)
    .messages({
      'number.min': 'Batch size must be at least 1',
      'number.max': 'Batch size cannot exceed 1000'
    }),
  
  s3Key: Joi.string().pattern(/^[a-zA-Z0-9_\/\-\.]+$/).required()
    .messages({
      'string.pattern.base': 'S3 key must contain only valid characters'
    }),
  
  bucket: Joi.string().pattern(/^[a-z0-9][a-z0-9\-]*[a-z0-9]$/).required()
    .messages({
      'string.pattern.base': 'Bucket name must be a valid S3 bucket name'
    })
};

// Lambda-specific validation schemas
export const lambdaSchemas = {
  // CreateCheckout validation
  createCheckout: Joi.object({
    userId: commonSchemas.userId,
    sizeTier: commonSchemas.sizeTier,
    photoKeys: commonSchemas.photoKeys,
    customerEmail: commonSchemas.email,
    successUrl: Joi.string().uri().required(),
    cancelUrl: Joi.string().uri().required()
  }),

  // PresignUpload validation
  presignUpload: Joi.object({
    fileName: Joi.string().pattern(/^[^\/\\:*?"<>|]+\.(jpg|jpeg|png|webp)$/i).required()
      .messages({
        'string.pattern.base': 'File name must be valid with jpg/jpeg/png/webp extension'
      }),
    fileType: Joi.string().valid('jpeg', 'jpg', 'png', 'webp').required(),
    fileSize: Joi.number().positive().max(10 * 1024 * 1024).required()
      .messages({
        'number.max': 'File size must be less than 10MB'
      })
  }),

  // DownloadPhotos validation
  downloadPhotos: Joi.object({
    orderId: commonSchemas.orderId,
    userId: commonSchemas.userId,
    photoKeys: commonSchemas.photoKeys,
    uploadBucket: Joi.string().required()
  }),

  // FetchNewPhotos validation
  fetchNewPhotos: Joi.object({
    startDate: commonSchemas.dateString,
    endDate: commonSchemas.dateString,
    batchSize: commonSchemas.batchSize.optional()
  }),

  // NotifyPrinter validation
  notifyPrinter: Joi.object({
    orderId: commonSchemas.orderId,
    userId: commonSchemas.userId,
    readyStlKey: commonSchemas.s3Key,
    sizeTier: commonSchemas.sizeTier,
    stlBucket: commonSchemas.bucket.optional()
  }),

  // GenerateSTL validation
  generateSTL: Joi.object({
    orderId: commonSchemas.orderId,
    userId: commonSchemas.userId,
    photoKeys: commonSchemas.photoKeys,
    sizeTier: commonSchemas.sizeTier,
    rawStlBucket: commonSchemas.bucket,
    downloadedPhotos: Joi.array().items(Joi.string()).optional()
  }),

  // ProcessSTL validation
  processSTL: Joi.object({
    orderId: commonSchemas.orderId,
    userId: commonSchemas.userId,
    rawStlKey: commonSchemas.s3Key,
    sizeTier: commonSchemas.sizeTier,
    readyStlBucket: commonSchemas.bucket
  }),

  // NotifyCustomer validation
  notifyCustomer: Joi.object({
    orderId: commonSchemas.orderId,
    userId: commonSchemas.userId,
    customerEmail: commonSchemas.email,
    readyStlKey: commonSchemas.s3Key,
    status: Joi.string().valid('COMPLETED', 'FAILED').required(),
    printingSpecs: Joi.object({
      layerHeight: Joi.number().positive().required(),
      infill: Joi.number().min(0).max(100).required(),
      supports: Joi.boolean().required(),
      estimatedPrintTime: Joi.string().required(),
      filamentUsage: Joi.string().required()
    }).optional()
  }),

  // Stripe Webhook validation
  stripeWebhook: Joi.object({
    id: Joi.string().required(),
    type: Joi.string().required(),
    data: Joi.object({
      object: Joi.object().required()
    }).required(),
    created: Joi.number().positive().required()
  }),

  // EventBridge event validation
  eventBridgeEvent: Joi.object({
    source: Joi.string().required(),
    'detail-type': Joi.string().required(),
    detail: Joi.object().required(),
    time: Joi.string().isoDate().required(),
    id: Joi.string().required(),
    account: Joi.string().required(),
    region: Joi.string().required()
  })
};

// Validation function for objects
export const validateInput = <T>(
  data: any,
  schema: Joi.ObjectSchema<T>,
  options: Joi.ValidationOptions = {}
): T => {
  const defaultOptions: Joi.ValidationOptions = {
    abortEarly: false,
    stripUnknown: true,
    convert: true,
    ...options
  };

  const { error, value } = schema.validate(data, defaultOptions);

  if (error) {
    const validationErrors = error.details.map(detail => ({
      field: detail.path.join('.'),
      message: detail.message,
      value: detail.context?.value
    }));

    throw new ValidationError('Input validation failed', {
      errors: validationErrors,
      errorCount: validationErrors.length
    });
  }

  return value;
};

// Validation function for any schema type (including primitives)
export const validateValue = <T>(
  data: any,
  schema: Joi.Schema<T>,
  options: Joi.ValidationOptions = {}
): T => {
  const defaultOptions: Joi.ValidationOptions = {
    abortEarly: false,
    stripUnknown: true,
    convert: true,
    ...options
  };

  const { error, value } = schema.validate(data, defaultOptions);

  if (error) {
    const validationErrors = error.details.map(detail => ({
      field: detail.path.join('.') || 'value',
      message: detail.message,
      value: detail.context?.value
    }));

    throw new ValidationError('Value validation failed', {
      errors: validationErrors,
      errorCount: validationErrors.length
    });
  }

  return value;
};

// Lambda event validation wrapper
export const withInputValidation = <T>(
  schema: Joi.ObjectSchema<T>
) => {
  return (handler: (validatedInput: T, event: any, context: any) => Promise<any>) => {
    return async (event: any, context: any) => {
      // Extract input based on event type
      let input: any;
      
      if (event.body) {
        // API Gateway event
        input = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
      } else if (event.detail) {
        // EventBridge event
        input = event.detail;
      } else {
        // Direct Lambda invocation
        input = event;
      }

      const validatedInput = validateInput(input, schema);
      return handler(validatedInput, event, context);
    };
  };
};

// Specific validators for common use cases
export const validators = {
  orderId: (orderId: string) => validateValue(orderId, commonSchemas.orderId),
  userId: (userId: string) => validateValue(userId, commonSchemas.userId),
  email: (email: string) => validateValue(email, commonSchemas.email),
  sizeTier: (sizeTier: string) => validateValue(sizeTier, commonSchemas.sizeTier),
  photoKeys: (photoKeys: string[]) => validateValue(photoKeys, commonSchemas.photoKeys),
  s3Key: (s3Key: string) => validateValue(s3Key, commonSchemas.s3Key)
};
