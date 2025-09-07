/**
 * Lambda 3: Kick Fine-Tune Job
 * Triggers Modal fine-tuning job with new dataset
 */

import { Context } from 'aws-lambda';
import AWS from 'aws-sdk';
import fetch from 'node-fetch';

const secretsManager = new AWS.SecretsManager();

interface KickFineTuneEvent {
  manifestVersion: string;
  newImagesAdded: number;
  totalImages: number;
  batchId: string;
  trainingStats: Record<string, any>;
}

interface ModalJobConfig {
  model_name: string;
  dataset_manifest_s3_key: string;
  base_model_s3_key: string;
  epochs: number;
  batch_size: number;
  learning_rate: number;
  output_model_s3_key: string;
  job_id: string;
}

export const handler = async (
  event: KickFineTuneEvent,
  context: Context
) => {
  console.log('Kicking fine-tune job:', JSON.stringify(event, null, 2));
  
  const { manifestVersion, newImagesAdded, totalImages, batchId, trainingStats } = event;
  
  try {
    // 1. Check if we have enough new data for training
    if (newImagesAdded < parseInt(process.env.MIN_IMAGES_FOR_TRAINING || '10')) {
      console.log(`Not enough new images (${newImagesAdded}) for training, skipping`);
      return {
        action: 'skipped',
        reason: 'insufficient_new_data',
        newImagesAdded,
        minimumRequired: process.env.MIN_IMAGES_FOR_TRAINING || '10'
      };
    }
    
    // 2. Get Modal API token
    const modalToken = await getModalToken();
    
    // 3. Prepare job configuration
    const jobConfig = await prepareJobConfig(manifestVersion, batchId, trainingStats);
    
    // 4. Submit job to Modal
    const modalJob = await submitModalJob(modalToken, jobConfig);
    
    // 5. Store job reference
    await storeJobReference(modalJob, jobConfig);
    
    const result = {
      modalJobId: modalJob.id,
      jobConfig,
      estimatedDuration: '15-30 minutes',
      nextAction: 'evaluateMetrics',
      monitoringUrl: `https://modal.com/jobs/${modalJob.id}`
    };
    
    console.log('Fine-tune job kicked:', result);
    return result;
    
  } catch (error) {
    console.error('Failed to kick fine-tune job:', error);
    throw new Error(
      error instanceof Error ? error.message : 'Fine-tune job creation failed'
    );
  }
};

async function getModalToken(): Promise<string> {
  try {
    const result = await secretsManager.getSecretValue({
      SecretId: 'petplantr/modal-token'
    }).promise();
    
    if (result.SecretString) {
      const secrets = JSON.parse(result.SecretString);
      return secrets.MODAL_TOKEN;
    }
    
    throw new Error('Modal token not found in secrets');
  } catch (error) {
    console.error('Failed to get Modal token:', error);
    throw error;
  }
}

async function prepareJobConfig(
  manifestVersion: string,
  batchId: string,
  trainingStats: Record<string, any>
): Promise<ModalJobConfig> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const jobId = `finetune-${batchId}-${timestamp}`;
  
  return {
    model_name: 'shape_mvd_unet_256',
    dataset_manifest_s3_key: 'training-manifest.json',
    base_model_s3_key: 'models/shape_mvd_unet_256_base.pth',
    epochs: 2, // As specified in requirements
    batch_size: calculateOptimalBatchSize(trainingStats.totalImages),
    learning_rate: 0.0001, // Conservative learning rate for fine-tuning
    output_model_s3_key: `models/candidates/${jobId}/unet_finetuned.pth`,
    job_id: jobId
  };
}

function calculateOptimalBatchSize(totalImages: number): number {
  // Calculate batch size based on available data
  if (totalImages < 100) return 4;
  if (totalImages < 500) return 8;
  if (totalImages < 1000) return 16;
  return 32;
}

async function submitModalJob(
  modalToken: string,
  jobConfig: ModalJobConfig
): Promise<{ id: string; status: string }> {
  const modalEndpoint = process.env.MODAL_ENDPOINT || 'https://api.modal.com/v1';
  
  try {
    const response = await fetch(`${modalEndpoint}/functions/train_unet_incremental`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${modalToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: {
          ...jobConfig,
          // Environment variables for the Modal function
          S3_DATASET_BUCKET: process.env.S3_DATASET_BUCKET,
          S3_MODEL_BUCKET: process.env.S3_MODEL_BUCKET,
          AWS_ACCESS_KEY_ID: process.env.AWS_ACCESS_KEY_ID,
          AWS_SECRET_ACCESS_KEY: process.env.AWS_SECRET_ACCESS_KEY,
          AWS_DEFAULT_REGION: process.env.AWS_DEFAULT_REGION
        },
        // Use T4 GPU as specified
        gpu: 'T4'
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Modal API error: ${response.status} - ${errorText}`);
    }
    
    const result = await response.json() as any;
    
    return {
      id: result.call_id || result.id,
      status: result.status || 'submitted'
    };
    
  } catch (error) {
    console.error('Modal job submission failed:', error);
    throw error;
  }
}

async function storeJobReference(
  modalJob: { id: string; status: string },
  jobConfig: ModalJobConfig
): Promise<void> {
  const s3 = new AWS.S3();
  const bucketName = process.env.S3_MODEL_BUCKET!;
  const jobReferenceKey = `jobs/${jobConfig.job_id}/job-config.json`;
  
  const jobReference = {
    modalJobId: modalJob.id,
    jobConfig,
    status: modalJob.status,
    createdAt: new Date().toISOString(),
    createdBy: 'lambda-kickFineTuneJob'
  };
  
  await s3.upload({
    Bucket: bucketName,
    Key: jobReferenceKey,
    Body: JSON.stringify(jobReference, null, 2),
    ContentType: 'application/json'
  }).promise();
}
