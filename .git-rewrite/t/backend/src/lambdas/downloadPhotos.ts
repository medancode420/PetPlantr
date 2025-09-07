import { S3Client, GetObjectCommand, CopyObjectCommand } from '@aws-sdk/client-s3';
import { logger } from '../utils/enhancedLogger';
import { validateInput, lambdaSchemas } from '../utils/validation';

const s3 = new S3Client({ region: 'us-east-1' });

interface DownloadPhotosInput {
  orderId: string;
  userId: string;
  photoKeys: string[];
  uploadBucket: string;
}

interface DownloadPhotosOutput {
  orderId: string;
  userId: string;
  downloadedPhotos: string[];
  status: string;
  downloadedAt: string;
}

export const handler = async (event: DownloadPhotosInput): Promise<DownloadPhotosOutput> => {
  const correlationId = `download_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  
  logger.info('DownloadPhotos Lambda invoked', {
    correlationId,
    orderId: event.orderId,
    userId: event.userId,
    photoCount: event.photoKeys?.length
  });

  // Validate input using enhanced validation
  const validatedEvent = validateInput(event, lambdaSchemas.downloadPhotos);
  const { orderId, userId, photoKeys, uploadBucket } = validatedEvent;

  try {
    // Validate input
    if (!orderId || !userId || !photoKeys || !uploadBucket) {
      throw new Error('Missing required parameters');
    }

    if (!Array.isArray(photoKeys) || photoKeys.length === 0) {
      throw new Error('No photo keys provided');
    }

    const downloadedPhotos: string[] = [];

    // Process each photo
    for (const photoKey of photoKeys) {
      try {
        // Verify the photo exists in the upload bucket
        const getObjectCommand = new GetObjectCommand({
          Bucket: uploadBucket,
          Key: photoKey,
        });

        await s3.send(getObjectCommand);
        
        // For now, we'll just verify the photos exist
        // In a real implementation, you might want to:
        // 1. Download and validate image format/size
        // 2. Apply any pre-processing (resize, format conversion)
        // 3. Copy to a processing bucket with order prefix
        
        downloadedPhotos.push(photoKey);
        logger.info(`Successfully validated photo: ${photoKey}`, { correlationId });
        
      } catch (error) {
        logger.error(`Failed to process photo ${photoKey}:`, error, { correlationId });
        // Continue with other photos, don't fail the entire batch
      }
    }

    if (downloadedPhotos.length === 0) {
      throw new Error('No photos could be downloaded/validated');
    }

    const result: DownloadPhotosOutput = {
      orderId,
      userId,
      downloadedPhotos,
      status: 'DOWNLOADED',
      downloadedAt: new Date().toISOString(),
    };

    logger.info('DownloadPhotos Lambda successful', {
      correlationId,
      result,
    });
    return result;

  } catch (error) {
    logger.error('DownloadPhotos Lambda Error:', error, { correlationId });
    
    // Return error details for Step Functions error handling
    throw {
      errorType: 'DownloadPhotosError',
      errorMessage: error instanceof Error ? error.message : 'Unknown error',
      orderId,
      userId,
      timestamp: new Date().toISOString(),
    };
  }
};
