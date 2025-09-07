import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { logger } from '../utils/enhancedLogger';
import { ValidationError } from '../utils/enhancedErrorHandler';
import { lambdaSchemas } from '../utils/validation';
import { 
  getCompletePipelinePrompts, 
  PhotoUrls, 
  getSizeTierSpecs,
  formatReconstructionPrompt,
  formatCadPrompt,
  formatValidationPrompt
} from '../utils/shapeMvdPrompts';

const s3 = new S3Client({ region: 'us-east-1' });

interface GenerateSTLInput {
  orderId: string;
  userId: string;
  photoKeys: string[];
  sizeTier: 'SMALL' | 'MEDIUM' | 'LARGE';
  rawStlBucket: string;
  downloadedPhotos?: string[];
}

interface GenerateSTLOutput {
  orderId: string;
  userId: string;
  rawStlKey: string;
  status: string;
  generatedAt: string;
  shapeMvdPrompts?: {
    reconstruction: string;
    cad_generation: string;
    validation: string;
  };
  sizeTierSpecs?: any;
}

export const handler = async (event: GenerateSTLInput): Promise<GenerateSTLOutput> => {
  const correlationId = Date.now().toString();
  logger.info('GenerateSTL Lambda started', { event, correlationId });

  try {
    // Validate input
    const { error, value } = lambdaSchemas.generateSTL.validate(event);
    if (error) {
      logger.error('Invalid input data', { error: error.message, correlationId });
      throw new ValidationError(`Invalid input data: ${error.message}`);
    }

    const { orderId, userId, photoKeys, sizeTier, rawStlBucket } = value;

    logger.info(`Processing STL generation for order ${orderId}`, { 
      sizeTier, 
      photoCount: photoKeys.length,
      correlationId 
    });
    
    // Get size tier specifications
    const specs = getSizeTierSpecs(sizeTier);
    logger.info('Size specifications loaded', { specs, correlationId });
    
    // Generate photo URLs (assuming they're in the upload bucket)
    const photoUrls: PhotoUrls = {
      front: `https://${process.env.UPLOAD_BUCKET}.s3.amazonaws.com/${photoKeys[0] || 'front.jpg'}`,
      left: `https://${process.env.UPLOAD_BUCKET}.s3.amazonaws.com/${photoKeys[1] || 'left.jpg'}`,
      right: `https://${process.env.UPLOAD_BUCKET}.s3.amazonaws.com/${photoKeys[2] || 'right.jpg'}`,
      back: `https://${process.env.UPLOAD_BUCKET}.s3.amazonaws.com/${photoKeys[3] || 'back.jpg'}`,
      top: `https://${process.env.UPLOAD_BUCKET}.s3.amazonaws.com/${photoKeys[4] || 'top.jpg'}`
    };
    
    // Generate production-ready Shape-MVD prompts
    logger.info('Generating Shape-MVD prompts', { correlationId });
    const prompts = getCompletePipelinePrompts(orderId, sizeTier, photoUrls);
    
    logger.info('Shape-MVD prompts generated successfully', {
      reconstructionLength: prompts.reconstruction.length,
      cadGenerationLength: prompts.cad_generation.length,
      validationLength: prompts.validation.length,
      correlationId
    });

    // In a real implementation, this would:
    // 1. Send prompts.reconstruction to Shape-MVD reconstruction service
    // 2. Send prompts.cad_generation to CAD generation service
    // 3. Send prompts.validation to validation service
    // 4. Process results and upload final STL
    
    // For now, we'll simulate the process with enhanced mock STL
    const rawStlKey = `orders/${orderId}/raw/${userId}_${sizeTier.toLowerCase()}_${Date.now()}.stl`;
    
    // Simulate enhanced STL generation with proper specifications
    const mockStlContent = generateEnhancedMockSTL(sizeTier, specs, prompts);
    
    // Upload the generated STL to the raw bucket
    const putObjectCommand = new PutObjectCommand({
      Bucket: rawStlBucket,
      Key: rawStlKey,
      Body: mockStlContent,
      ContentType: 'application/sla', // STL MIME type
      Metadata: {
        orderId,
        userId,
        sizeTier,
        photoCount: photoKeys.length.toString(),
        generatedAt: new Date().toISOString(),
        bboxX: specs.bbox_mm[0].toString(),
        bboxY: specs.bbox_mm[1].toString(),
        bboxZ: specs.bbox_mm[2].toString(),
        cavityDiameter: specs.cavity_diameter.toString(),
        cavityDepth: specs.cavity_depth.toString(),
        wallThickness: specs.material_thickness.toString(),
      },
    });

    await s3.send(putObjectCommand);

    logger.info('STL uploaded to S3 successfully', { 
      rawStlKey, 
      bucket: rawStlBucket, 
      correlationId 
    });

    const result: GenerateSTLOutput = {
      orderId,
      userId,
      rawStlKey,
      status: 'GENERATED',
      generatedAt: new Date().toISOString(),
      shapeMvdPrompts: {
        reconstruction: prompts.reconstruction,
        cad_generation: prompts.cad_generation,
        validation: prompts.validation
      },
      sizeTierSpecs: specs
    };

    logger.info('GenerateSTL Lambda completed successfully', { result, correlationId });
    return result;

  } catch (error) {
    logger.error('GenerateSTL Lambda failed', { 
      error: error instanceof Error ? error.message : String(error),
      correlationId 
    });
    
    throw error;
  }
};

function generateEnhancedMockSTL(sizeTier: string, specs: any, prompts: any): string {
  // Enhanced mock STL with proper specifications
  const bbox = specs.bbox_mm;
  const cavity = specs.cavity_diameter;
  const depth = specs.cavity_depth;
  const thickness = specs.material_thickness;
  
  return `solid PetPlantr_Enhanced_${sizeTier}
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex ${bbox[0]} 0.0 0.0
      vertex ${bbox[0]} ${bbox[1]} 0.0
    endloop
  endfacet
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex ${bbox[0]} ${bbox[1]} 0.0
      vertex 0.0 ${bbox[1]} 0.0
    endloop
  endfacet
  facet normal 0.0 0.0 -1.0
    outer loop
      vertex ${thickness} ${thickness} ${bbox[2]}
      vertex ${bbox[0] - thickness} ${bbox[1] - thickness} ${bbox[2]}
      vertex ${bbox[0] - thickness} ${thickness} ${bbox[2]}
    endloop
  endfacet
  facet normal 0.0 0.0 -1.0
    outer loop
      vertex ${thickness} ${thickness} ${bbox[2]}
      vertex ${thickness} ${bbox[1] - thickness} ${bbox[2]}
      vertex ${bbox[0] - thickness} ${bbox[1] - thickness} ${bbox[2]}
    endloop
  endfacet
endsolid PetPlantr_Enhanced_${sizeTier}`;
}

function getSizeDimensions(sizeTier: string): { width: number; depth: number; height: number } {
  const specs = getSizeTierSpecs(sizeTier);
  return { 
    width: specs.bbox_mm[0], 
    depth: specs.bbox_mm[1], 
    height: specs.bbox_mm[2] 
  };
}
