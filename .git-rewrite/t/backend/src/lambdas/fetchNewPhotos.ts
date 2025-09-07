/**
 * Lambda 1: Fetch New Photos
 * Retrieves consented photos from Stripe metadata for AI training dataset
 * Features:
 * - Validates and downloads customer-consented photos
 * - Performs quality checks and content validation
 * - Stores anonymized photos in S3 training dataset bucket
 * - Maintains consent compliance and data privacy
 */

import { EventBridgeEvent, Context } from 'aws-lambda';
import AWS from 'aws-sdk';
import Stripe from 'stripe';
import { logger } from '../utils/enhancedLogger';
import { ValidationError } from '../utils/enhancedErrorHandler';
import { lambdaSchemas } from '../utils/validation';

const s3 = new AWS.S3();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

// Configuration constants
const CONFIG = {
  DEFAULT_BATCH_SIZE: 100,
  MAX_BATCH_SIZE: 1000,
  MIN_QUALITY_SCORE: 0.5,
  MAX_FILE_SIZE_MB: 10,
  SUPPORTED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/webp'],
  S3_TIMEOUT_MS: 30000,
  FETCH_TIMEOUT_MS: 10000,
} as const;

interface FetchPhotosEvent {
  startDate: string;
  endDate: string;
  batchSize?: number;
}

interface PhotoRecord {
  orderId: string;
  photoUrl: string;
  petName: string;
  qualityScore: number;
  consentTimestamp: string;
  printOptions: {
    size?: string;
    color?: string;
    plantType?: string;
    drainage?: boolean;
  };
  metadata?: {
    fileSize?: number;
    contentType?: string;
    dimensions?: { width: number; height: number };
  };
}

interface ProcessingResult {
  totalPhotos: number;
  validPhotos: number;
  s3Keys: string[];
  batchId: string;
  timestamp: string;
  nextAction: string;
  errors?: string[];
  processingStats: {
    downloaded: number;
    validated: number;
    stored: number;
    failed: number;
  };
}

export const handler = async (
  event: EventBridgeEvent<'New Consented Order', FetchPhotosEvent>,
  context: Context
): Promise<ProcessingResult> => {
  const correlationId = context.awsRequestId;
  const startTime = Date.now();
  
  logger.info('Starting fetch new consented photos process', { 
    event: event.detail, 
    correlationId,
    source: event.source,
    detailType: event['detail-type']
  });
  
  try {
    // Validate environment variables
    validateEnvironment();
    
    // Validate input event
    const { error, value } = lambdaSchemas.fetchNewPhotos.validate(event.detail);
    if (error) {
      logger.error('Invalid event data', { error: error.message, correlationId });
      throw new ValidationError(`Invalid event data: ${error.message}`);
    }
    
    const { startDate, endDate, batchSize = CONFIG.DEFAULT_BATCH_SIZE } = value;
    
    // Validate batch size
    if (batchSize > CONFIG.MAX_BATCH_SIZE) {
      throw new ValidationError(`Batch size ${batchSize} exceeds maximum ${CONFIG.MAX_BATCH_SIZE}`);
    }
    
    // Validate date range
    const start = new Date(startDate);
    const end = new Date(endDate);
    if (start >= end) {
      throw new ValidationError('Start date must be before end date');
    }
    
    const daysDiff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
    if (daysDiff > 90) {
      logger.warn('Large date range detected', { daysDiff, correlationId });
    }
    
    // Initialize processing stats
    const processingStats = {
      downloaded: 0,
      validated: 0,
      stored: 0,
      failed: 0
    };
    
    // 1. Query Stripe for consented orders
    const consentedPhotos = await fetchConsentedPhotos(start, end, batchSize);
    processingStats.downloaded = consentedPhotos.length;
    
    logger.info(`Found ${consentedPhotos.length} consented photos`, { 
      correlationId, 
      count: consentedPhotos.length,
      dateRange: { startDate, endDate }
    });
    
    // 2. Download and validate photos
    const validatedPhotos = await validateAndProcessPhotos(consentedPhotos);
    processingStats.validated = validatedPhotos.length;
    
    // 3. Store in S3 dataset bucket
    const s3Keys = await storePhotosInDataset(validatedPhotos);
    processingStats.stored = s3Keys.length;
    processingStats.failed = consentedPhotos.length - s3Keys.length;
    
    // 4. Return comprehensive summary
    const result: ProcessingResult = {
      totalPhotos: consentedPhotos.length,
      validPhotos: validatedPhotos.length,
      s3Keys,
      batchId: context.awsRequestId,
      timestamp: new Date().toISOString(),
      nextAction: 'updateManifest',
      processingStats
    };
    
    const duration = Date.now() - startTime;
    logger.info('Fetch photos completed successfully', { 
      result, 
      correlationId,
      durationMs: duration,
      photosPerSecond: Math.round((consentedPhotos.length / duration) * 1000)
    });
    
    return result;
    
  } catch (error) {
    const duration = Date.now() - startTime;
    logger.error('Failed to fetch consented photos', { 
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } : String(error),
      correlationId,
      durationMs: duration
    });
    throw error;
  }
};

/**
 * Validates required environment variables
 */
function validateEnvironment(): void {
  const required = ['STRIPE_SECRET_KEY', 'S3_DATASET_BUCKET'];
  const missing = required.filter(key => !process.env[key]);
  
  if (missing.length > 0) {
    throw new ValidationError(`Missing required environment variables: ${missing.join(', ')}`);
  }
}

/**
 * Fetches consented photos from Stripe within the specified date range
 */
async function fetchConsentedPhotos(
  startDate: Date,
  endDate: Date,
  limit: number
): Promise<PhotoRecord[]> {
  const photos: PhotoRecord[] = [];
  
  try {
    logger.info('Querying Stripe for consented photos', {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      limit,
      dateRangeDays: Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))
    });
    
    // Get charges with payment intents in date range
    const charges = await stripe.charges.list({
      created: {
        gte: Math.floor(startDate.getTime() / 1000),
        lt: Math.floor(endDate.getTime() / 1000)
      },
      limit,
      expand: ['data.payment_intent']
    });
    
    let consentedCount = 0;
    let totalProcessed = 0;
    
    for (const charge of charges.data) {
      totalProcessed++;
      
      try {
        if (!charge.payment_intent || typeof charge.payment_intent !== 'object') {
          logger.debug(`Skipping charge without payment intent: ${charge.id}`);
          continue;
        }
        
        const metadata = charge.payment_intent.metadata;
        
        // Validate consent and required fields
        if (!isValidConsentedOrder(metadata)) {
          continue;
        }
        
        consentedCount++;
        
        const photoRecord: PhotoRecord = {
          orderId: charge.payment_intent.id,
          photoUrl: metadata.photo_url!,
          petName: sanitizePetName(metadata.pet_name || 'Unknown'),
          qualityScore: parseFloat(metadata.photo_quality_score || '0'),
          consentTimestamp: metadata.consent_timestamp || new Date().toISOString(),
          printOptions: {
            size: metadata.print_size,
            color: metadata.print_color,
            plantType: metadata.plant_type,
            drainage: metadata.drainage === 'true'
          }
        };
        
        photos.push(photoRecord);
        
      } catch (error) {
        logger.warn(`Failed to process charge ${charge.id}`, { 
          error: error instanceof Error ? error.message : String(error) 
        });
      }
    }
    
    logger.info('Successfully fetched consented photos from Stripe', { 
      totalCharges: charges.data.length,
      totalProcessed,
      consentedOrders: consentedCount,
      validPhotoRecords: photos.length,
      consentRate: totalProcessed > 0 ? Math.round((consentedCount / totalProcessed) * 100) : 0
    });
    
    return photos;
    
  } catch (error) {
    logger.error('Stripe query failed', { 
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        code: (error as any).code
      } : String(error),
      dateRange: { startDate: startDate.toISOString(), endDate: endDate.toISOString() }
    });
    throw error;
  }
}

/**
 * Validates if an order has proper consent and required metadata
 */
function isValidConsentedOrder(metadata: Record<string, string> | undefined): boolean {
  if (!metadata) return false;
  
  // Check consent
  if (metadata.improvement_consent !== 'true') return false;
  
  // Check required fields
  if (!metadata.photo_url) return false;
  
  // Validate photo URL format
  try {
    new URL(metadata.photo_url);
  } catch {
    logger.warn('Invalid photo URL in metadata', { photoUrl: metadata.photo_url });
    return false;
  }
  
  return true;
}

/**
 * Sanitizes pet name for safe storage
 */
function sanitizePetName(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9\s-]/g, '') // Remove special characters
    .trim()
    .substring(0, 50) // Limit length
    || 'Unknown';
}

/**
 * Downloads, validates, and processes photos for training dataset
 */
async function validateAndProcessPhotos(photos: PhotoRecord[]): Promise<PhotoRecord[]> {
  const validPhotos: PhotoRecord[] = [];
  const errors: string[] = [];
  
  logger.info('Starting comprehensive photo validation', { 
    totalPhotos: photos.length,
    qualityThreshold: CONFIG.MIN_QUALITY_SCORE,
    maxFileSize: `${CONFIG.MAX_FILE_SIZE_MB}MB`
  });
  
  // Process photos in batches to avoid overwhelming memory
  const batchSize = 10;
  for (let i = 0; i < photos.length; i += batchSize) {
    const batch = photos.slice(i, i + batchSize);
    const batchResults = await Promise.allSettled(
      batch.map(photo => validateSinglePhoto(photo))
    );
    
    batchResults.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value) {
        validPhotos.push(result.value);
      } else if (result.status === 'rejected') {
        const photo = batch[index];
        const error = `Photo ${photo.orderId}: ${result.reason}`;
        errors.push(error);
        logger.warn('Photo validation failed', { 
          orderId: photo.orderId,
          error: result.reason 
        });
      }
    });
    
    // Log progress for large batches
    if (photos.length > 50) {
      logger.info(`Processed batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(photos.length / batchSize)}`, {
        validPhotos: validPhotos.length,
        processed: Math.min(i + batchSize, photos.length)
      });
    }
  }
  
  const rejectedCount = photos.length - validPhotos.length;
  
  logger.info('Photo validation completed', { 
    totalPhotos: photos.length,
    validPhotos: validPhotos.length,
    rejectedPhotos: rejectedCount,
    successRate: Math.round((validPhotos.length / photos.length) * 100),
    topRejectionReasons: getTopErrors(errors)
  });
  
  return validPhotos;
}

/**
 * Validates a single photo with comprehensive checks
 */
async function validateSinglePhoto(photo: PhotoRecord): Promise<PhotoRecord | null> {
  try {
    // 1. Quality threshold check (early exit)
    if (photo.qualityScore < CONFIG.MIN_QUALITY_SCORE) {
      throw new Error(`Quality score ${photo.qualityScore} below threshold ${CONFIG.MIN_QUALITY_SCORE}`);
    }
    
    // 2. Download photo with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT_MS);
    
    try {
      const response = await fetch(photo.photoUrl, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'PetPlantr-Training-Bot/1.0'
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // 3. Check content type
      const contentType = response.headers.get('content-type');
      if (!contentType || !CONFIG.SUPPORTED_IMAGE_TYPES.includes(contentType as any)) {
        throw new Error(`Unsupported content type: ${contentType}`);
      }
      
      // 4. Check file size
      const contentLength = response.headers.get('content-length');
      if (contentLength) {
        const sizeInMB = parseInt(contentLength) / (1024 * 1024);
        if (sizeInMB > CONFIG.MAX_FILE_SIZE_MB) {
          throw new Error(`File size ${sizeInMB.toFixed(2)}MB exceeds limit ${CONFIG.MAX_FILE_SIZE_MB}MB`);
        }
      }
      
      // 5. Download and validate content
      const buffer = await response.arrayBuffer();
      const uint8Array = new Uint8Array(buffer);
      
      if (uint8Array.length === 0) {
        throw new Error('Empty file content');
      }
      
      // 6. Basic image format validation
      if (!isValidImageFormat(uint8Array)) {
        throw new Error('Invalid or corrupted image format');
      }
      
      // 7. Add metadata
      const enrichedPhoto: PhotoRecord = {
        ...photo,
        metadata: {
          fileSize: uint8Array.length,
          contentType,
          dimensions: await getImageDimensions(uint8Array, contentType)
        }
      };
      
      return enrichedPhoto;
      
    } finally {
      clearTimeout(timeoutId);
    }
    
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : String(error));
  }
}

/**
 * Validates image format by checking file signatures
 */
function isValidImageFormat(data: Uint8Array): boolean {
  if (data.length < 8) return false;
  
  // JPEG signature
  if (data[0] === 0xFF && data[1] === 0xD8 && data[2] === 0xFF) return true;
  
  // PNG signature
  if (data[0] === 0x89 && data[1] === 0x50 && data[2] === 0x4E && data[3] === 0x47) return true;
  
  // WebP signature
  if (data[0] === 0x52 && data[1] === 0x49 && data[2] === 0x46 && data[3] === 0x46 &&
      data[8] === 0x57 && data[9] === 0x45 && data[10] === 0x42 && data[11] === 0x50) return true;
  
  return false;
}

/**
 * Attempts to extract image dimensions (basic implementation)
 */
async function getImageDimensions(data: Uint8Array, contentType: string): Promise<{ width: number; height: number } | undefined> {
  try {
    if (contentType === 'image/jpeg') {
      return extractJPEGDimensions(data);
    }
    // For other formats, we'd need more complex parsing or a library
    return undefined;
  } catch {
    return undefined;
  }
}

/**
 * Extracts dimensions from JPEG file
 */
function extractJPEGDimensions(data: Uint8Array): { width: number; height: number } | undefined {
  let i = 2; // Skip initial FF D8
  
  while (i < data.length - 4) {
    if (data[i] === 0xFF) {
      const marker = data[i + 1];
      if (marker >= 0xC0 && marker <= 0xCF && marker !== 0xC4 && marker !== 0xC8 && marker !== 0xCC) {
        // SOF marker found
        const height = (data[i + 5] << 8) | data[i + 6];
        const width = (data[i + 7] << 8) | data[i + 8];
        return { width, height };
      }
      
      // Skip to next marker
      const length = (data[i + 2] << 8) | data[i + 3];
      i += length + 2;
    } else {
      i++;
    }
  }
  
  return undefined;
}

/**
 * Analyzes error patterns for reporting
 */
function getTopErrors(errors: string[]): Record<string, number> {
  const errorCounts: Record<string, number> = {};
  
  errors.forEach(error => {
    // Extract error type from message
    const match = error.match(/: (.+?)(?:\.|$)/);
    const errorType = match ? match[1] : 'Unknown error';
    errorCounts[errorType] = (errorCounts[errorType] || 0) + 1;
  });
  
  // Return top 5 errors
  return Object.fromEntries(
    Object.entries(errorCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
  );
}

/**
 * Stores validated photos in S3 training dataset bucket with anonymization
 */
async function storePhotosInDataset(photos: PhotoRecord[]): Promise<string[]> {
  const s3Keys: string[] = [];
  const bucketName = process.env.S3_DATASET_BUCKET!;
  
  logger.info('Starting S3 storage of training photos', { 
    bucket: bucketName,
    photoCount: photos.length,
    estimatedStorageSize: photos.reduce((sum, p) => sum + (p.metadata?.fileSize || 0), 0)
  });
  
  // Process uploads in smaller batches to manage memory and rate limits
  const uploadBatchSize = 5;
  const uploadResults: Array<{ success: boolean; key?: string; error?: string }> = [];
  
  for (let i = 0; i < photos.length; i += uploadBatchSize) {
    const batch = photos.slice(i, i + uploadBatchSize);
    
    const batchPromises = batch.map(async (photo, batchIndex) => {
      const photoIndex = i + batchIndex;
      try {
        return await uploadSinglePhoto(photo, photoIndex, bucketName);
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : String(error)
        };
      }
    });
    
    const batchResults = await Promise.allSettled(batchPromises);
    
    batchResults.forEach((result, batchIndex) => {
      const photo = batch[batchIndex];
      
      if (result.status === 'fulfilled') {
        uploadResults.push(result.value);
        if (result.value.success && result.value.key) {
          s3Keys.push(result.value.key);
        } else {
          logger.warn(`Upload failed for photo ${photo.orderId}`, { 
            error: result.value.error 
          });
        }
      } else {
        uploadResults.push({
          success: false,
          error: result.reason
        });
        logger.error(`Upload promise rejected for photo ${photo.orderId}`, { 
          error: result.reason 
        });
      }
    });
    
    // Log progress for large batches
    if (photos.length > 20) {
      logger.info(`Upload batch ${Math.floor(i / uploadBatchSize) + 1}/${Math.ceil(photos.length / uploadBatchSize)} completed`, {
        successfulUploads: s3Keys.length,
        processed: Math.min(i + uploadBatchSize, photos.length)
      });
    }
  }
  
  const successCount = uploadResults.filter(r => r.success).length;
  const failureCount = uploadResults.length - successCount;
  
  logger.info('S3 storage completed', { 
    totalPhotos: photos.length,
    successfulUploads: successCount,
    failedUploads: failureCount,
    successRate: Math.round((successCount / photos.length) * 100),
    finalS3Keys: s3Keys.length
  });
  
  return s3Keys;
}

/**
 * Uploads a single photo to S3 with proper error handling and metadata
 */
async function uploadSinglePhoto(
  photo: PhotoRecord, 
  index: number, 
  bucketName: string
): Promise<{ success: boolean; key?: string; error?: string }> {
  try {
    // Re-download photo (could be optimized by caching from validation step)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT_MS);
    
    let response: Response;
    try {
      response = await fetch(photo.photoUrl, { signal: controller.signal });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } finally {
      clearTimeout(timeoutId);
    }
    
    const buffer = await response.arrayBuffer();
    
    // Generate anonymized, collision-resistant S3 key
    const timestamp = new Date().toISOString().split('T')[0];
    const hash = Buffer.from(`${photo.orderId}_${index}_${Date.now()}`).toString('base64').slice(0, 12);
    const sanitizedPetName = photo.petName.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    const fileExtension = getFileExtension(photo.metadata?.contentType || 'image/jpeg');
    const s3Key = `training-data/${timestamp}/${hash}_${sanitizedPetName}.${fileExtension}`;
    
    // Prepare comprehensive metadata for training pipeline
    const s3Metadata: Record<string, string> = {
      'original-order-id': photo.orderId,
      'pet-name': photo.petName,
      'quality-score': photo.qualityScore.toString(),
      'consent-timestamp': photo.consentTimestamp,
      'file-size': (photo.metadata?.fileSize || buffer.byteLength).toString(),
      'content-type': photo.metadata?.contentType || 'image/jpeg',
      'print-size': photo.printOptions.size || 'unknown',
      'print-color': photo.printOptions.color || 'unknown',
      'plant-type': photo.printOptions.plantType || 'unknown',
      'has-drainage': photo.printOptions.drainage ? 'true' : 'false',
      'processed-timestamp': new Date().toISOString(),
      'anonymized': 'true',
      'training-ready': 'true',
      'pipeline-version': '1.0'
    };
    
    // Add image dimensions if available
    if (photo.metadata?.dimensions) {
      s3Metadata['image-width'] = photo.metadata.dimensions.width.toString();
      s3Metadata['image-height'] = photo.metadata.dimensions.height.toString();
    }
    
    // Upload to S3 with timeout
    const uploadParams = {
      Bucket: bucketName,
      Key: s3Key,
      Body: Buffer.from(buffer),
      ContentType: photo.metadata?.contentType || 'image/jpeg',
      Metadata: s3Metadata,
      ServerSideEncryption: 'AES256',
      StorageClass: 'STANDARD_IA' // Cost-effective for training data
    };
    
    await s3.upload(uploadParams).promise();
    
    return { success: true, key: s3Key };
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger.error(`Failed to upload photo ${photo.orderId}`, { 
      error: errorMessage,
      photoUrl: photo.photoUrl
    });
    
    return { success: false, error: errorMessage };
  }
}

/**
 * Determines file extension from content type
 */
function getFileExtension(contentType: string): string {
  switch (contentType) {
    case 'image/png': return 'png';
    case 'image/webp': return 'webp';
    case 'image/jpeg':
    default: return 'jpg';
  }
}
