import { EventBridgeEvent } from 'aws-lambda';
import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import { 
  getCompletePipelinePrompts, 
  PhotoUrls, 
  SizeTierSpec,
  getSizeTierSpecs
} from '../utils/shapeMvdPrompts';

const s3 = new S3Client({ region: process.env.AWS_REGION });
const eventBridge = new EventBridgeClient({ region: process.env.AWS_REGION });

interface GenerateSTLEvent {
  orderId: string;
  userId: string;
  sizeTier: 'SMALL' | 'MEDIUM' | 'LARGE';
  photoUrls: PhotoUrls;
  timestamp: string;
}

interface ValidationResult {
  orderId: string;
  sizeTier: string;
  bbox_mm: [number, number, number];
  cavity_mm: { diameter: number; depth: number };
  wall_thickness_min: number;
  triangle_count: number;
  manifold_ratio: number;
  pass: boolean;
  errors: string[];
}

export const handler = async (event: EventBridgeEvent<string, GenerateSTLEvent>) => {
  console.log('Enhanced GenerateSTL Lambda Input:', JSON.stringify(event, null, 2));
  
  const { orderId, userId, sizeTier, photoUrls, timestamp } = event.detail;
  
  try {
    // Generate production-ready prompts
    const prompts = getCompletePipelinePrompts(orderId, sizeTier, photoUrls);
    const specs = getSizeTierSpecs(sizeTier);
    
    console.log(`Processing order ${orderId} for size tier ${sizeTier}`);
    console.log(`Target specifications:`, specs);
    
    // Step 1: Pet Geometry Reconstruction
    console.log('Step 1: Starting pet geometry reconstruction...');
    const reconstructionResult = await processReconstructionStage(
      orderId, 
      prompts.reconstruction, 
      photoUrls
    );
    
    if (!reconstructionResult.success) {
      throw new Error(`Reconstruction failed: ${reconstructionResult.error}`);
    }
    
    // Step 2: Planter CAD Generation
    console.log('Step 2: Starting planter CAD generation...');
    const cadResult = await processCadStage(
      orderId,
      sizeTier,
      prompts.cad_generation,
      reconstructionResult.meshUrl!
    );
    
    if (!cadResult.success) {
      throw new Error(`CAD generation failed: ${cadResult.error}`);
    }
    
    // Step 3: Design Rule Validation
    console.log('Step 3: Starting design rule validation...');
    const validationResult = await processValidationStage(
      orderId,
      sizeTier,
      prompts.validation,
      cadResult.stlUrl!
    );
    
    if (!validationResult.pass) {
      console.error('Design validation failed:', validationResult.errors);
      
      // Send to error handling
      await sendEvent('STLGenerationFailed', {
        orderId,
        userId,
        error: 'Design validation failed',
        validationErrors: validationResult.errors,
        specs: specs,
        timestamp: new Date().toISOString()
      });
      
      return {
        statusCode: 400,
        body: JSON.stringify({
          success: false,
          error: 'Design validation failed',
          validationErrors: validationResult.errors
        })
      };
    }
    
    // Success - move STL to ready bucket
    const readyStlKey = await moveToReadyBucket(orderId, cadResult.stlUrl!);
    
    console.log(`✅ STL generation completed successfully for order ${orderId}`);
    console.log(`Ready STL: ${readyStlKey}`);
    console.log(`Validation results:`, validationResult);
    
    // Send success event
    await sendEvent('STLGenerated', {
      orderId,
      userId,
      sizeTier,
      readyStlKey,
      validationResult,
      specs,
      timestamp: new Date().toISOString()
    });
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        success: true,
        orderId,
        sizeTier,
        readyStlKey,
        validationResult,
        specs
      })
    };
    
  } catch (error) {
    console.error('Enhanced GenerateSTL Lambda Error:', error);
    
    await sendEvent('STLGenerationFailed', {
      orderId,
      userId,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    });
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    };
  }
};

async function processReconstructionStage(
  orderId: string, 
  prompt: string, 
  photoUrls: PhotoUrls
): Promise<{ success: boolean; meshUrl?: string; error?: string }> {
  try {
    console.log('🔄 Processing reconstruction with production prompt...');
    
    // In production, this would call your Shape-MVD reconstruction service
    // For now, simulate the process
    
    // TODO: Replace with actual reconstruction API call
    // const reconstructionResponse = await callReconstructionAPI(prompt, photoUrls);
    
    // Simulate successful reconstruction
    const meshUrl = `S3://petplantr-raw-dev/${orderId}/recon.obj`;
    
    console.log('✅ Reconstruction completed:', meshUrl);
    
    return {
      success: true,
      meshUrl: meshUrl
    };
    
  } catch (error) {
    console.error('❌ Reconstruction failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Reconstruction failed'
    };
  }
}

async function processCadStage(
  orderId: string,
  sizeTier: string,
  prompt: string,
  meshUrl: string
): Promise<{ success: boolean; stlUrl?: string; error?: string }> {
  try {
    console.log('🔄 Processing CAD generation with production prompt...');
    console.log('Input mesh:', meshUrl);
    
    // In production, this would call your CAD generation service
    // For now, simulate the process
    
    // TODO: Replace with actual CAD API call
    // const cadResponse = await callCadAPI(prompt, meshUrl);
    
    // Simulate successful CAD generation
    const stlUrl = `S3://petplantr-stl-raw-dev/${orderId}/petplantr_${orderId}.stl`;
    
    console.log('✅ CAD generation completed:', stlUrl);
    
    return {
      success: true,
      stlUrl: stlUrl
    };
    
  } catch (error) {
    console.error('❌ CAD generation failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'CAD generation failed'
    };
  }
}

async function processValidationStage(
  orderId: string,
  sizeTier: string,
  prompt: string,
  stlUrl: string
): Promise<ValidationResult> {
  try {
    console.log('🔄 Processing validation with production prompt...');
    console.log('Input STL:', stlUrl);
    
    // In production, this would call your validation service
    // For now, simulate successful validation
    
    // TODO: Replace with actual validation API call
    // const validationResponse = await callValidationAPI(prompt, stlUrl);
    
    const specs = getSizeTierSpecs(sizeTier);
    
    // Simulate successful validation result
    const validationResult: ValidationResult = {
      orderId: orderId,
      sizeTier: sizeTier,
      bbox_mm: specs.bbox_mm,
      cavity_mm: {
        diameter: specs.cavity_diameter,
        depth: specs.cavity_depth
      },
      wall_thickness_min: specs.material_thickness,
      triangle_count: 145000, // Simulated count < 180k
      manifold_ratio: 0.98, // Simulated ratio > 95%
      pass: true,
      errors: []
    };
    
    console.log('✅ Validation completed:', validationResult);
    
    return validationResult;
    
  } catch (error) {
    console.error('❌ Validation failed:', error);
    
    // Return failed validation
    return {
      orderId: orderId,
      sizeTier: sizeTier,
      bbox_mm: [0, 0, 0],
      cavity_mm: { diameter: 0, depth: 0 },
      wall_thickness_min: 0,
      triangle_count: 0,
      manifold_ratio: 0,
      pass: false,
      errors: [error instanceof Error ? error.message : 'Validation failed']
    };
  }
}

async function moveToReadyBucket(orderId: string, stlUrl: string): Promise<string> {
  // In production, this would copy the STL from raw bucket to ready bucket
  // For now, return the expected ready bucket path
  
  const readyStlKey = `${orderId}/petplantr_${orderId}.stl`;
  
  console.log(`Moving STL to ready bucket: ${readyStlKey}`);
  
  // TODO: Implement actual S3 copy operation
  // await s3.send(new CopyObjectCommand({
  //   CopySource: parseS3Url(stlUrl),
  //   Bucket: process.env.READY_STL_BUCKET,
  //   Key: readyStlKey
  // }));
  
  return readyStlKey;
}

async function sendEvent(eventType: string, detail: any) {
  const command = new PutEventsCommand({
    Entries: [
      {
        Source: 'petplantr.stl-generation',
        DetailType: eventType,
        Detail: JSON.stringify(detail),
        EventBusName: process.env.EVENT_BUS_NAME
      }
    ]
  });
  
  await eventBridge.send(command);
  console.log(`Event sent: ${eventType}`, detail);
}
