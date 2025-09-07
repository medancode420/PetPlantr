/**
 * Lambda 6: Traffic Shift
 * Evaluates canary performance and promotes to 100% or rolls back
 */

import { Context } from 'aws-lambda';
import AWS from 'aws-sdk';

const s3 = new AWS.S3();
const cloudWatch = new AWS.CloudWatch();
const lambda = new AWS.Lambda();

interface TrafficShiftEvent {
  action: string;
  jobId: string;
  canaryConfig?: {
    candidateModelKey: string;
    productionModelKey: string;
    trafficSplit: number;
    rollbackThresholds: {
      errorRate: number;
      thumbsDownRate: number;
      latencyIncrease: number;
    };
  };
}

interface CanaryMetrics {
  errorRate: number;
  thumbsDownRate: number;
  latencyIncrease: number;
  requestCount: number;
  successfulGenerations: number;
}

export const handler = async (
  event: TrafficShiftEvent,
  context: Context
) => {
  console.log('Evaluating traffic shift:', JSON.stringify(event, null, 2));
  
  const { action, jobId, canaryConfig } = event;
  
  try {
    if (action === 'evaluateCanary' && canaryConfig) {
      // Evaluate canary performance after monitoring period
      return await evaluateCanaryAndShift(jobId, canaryConfig);
    } else {
      // Direct rollback or promotion
      return await handleDirectAction(action, jobId);
    }
    
  } catch (error) {
    console.error('Failed to handle traffic shift:', error);
    // In case of error, trigger rollback for safety
    await rollbackToProduction(jobId, 'Traffic shift evaluation failed');
    throw new Error(
      error instanceof Error ? error.message : 'Traffic shift failed'
    );
  }
};

async function evaluateCanaryAndShift(
  jobId: string,
  canaryConfig: any
): Promise<any> {
  console.log(`Evaluating canary performance for job ${jobId}`);
  
  // 1. Collect canary metrics from CloudWatch
  const canaryMetrics = await collectCanaryMetrics();
  
  // 2. Evaluate against thresholds
  const evaluation = evaluateCanaryMetrics(canaryMetrics, canaryConfig.rollbackThresholds);
  
  // 3. Make promotion/rollback decision
  if (evaluation.shouldPromote) {
    // Promote to 100% traffic
    const result = await promoteToProduction(jobId, canaryConfig);
    await notifySlackPromotion(jobId, canaryMetrics, 'promoted');
    return result;
  } else {
    // Rollback to previous model
    const result = await rollbackToProduction(jobId, evaluation.reason);
    await notifySlackPromotion(jobId, canaryMetrics, 'rolled_back', evaluation.reason);
    return result;
  }
}

async function collectCanaryMetrics(): Promise<CanaryMetrics> {
  const endTime = new Date();
  const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000); // Last 24 hours
  
  try {
    // Get error rate
    const errorRateData = await cloudWatch.getMetricStatistics({
      Namespace: 'PetPlantr/CanaryDeployment',
      MetricName: 'ErrorRate',
      StartTime: startTime,
      EndTime: endTime,
      Period: 3600, // 1 hour periods
      Statistics: ['Average']
    }).promise();
    
    // Get thumbs down rate (key metric from requirements)
    const thumbsDownData = await cloudWatch.getMetricStatistics({
      Namespace: 'PetPlantr/CanaryDeployment',
      MetricName: 'ThumbsDownRate',
      StartTime: startTime,
      EndTime: endTime,
      Period: 3600,
      Statistics: ['Average']
    }).promise();
    
    // Get latency data
    const latencyData = await cloudWatch.getMetricStatistics({
      Namespace: 'PetPlantr/CanaryDeployment',
      MetricName: 'AverageLatency',
      StartTime: startTime,
      EndTime: endTime,
      Period: 3600,
      Statistics: ['Average']
    }).promise();
    
    // Get request count
    const requestCountData = await cloudWatch.getMetricStatistics({
      Namespace: 'PetPlantr/CanaryDeployment',
      MetricName: 'RequestCount',
      StartTime: startTime,
      EndTime: endTime,
      Period: 3600,
      Statistics: ['Sum']
    }).promise();
    
    // Calculate averages
    const errorRate = errorRateData.Datapoints?.length 
      ? errorRateData.Datapoints.reduce((sum, dp) => sum + (dp.Average || 0), 0) / errorRateData.Datapoints.length
      : 0;
      
    const thumbsDownRate = thumbsDownData.Datapoints?.length
      ? thumbsDownData.Datapoints.reduce((sum, dp) => sum + (dp.Average || 0), 0) / thumbsDownData.Datapoints.length
      : 0;
      
    const latencyIncrease = latencyData.Datapoints?.length
      ? latencyData.Datapoints.reduce((sum, dp) => sum + (dp.Average || 0), 0) / latencyData.Datapoints.length
      : 0;
      
    const requestCount = requestCountData.Datapoints?.length
      ? requestCountData.Datapoints.reduce((sum, dp) => sum + (dp.Sum || 0), 0)
      : 0;
    
    return {
      errorRate,
      thumbsDownRate,
      latencyIncrease,
      requestCount,
      successfulGenerations: requestCount * (1 - errorRate / 100)
    };
    
  } catch (error) {
    console.error('Failed to collect canary metrics:', error);
    // Return safe defaults that will trigger rollback
    return {
      errorRate: 100,
      thumbsDownRate: 100,
      latencyIncrease: 100,
      requestCount: 0,
      successfulGenerations: 0
    };
  }
}

function evaluateCanaryMetrics(
  metrics: CanaryMetrics,
  thresholds: any
): { shouldPromote: boolean; reason: string } {
  // Check thumbs down rate (key requirement: < 15%)
  if (metrics.thumbsDownRate > thresholds.thumbsDownRate) {
    return {
      shouldPromote: false,
      reason: `Thumbs down rate (${metrics.thumbsDownRate.toFixed(2)}%) exceeds threshold (${thresholds.thumbsDownRate}%)`
    };
  }
  
  // Check error rate
  if (metrics.errorRate > thresholds.errorRate) {
    return {
      shouldPromote: false,
      reason: `Error rate (${metrics.errorRate.toFixed(2)}%) exceeds threshold (${thresholds.errorRate}%)`
    };
  }
  
  // Check latency increase
  if (metrics.latencyIncrease > thresholds.latencyIncrease) {
    return {
      shouldPromote: false,
      reason: `Latency increase (${metrics.latencyIncrease.toFixed(2)}%) exceeds threshold (${thresholds.latencyIncrease}%)`
    };
  }
  
  // Check minimum request volume
  if (metrics.requestCount < 10) {
    return {
      shouldPromote: false,
      reason: `Insufficient traffic volume (${metrics.requestCount} requests) for confident evaluation`
    };
  }
  
  return {
    shouldPromote: true,
    reason: 'All metrics within acceptable thresholds'
  };
}

async function promoteToProduction(jobId: string, canaryConfig: any): Promise<any> {
  console.log(`Promoting canary to production for job ${jobId}`);
  
  const bucketName = process.env.S3_MODEL_BUCKET!;
  
  // 1. Copy canary model to production location
  await s3.copyObject({
    Bucket: bucketName,
    CopySource: `${bucketName}/models/canary/unet_canary.pth`,
    Key: 'models/prod/unet_latest.pth',
    Metadata: {
      'promoted-from': canaryConfig.candidateModelKey,
      'promoted-at': new Date().toISOString(),
      'job-id': jobId,
      'deployment-type': 'production'
    },
    MetadataDirective: 'REPLACE'
  }).promise();
  
  // 2. Update Lambda function to use production model (100% traffic)
  await updateTrafficToProduction();
  
  // 3. Clean up canary deployment
  await cleanupCanaryDeployment(jobId);
  
  // 4. Update baseline metrics for future comparisons
  await updateBaselineMetrics(canaryConfig.candidateModelKey);
  
  return {
    action: 'promoted',
    newProductionModel: 'models/prod/unet_latest.pth',
    trafficSplit: '100% production',
    jobId
  };
}

async function rollbackToProduction(jobId: string, reason: string): Promise<any> {
  console.log(`Rolling back canary deployment for job ${jobId}: ${reason}`);
  
  // 1. Update Lambda function to disable canary (100% production traffic)
  await updateTrafficToProduction();
  
  // 2. Clean up canary deployment
  await cleanupCanaryDeployment(jobId);
  
  return {
    action: 'rolled_back',
    reason,
    trafficSplit: '100% production',
    jobId
  };
}

async function updateTrafficToProduction(): Promise<void> {
  const generateSTLFunctionName = process.env.GENERATE_STL_FUNCTION_NAME || 'petplantr-generateSTL';
  
  try {
    const functionConfig = await lambda.getFunctionConfiguration({
      FunctionName: generateSTLFunctionName
    }).promise();
    
    const updatedEnvironment = {
      ...functionConfig.Environment?.Variables,
      CANARY_ENABLED: 'false',
      CANARY_TRAFFIC_PERCENTAGE: '0',
      PRODUCTION_MODEL_KEY: 'models/prod/unet_latest.pth'
    };
    
    // Remove canary-specific variables
    delete (updatedEnvironment as any).CANARY_MODEL_KEY;
    delete (updatedEnvironment as any).CANARY_DEPLOYED_AT;
    
    await lambda.updateFunctionConfiguration({
      FunctionName: generateSTLFunctionName,
      Environment: {
        Variables: updatedEnvironment
      }
    }).promise();
    
    console.log('Traffic routing updated to 100% production');
    
  } catch (error) {
    console.error('Failed to update traffic routing:', error);
    throw error;
  }
}

async function cleanupCanaryDeployment(jobId: string): Promise<void> {
  // 1. Remove CloudWatch alarms
  const alarmNames = [
    'PetPlantr-Canary-ErrorRate',
    'PetPlantr-Canary-ThumbsDownRate',
    'PetPlantr-Canary-Latency'
  ];
  
  for (const alarmName of alarmNames) {
    try {
      await cloudWatch.deleteAlarms({
        AlarmNames: [alarmName]
      }).promise();
    } catch (error) {
      console.error(`Failed to delete alarm ${alarmName}:`, error);
    }
  }
  
  // 2. Remove scheduled evaluation rule
  const eventBridge = new AWS.EventBridge();
  const ruleName = `petplantr-canary-evaluation-${jobId}`;
  
  try {
    await eventBridge.removeTargets({
      Rule: ruleName,
      Ids: ['1']
    }).promise();
    
    await eventBridge.deleteRule({
      Name: ruleName
    }).promise();
  } catch (error) {
    console.error(`Failed to cleanup EventBridge rule ${ruleName}:`, error);
  }
  
  console.log('Canary deployment cleanup completed');
}

async function updateBaselineMetrics(candidateModelKey: string): Promise<void> {
  const bucketName = process.env.S3_MODEL_BUCKET!;
  const metricsKey = candidateModelKey.replace('.pth', '_metrics.json');
  
  try {
    // Copy candidate metrics to baseline
    await s3.copyObject({
      Bucket: bucketName,
      CopySource: `${bucketName}/${metricsKey}`,
      Key: 'models/baseline_metrics.json',
      Metadata: {
        'promoted-from': candidateModelKey,
        'updated-at': new Date().toISOString()
      },
      MetadataDirective: 'REPLACE'
    }).promise();
    
    console.log('Baseline metrics updated');
  } catch (error) {
    console.error('Failed to update baseline metrics:', error);
  }
}

async function handleDirectAction(action: string, jobId: string): Promise<any> {
  switch (action) {
    case 'rollback':
      return await rollbackToProduction(jobId, 'Manual rollback requested');
    case 'promote':
      // For direct promotion, we need to load canary config
      // This would typically come from stored job data
      return { action: 'promotion_requires_canary_config' };
    default:
      throw new Error(`Unknown action: ${action}`);
  }
}

async function notifySlackPromotion(
  jobId: string,
  metrics: CanaryMetrics,
  action: 'promoted' | 'rolled_back',
  reason?: string
): Promise<void> {
  try {
    const slackWebhook = process.env.SLACK_WEBHOOK_MODEL;
    if (!slackWebhook) return;
    
    const isPromotion = action === 'promoted';
    const emoji = isPromotion ? '🎉' : '⚠️';
    const title = isPromotion ? 'Model Promoted to Production' : 'Canary Rolled Back';
    
    const message = {
      text: `${emoji} ${title}`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*${title}*${reason ? `\n_${reason}_` : ''}`
          }
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*Job ID:*\n${jobId}`
            },
            {
              type: 'mrkdwn',
              text: `*Action:*\n${action}`
            },
            {
              type: 'mrkdwn',
              text: `*Error Rate:*\n${metrics.errorRate.toFixed(2)}%`
            },
            {
              type: 'mrkdwn',
              text: `*Thumbs Down Rate:*\n${metrics.thumbsDownRate.toFixed(2)}%`
            }
          ]
        }
      ]
    };
    
    await fetch(slackWebhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message)
    });
    
  } catch (error) {
    console.error('Slack notification error:', error);
  }
}
