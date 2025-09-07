/**
 * Lambda 4: Evaluate Metrics
 * Evaluates fine-tuned model performance and determines if it should be deployed
 */

import { Context } from 'aws-lambda';
import AWS from 'aws-sdk';
import fetch from 'node-fetch';

const s3 = new AWS.S3();
const cloudWatch = new AWS.CloudWatch();

interface EvaluateMetricsEvent {
  modalJobId: string;
  jobConfig: {
    job_id: string;
    output_model_s3_key: string;
    base_model_s3_key: string;
  };
  estimatedDuration: string;
}

interface ModelMetrics {
  validation_loss: number;
  training_loss: number;
  accuracy: number;
  f1_score: number;
  inference_time_ms: number;
  model_size_mb: number;
}

interface EvaluationResult {
  passed: boolean;
  metrics: ModelMetrics;
  baselineMetrics: ModelMetrics;
  improvements: Record<string, number>;
  decision: 'promote' | 'rollback' | 'needs_review';
  reason: string;
}

export const handler = async (
  event: EvaluateMetricsEvent,
  context: Context
) => {
  console.log('Evaluating model metrics:', JSON.stringify(event, null, 2));
  
  const { modalJobId, jobConfig } = event;
  
  try {
    // 1. Check if Modal job is complete
    const jobStatus = await checkModalJobStatus(modalJobId);
    
    if (jobStatus.status !== 'completed') {
      console.log(`Modal job ${modalJobId} not yet complete: ${jobStatus.status}`);
      return {
        action: 'wait',
        jobStatus: jobStatus.status,
        retryAfter: '5 minutes'
      };
    }
    
    // 2. Load new model metrics
    const newModelMetrics = await loadModelMetrics(jobConfig.output_model_s3_key);
    
    // 3. Load baseline metrics
    const baselineMetrics = await loadBaselineMetrics();
    
    // 4. Evaluate model performance
    const evaluation = evaluateModelPerformance(newModelMetrics, baselineMetrics);
    
    // 5. Record metrics in CloudWatch
    await recordMetricsInCloudWatch(newModelMetrics, evaluation);
    
    // 6. Store evaluation results
    await storeEvaluationResults(jobConfig.job_id, evaluation);
    
    const result = {
      evaluation,
      nextAction: evaluation.decision === 'promote' ? 'canaryDeploy' : 'trafficShift',
      candidateModelKey: jobConfig.output_model_s3_key,
      jobId: jobConfig.job_id
    };
    
    console.log('Model evaluation result:', result);
    return result;
    
  } catch (error) {
    console.error('Failed to evaluate model metrics:', error);
    throw new Error(
      error instanceof Error ? error.message : 'Model evaluation failed'
    );
  }
};

async function checkModalJobStatus(modalJobId: string): Promise<{ status: string; logs?: string[] }> {
  try {
    const modalToken = await getModalToken();
    const modalEndpoint = process.env.MODAL_ENDPOINT || 'https://api.modal.com/v1';
    
    const response = await fetch(`${modalEndpoint}/calls/${modalJobId}`, {
      headers: {
        'Authorization': `Bearer ${modalToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Modal API error: ${response.status}`);
    }
    
    const result = await response.json() as any;
    
    return {
      status: result.status || 'unknown',
      logs: result.logs || []
    };
    
  } catch (error) {
    console.error('Failed to check Modal job status:', error);
    return { status: 'error' };
  }
}

async function getModalToken(): Promise<string> {
  const secretsManager = new AWS.SecretsManager();
  const result = await secretsManager.getSecretValue({
    SecretId: 'petplantr/modal-token'
  }).promise();
  
  if (result.SecretString) {
    const secrets = JSON.parse(result.SecretString);
    return secrets.MODAL_TOKEN;
  }
  
  throw new Error('Modal token not found');
}

async function loadModelMetrics(modelS3Key: string): Promise<ModelMetrics> {
  const bucketName = process.env.S3_MODEL_BUCKET!;
  const metricsKey = modelS3Key.replace('.pth', '_metrics.json');
  
  try {
    const result = await s3.getObject({
      Bucket: bucketName,
      Key: metricsKey
    }).promise();
    
    if (result.Body) {
      return JSON.parse(result.Body.toString());
    }
    
    throw new Error('Metrics file not found');
  } catch (error) {
    console.error(`Failed to load metrics from ${metricsKey}:`, error);
    throw error;
  }
}

async function loadBaselineMetrics(): Promise<ModelMetrics> {
  const bucketName = process.env.S3_MODEL_BUCKET!;
  const baselineKey = 'models/baseline_metrics.json';
  
  try {
    const result = await s3.getObject({
      Bucket: bucketName,
      Key: baselineKey
    }).promise();
    
    if (result.Body) {
      return JSON.parse(result.Body.toString());
    }
  } catch (error) {
    console.log('No baseline metrics found, using defaults');
  }
  
  // Default baseline metrics if none exist
  return {
    validation_loss: 0.5,
    training_loss: 0.4,
    accuracy: 0.85,
    f1_score: 0.82,
    inference_time_ms: 150,
    model_size_mb: 45
  };
}

function evaluateModelPerformance(
  newMetrics: ModelMetrics,
  baselineMetrics: ModelMetrics
): EvaluationResult {
  const improvements = {
    validation_loss: ((baselineMetrics.validation_loss - newMetrics.validation_loss) / baselineMetrics.validation_loss) * 100,
    accuracy: ((newMetrics.accuracy - baselineMetrics.accuracy) / baselineMetrics.accuracy) * 100,
    f1_score: ((newMetrics.f1_score - baselineMetrics.f1_score) / baselineMetrics.f1_score) * 100,
    inference_time: ((baselineMetrics.inference_time_ms - newMetrics.inference_time_ms) / baselineMetrics.inference_time_ms) * 100
  };
  
  // Decision criteria as specified in requirements
  const validationLossIncrease = ((newMetrics.validation_loss - baselineMetrics.validation_loss) / baselineMetrics.validation_loss) * 100;
  
  let decision: 'promote' | 'rollback' | 'needs_review' = 'promote';
  let reason = 'Model shows improvement across key metrics';
  
  // Check validation loss threshold (+5% max increase)
  if (validationLossIncrease > 5) {
    decision = 'rollback';
    reason = `Validation loss increased by ${validationLossIncrease.toFixed(2)}% (>5% threshold)`;
  }
  // Check for significant accuracy degradation
  else if (improvements.accuracy < -2) {
    decision = 'needs_review';
    reason = `Accuracy decreased by ${Math.abs(improvements.accuracy).toFixed(2)}%`;
  }
  // Check for inference time regression
  else if (improvements.inference_time < -20) {
    decision = 'needs_review';
    reason = `Inference time increased by ${Math.abs(improvements.inference_time).toFixed(2)}%`;
  }
  
  return {
    passed: decision === 'promote',
    metrics: newMetrics,
    baselineMetrics,
    improvements,
    decision,
    reason
  };
}

async function recordMetricsInCloudWatch(
  metrics: ModelMetrics,
  evaluation: EvaluationResult
): Promise<void> {
  const timestamp = new Date();
  
  const metricData = [
    {
      MetricName: 'ValidationLoss',
      Value: metrics.validation_loss,
      Unit: 'None',
      Timestamp: timestamp
    },
    {
      MetricName: 'Accuracy',
      Value: metrics.accuracy,
      Unit: 'Percent',
      Timestamp: timestamp
    },
    {
      MetricName: 'F1Score',
      Value: metrics.f1_score,
      Unit: 'None',
      Timestamp: timestamp
    },
    {
      MetricName: 'InferenceTime',
      Value: metrics.inference_time_ms,
      Unit: 'Milliseconds',
      Timestamp: timestamp
    },
    {
      MetricName: 'ModelEvaluationPassed',
      Value: evaluation.passed ? 1 : 0,
      Unit: 'Count',
      Timestamp: timestamp
    }
  ];
  
  await cloudWatch.putMetricData({
    Namespace: 'PetPlantr/ModelTraining',
    MetricData: metricData
  }).promise();
}

async function storeEvaluationResults(
  jobId: string,
  evaluation: EvaluationResult
): Promise<void> {
  const bucketName = process.env.S3_MODEL_BUCKET!;
  const evaluationKey = `jobs/${jobId}/evaluation-results.json`;
  
  const evaluationData = {
    ...evaluation,
    evaluatedAt: new Date().toISOString(),
    evaluatedBy: 'lambda-evaluateMetrics'
  };
  
  await s3.upload({
    Bucket: bucketName,
    Key: evaluationKey,
    Body: JSON.stringify(evaluationData, null, 2),
    ContentType: 'application/json'
  }).promise();
}
