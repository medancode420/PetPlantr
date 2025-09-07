import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { logger } from '../utils/enhancedLogger';
import { ValidationError } from '../utils/enhancedErrorHandler';
import { lambdaSchemas } from '../utils/validation';

const s3 = new S3Client({ region: 'us-east-1' });

interface ProcessSTLInput {
  orderId: string;
  userId: string;
  rawStlKey: string;
  sizeTier: string;
  readyStlBucket: string;
}

interface ProcessSTLOutput {
  orderId: string;
  userId: string;
  readyStlKey: string;
  status: string;
  processedAt: string;
  printingSpecs: {
    layerHeight: number;
    infill: number;
    supports: boolean;
    estimatedPrintTime: string;
    filamentUsage: string;
  };
}

export const handler = async (event: ProcessSTLInput): Promise<ProcessSTLOutput> => {
  const correlationId = Date.now().toString();
  logger.info('ProcessSTL Lambda started', { event, correlationId });

  try {
    // Validate input
    const { error, value } = lambdaSchemas.processSTL.validate(event);
    if (error) {
      logger.error('Invalid input data', { error: error.message, correlationId });
      throw new ValidationError(`Invalid input data: ${error.message}`);
    }

    const { orderId, userId, rawStlKey, sizeTier, readyStlBucket } = value;

    // Extract bucket name from rawStlKey if it includes bucket info
    const rawStlBucket = process.env.RAW_STL_BUCKET || 'petplantr-raw-stl-dev';

    logger.info('Downloading raw STL from S3', { 
      bucket: rawStlBucket, 
      key: rawStlKey, 
      correlationId 
    });

    // Download the raw STL file
    const getObjectCommand = new GetObjectCommand({
      Bucket: rawStlBucket,
      Key: rawStlKey,
    });

    const rawStlResponse = await s3.send(getObjectCommand);
    const rawStlContent = await rawStlResponse.Body?.transformToString() || '';

    if (!rawStlContent) {
      throw new ValidationError('Failed to download raw STL content');
    }

    logger.info('Raw STL downloaded successfully', { 
      contentLength: rawStlContent.length, 
      correlationId 
    });

    // In a real implementation, this would:
    // 1. Parse and validate the STL mesh
    // 2. Check for manifold errors, non-watertight geometry
    // 3. Repair mesh issues (holes, overlapping faces, etc.)
    // 4. Optimize for 3D printing (wall thickness, supports, etc.)
    // 5. Generate printing instructions based on size tier
    // 6. Apply size-specific optimizations

    // For now, we'll simulate mesh processing and validation
    const processedStlContent = processSTLMesh(rawStlContent, sizeTier);
    const printingSpecs = generatePrintingSpecs(sizeTier);

    // Generate the ready STL key
    const readyStlKey = `orders/${orderId}/ready/${userId}_${sizeTier.toLowerCase()}_ready_${Date.now()}.stl`;

    logger.info('Uploading processed STL to ready bucket', { 
      bucket: readyStlBucket, 
      key: readyStlKey, 
      correlationId 
    });

    // Upload the processed STL to the ready bucket
    const putObjectCommand = new PutObjectCommand({
      Bucket: readyStlBucket,
      Key: readyStlKey,
      Body: processedStlContent,
      ContentType: 'application/sla',
      Metadata: {
        orderId,
        userId,
        sizeTier,
        processedAt: new Date().toISOString(),
        layerHeight: printingSpecs.layerHeight.toString(),
        infill: printingSpecs.infill.toString(),
        supports: printingSpecs.supports.toString(),
        estimatedPrintTime: printingSpecs.estimatedPrintTime,
        filamentUsage: printingSpecs.filamentUsage,
      },
    });

    await s3.send(putObjectCommand);

    logger.info('Processed STL uploaded successfully', { 
      readyStlKey, 
      bucket: readyStlBucket, 
      correlationId 
    });

    const result: ProcessSTLOutput = {
      orderId,
      userId,
      readyStlKey,
      status: 'PROCESSED',
      processedAt: new Date().toISOString(),
      printingSpecs,
    };

    logger.info('ProcessSTL Lambda completed successfully', { result, correlationId });
    return result;

  } catch (error) {
    logger.error('ProcessSTL Lambda failed', { 
      error: error instanceof Error ? error.message : String(error),
      correlationId 
    });
    
    throw error;
  }
};

function processSTLMesh(rawStlContent: string, sizeTier: string): string {
  // In a real implementation, this would:
  // 1. Parse STL triangular mesh
  // 2. Validate mesh integrity
  // 3. Repair common issues
  // 4. Optimize for printing
  
  // For now, we'll add some processing metadata to the STL content
  const processedHeader = `solid PetPlantr_${sizeTier}_Processed`;
  const processedContent = rawStlContent.replace(/^solid\s+\S+/, processedHeader);
  
  return processedContent;
}

function generatePrintingSpecs(sizeTier: string) {
  switch (sizeTier) {
    case 'SMALL':
      return {
        layerHeight: 0.2,
        infill: 15,
        supports: false,
        estimatedPrintTime: '3-4 hours',
        filamentUsage: '25-35g PLA',
      };
    case 'MEDIUM':
      return {
        layerHeight: 0.2,
        infill: 20,
        supports: true,
        estimatedPrintTime: '6-8 hours',
        filamentUsage: '50-70g PLA',
      };
    case 'LARGE':
      return {
        layerHeight: 0.3,
        infill: 20,
        supports: true,
        estimatedPrintTime: '10-14 hours',
        filamentUsage: '100-140g PLA',
      };
    default:
      return {
        layerHeight: 0.2,
        infill: 20,
        supports: true,
        estimatedPrintTime: '6-8 hours',
        filamentUsage: '50-70g PLA',
      };
  }
}
