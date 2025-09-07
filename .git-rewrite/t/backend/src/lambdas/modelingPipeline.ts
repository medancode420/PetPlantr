import { SFNClient, SendTaskSuccessCommand, SendTaskFailureCommand } from '@aws-sdk/client-sfn';
import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
import fs from 'fs/promises';
import path from 'path';

const sfn = new SFNClient({ region: 'us-east-1' });
const s3 = new S3Client({ region: 'us-east-1' });
const secretsManager = new SecretsManagerClient({ region: 'us-east-1' });

// Load production modeling pipeline configuration from S3
let PIPELINE_CONFIG: any = null;

async function loadPipelineConfig(): Promise<any> {
  if (!PIPELINE_CONFIG) {
    try {
      const configBucket = process.env.MODELS_BUCKET || 'petplantr-models-prod';
      const response = await s3.send(new GetObjectCommand({
        Bucket: configBucket,
        Key: 'config/modeling-pipeline.json'
      }));
      const configText = await response.Body?.transformToString();
      PIPELINE_CONFIG = JSON.parse(configText || '{}');
      console.log('Loaded production pipeline configuration');
    } catch (error) {
      console.error('Failed to load pipeline config from S3:', error);
      // Fallback to local config for development
      PIPELINE_CONFIG = require('../config/modeling-pipeline.json');
    }
  }
  return PIPELINE_CONFIG;
}

async function getModelWeightsPath(secretKey: string): Promise<string> {
  try {
    const response = await secretsManager.send(new GetSecretValueCommand({
      SecretId: secretKey
    }));
    return response.SecretString || '';
  } catch (error) {
    console.error(`Failed to get model weights path from secret ${secretKey}:`, error);
    throw new Error(`Model weights not configured: ${secretKey}`);
  }
}

interface ModelingPipelineInput {
  orderId: string;
  userId: string;
  photoUrls: string[];
  stage: 'featureExtraction' | 'depthEstimation' | 'meshReconstruction' | 'planterGeometry' | 'meshCleanup' | 'textureMarking';
  taskToken?: string;
  previousStageOutput?: any;
}

interface ModelingPipelineOutput {
  orderId: string;
  userId: string;
  stage: string;
  outputPath: string;
  processingTimeSeconds: number;
  qualityMetrics: any;
  nextStage?: string;
}

/**
 * AI/ML Modeling Pipeline Lambda
 * Processes pet photos through the 6-stage modeling pipeline
 * Integrates with existing Step Functions workflow
 * Uses production model weights from S3 and Secrets Manager
 */
export const handler = async (event: ModelingPipelineInput): Promise<ModelingPipelineOutput> => {
  console.log('Modeling Pipeline Input:', JSON.stringify(event, null, 2));

  const { orderId, userId, photoUrls, stage, taskToken, previousStageOutput } = event;
  const startTime = Date.now();

  try {
    // Load production pipeline configuration
    const pipelineConfig = await loadPipelineConfig();
    const stageConfig = pipelineConfig.modelingPipeline.stages[stage];
    
    if (!stageConfig || !stageConfig.enabled) {
      throw new Error(`Stage ${stage} is not enabled or configured`);
    }

    console.log(`Processing stage: ${stage} for order ${orderId}`);
    console.log(`Stage config:`, JSON.stringify(stageConfig, null, 2));

    // Get model weights path from Secrets Manager if available
    let modelWeightsPath: string | null = null;
    if (stageConfig.model?.secretsManagerKey) {
      try {
        modelWeightsPath = await getModelWeightsPath(stageConfig.model.secretsManagerKey);
        console.log(`Using production model weights: ${modelWeightsPath}`);
      } catch (error) {
        console.warn(`Could not load production weights, using stub: ${error}`);
      }
    }

    // Create processing workspace
    const workspaceDir = `/tmp/petplantr-${orderId}-${stage}`;
    await fs.mkdir(workspaceDir, { recursive: true });

    let outputPath: string;
    let qualityMetrics: any = {};

    // Route to appropriate processing function based on stage
    switch (stage) {
      case 'featureExtraction':
        outputPath = await processFeatureExtraction(orderId, photoUrls, workspaceDir, stageConfig);
        break;
      
      case 'depthEstimation':
        outputPath = await processDepthEstimation(orderId, previousStageOutput, workspaceDir, stageConfig);
        break;
      
      case 'meshReconstruction':
        outputPath = await processMeshReconstruction(orderId, previousStageOutput, workspaceDir, stageConfig);
        break;
      
      case 'planterGeometry':
        outputPath = await processPlanterGeometry(orderId, previousStageOutput, workspaceDir, stageConfig);
        break;
      
      case 'meshCleanup':
        outputPath = await processMeshCleanup(orderId, previousStageOutput, workspaceDir, stageConfig);
        qualityMetrics = await validateMeshQuality(outputPath);
        break;
      
      case 'textureMarking':
        outputPath = await processTextureMarking(orderId, previousStageOutput, workspaceDir, stageConfig);
        break;
      
      default:
        throw new Error(`Unknown stage: ${stage}`);
    }

    // Calculate processing time
    const processingTimeSeconds = Math.round((Date.now() - startTime) / 1000);
    
    // Check if processing time exceeds target
    const targetTime = PIPELINE_CONFIG.modelingPipeline.performance.targetTimes[stage];
    if (processingTimeSeconds > targetTime * 1.5) {
      console.warn(`Stage ${stage} took ${processingTimeSeconds}s, target was ${targetTime}s`);
    }

    // Determine next stage
    const stageOrder = ['featureExtraction', 'depthEstimation', 'meshReconstruction', 'planterGeometry', 'meshCleanup', 'textureMarking'];
    const currentIndex = stageOrder.indexOf(stage);
    const nextStage = currentIndex < stageOrder.length - 1 ? stageOrder[currentIndex + 1] : undefined;

    // Skip textureMarking if disabled
    const finalNextStage = nextStage === 'textureMarking' && !PIPELINE_CONFIG.modelingPipeline.stages.textureMarking.enabled 
      ? undefined 
      : nextStage;

    const result: ModelingPipelineOutput = {
      orderId,
      userId,
      stage,
      outputPath,
      processingTimeSeconds,
      qualityMetrics,
      nextStage: finalNextStage
    };

    // If this is a Step Functions task, send success
    if (taskToken) {
      await sfn.send(new SendTaskSuccessCommand({
        taskToken,
        output: JSON.stringify(result)
      }));
    }

    console.log('Modeling Pipeline Output:', JSON.stringify(result, null, 2));
    return result;

  } catch (error) {
    console.error('Modeling Pipeline Error:', error);

    // If this is a Step Functions task, send failure
    if (taskToken) {
      await sfn.send(new SendTaskFailureCommand({
        taskToken,
        error: 'ModelingPipelineError',
        cause: error instanceof Error ? error.message : 'Unknown error'
      }));
    }

    throw {
      errorType: 'ModelingPipelineError',
      errorMessage: error instanceof Error ? error.message : 'Unknown error',
      stage,
      orderId,
      processingTimeSeconds: Math.round((Date.now() - startTime) / 1000)
    };
  }
};

// Individual stage processing functions (stubs for now)
async function processFeatureExtraction(orderId: string, photoUrls: string[], workspaceDir: string, config: any): Promise<string> {
  console.log(`Processing feature extraction for order ${orderId}`);
  
  // TODO: Implement ViT feature extraction
  // 1. Download photos from S3
  // 2. Load fine-tuned ViT model
  // 3. Extract facial features with ArcFace loss
  // 4. Save feature vectors to S3
  
  const outputPath = `s3://petplantr-processing-dev/${orderId}/features.json`;
  
  // Mock implementation
  const features = {
    orderId,
    extractedFeatures: 'mock_feature_vector',
    confidence: 0.95,
    breedPrediction: 'golden_retriever'
  };
  
  // In real implementation: upload to S3
  console.log('Feature extraction completed (mock)');
  return outputPath;
}

async function processDepthEstimation(orderId: string, previousOutput: any, workspaceDir: string, config: any): Promise<string> {
  console.log(`Processing depth estimation for order ${orderId}`);
  
  // TODO: Implement DINOv2 + MiDaS ensemble
  // 1. Load images and feature vectors
  // 2. Run DINOv2 for feature enhancement
  // 3. Run MiDaS-DPT-Large for depth estimation
  // 4. Ensemble results with configured weights
  // 5. Generate surface normals with fur edge enhancement
  
  const outputPath = `s3://petplantr-processing-dev/${orderId}/depth_normals.npz`;
  
  console.log('Depth estimation completed (mock)');
  return outputPath;
}

async function processMeshReconstruction(orderId: string, previousOutput: any, workspaceDir: string, config: any): Promise<string> {
  console.log(`Processing mesh reconstruction for order ${orderId}`);
  
  // TODO: Implement Shape-MVD reconstruction
  // 1. Load depth maps and normals
  // 2. Generate multi-view consistency
  // 3. Run Shape-MVD with fine-tuned weights
  // 4. Generate initial mesh with target resolution
  
  const outputPath = `s3://petplantr-processing-dev/${orderId}/initial_mesh.obj`;
  
  console.log('Mesh reconstruction completed (mock)');
  return outputPath;
}

async function processPlanterGeometry(orderId: string, previousOutput: any, workspaceDir: string, config: any): Promise<string> {
  console.log(`Processing planter geometry for order ${orderId}`);
  
  // TODO: Implement OpenSCAD boolean operations
  // 1. Load reconstructed mesh
  // 2. Create cylindrical cavity with configured diameter
  // 3. Add drainage hole
  // 4. Create shell with 2mm wall thickness
  // 5. Preserve facial geometry integrity
  
  const outputPath = `s3://petplantr-processing-dev/${orderId}/planter_geometry.stl`;
  
  console.log('Planter geometry completed (mock)');
  return outputPath;
}

async function processMeshCleanup(orderId: string, previousOutput: any, workspaceDir: string, config: any): Promise<string> {
  console.log(`Processing mesh cleanup for order ${orderId}`);
  
  // TODO: Implement Instant-Meshes + MeshLab cleanup
  // 1. Load planter geometry
  // 2. Run Instant-Meshes for retopology
  // 3. Apply MeshLab filters:
  //    - Remove isolated pieces
  //    - Remove duplicate vertices
  //    - Fix non-manifold edges
  //    - Laplacian smoothing
  // 4. Validate target face count < 180k
  
  const outputPath = `s3://petplantr-stl-ready-dev/${orderId}.stl`;
  
  console.log('Mesh cleanup completed (mock)');
  return outputPath;
}

async function processTextureMarking(orderId: string, previousOutput: any, workspaceDir: string, config: any): Promise<string> {
  console.log(`Processing texture marking for order ${orderId}`);
  
  // TODO: Implement vertex color baking
  // 1. Load cleaned mesh
  // 2. Bake vertex colors at 2048 resolution
  // 3. Generate bump maps for surface detail
  // 4. Add procedural noise for layer line masking
  
  const outputPath = `s3://petplantr-stl-ready-dev/${orderId}_textured.stl`;
  
  console.log('Texture marking completed (mock)');
  return outputPath;
}

async function validateMeshQuality(meshPath: string): Promise<any> {
  // TODO: Implement mesh validation
  // 1. Check manifold ratio
  // 2. Validate face count
  // 3. Ensure positive volume
  // 4. Check printability constraints
  
  return {
    manifoldRatio: 0.98,
    faceCount: 175000,
    volumePositive: true,
    printabilityScore: 0.92,
    minimumFeatureSize: 0.5,
    overhangs: 'minimal'
  };
}
