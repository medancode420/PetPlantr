/**
 * Lambda 5: Canary Deploy
 * Deploys the new model as a canary (10% traffic) with monitoring
 */

import { Context } from 'aws-lambda';
import AWS from 'aws-sdk';

const s3 = new AWS.S3();
const cloudWatch = new AWS.CloudWatch();
const lambda = new AWS.Lambda();

interface CanaryDeployEvent {
  evaluation: {
    passed: boolean;
    decision: string;
    reason: string;
  };
  candidateModelKey: string;
  jobId: string;
}

interface CanaryConfig {
  candidateModelKey: string;
  productionModelKey: string;
  trafficSplit: number; // Percentage for canary
  monitoringDuration: number; // Minutes
  rollbackThresholds: {
    errorRate: number;
    thumbsDownRate: number;
    latencyIncrease: number;
  };
}

export const handler = async (
  event: CanaryDeployEvent,
  context: Context
) => {
  console.log('Starting canary deployment:', JSON.stringify(event, null, 2));
  
  const { evaluation, candidateModelKey, jobId } = event;
  
  try {
    // 1. Check if model should be deployed
    if (!evaluation.passed || evaluation.decision !== 'promote') {
      console.log(`Skipping canary deployment: ${evaluation.reason}`);
      await notifySlackRollback(jobId, evaluation.reason);
      return {
        action: 'skipped',
        reason: evaluation.reason,
        nextAction: 'trafficShift'
      };
    }
    
    // 2. Prepare canary configuration
    const canaryConfig = await prepareCanaryConfig(candidateModelKey, jobId);
    
    // 3. Deploy canary model
    await deployCanaryModel(canaryConfig);
    
    // 4. Update traffic routing (10% to canary)
    await updateTrafficRouting(canaryConfig);
    
    // 5. Set up monitoring and alarms
    await setupCanaryMonitoring(canaryConfig);
    
    // 6. Schedule evaluation check
    await scheduleCanaryEvaluation(canaryConfig, jobId);
    
    // 7. Notify Slack of canary deployment
    await notifySlackCanaryDeployed(jobId, canaryConfig);
    
    const result = {
      canaryDeployed: true,
      canaryConfig,
      monitoringDuration: `${canaryConfig.monitoringDuration} minutes`,
      trafficSplit: `${canaryConfig.trafficSplit}% canary`,
      nextEvaluation: new Date(Date.now() + canaryConfig.monitoringDuration * 60000).toISOString(),
      nextAction: 'monitorCanary'
    };
    
    console.log('Canary deployment result:', result);
    return result;
    
  } catch (error) {
    console.error('Failed to deploy canary:', error);
    await notifySlackRollback(jobId, error instanceof Error ? error.message : 'Canary deployment failed');
    throw new Error(
      error instanceof Error ? error.message : 'Canary deployment failed'
    );
  }
};

async function prepareCanaryConfig(
  candidateModelKey: string,
  jobId: string
): Promise<CanaryConfig> {
  return {
    candidateModelKey,
    productionModelKey: 'models/prod/unet_latest.pth',
    trafficSplit: 10, // 10% as specified in requirements
    monitoringDuration: 24 * 60, // 24 hours monitoring
    rollbackThresholds: {
      errorRate: 5.0, // 5% error rate threshold
      thumbsDownRate: 15.0, // 15% thumbs down rate as specified
      latencyIncrease: 50.0 // 50% latency increase threshold
    }
  };
}

async function deployCanaryModel(config: CanaryConfig): Promise<void> {
  const bucketName = process.env.S3_MODEL_BUCKET!;
  
  // Copy candidate model to canary location
  const canaryModelKey = 'models/canary/unet_canary.pth';
  
  await s3.copyObject({
    Bucket: bucketName,
    CopySource: `${bucketName}/${config.candidateModelKey}`,
    Key: canaryModelKey,
    Metadata: {
      'deployment-type': 'canary',
      'traffic-split': config.trafficSplit.toString(),
      'deployed-at': new Date().toISOString(),
      'source-model': config.candidateModelKey
    },
    MetadataDirective: 'REPLACE'
  }).promise();
  
  console.log(`Canary model deployed to ${canaryModelKey}`);
}

async function updateTrafficRouting(config: CanaryConfig): Promise<void> {
  // Update Lambda environment variables for traffic routing
  const generateSTLFunctionName = process.env.GENERATE_STL_FUNCTION_NAME || 'petplantr-generateSTL';
  
  try {
    // Get current function configuration
    const functionConfig = await lambda.getFunctionConfiguration({
      FunctionName: generateSTLFunctionName
    }).promise();
    
    // Update environment variables with canary routing
    const updatedEnvironment = {
      ...functionConfig.Environment?.Variables,
      CANARY_ENABLED: 'true',
      CANARY_TRAFFIC_PERCENTAGE: config.trafficSplit.toString(),
      CANARY_MODEL_KEY: 'models/canary/unet_canary.pth',
      PRODUCTION_MODEL_KEY: config.productionModelKey,
      CANARY_DEPLOYED_AT: new Date().toISOString()
    };
    
    await lambda.updateFunctionConfiguration({
      FunctionName: generateSTLFunctionName,
      Environment: {
        Variables: updatedEnvironment
      }
    }).promise();
    
    console.log(`Traffic routing updated: ${config.trafficSplit}% to canary`);
    
  } catch (error) {
    console.error('Failed to update traffic routing:', error);
    throw error;
  }
}

async function setupCanaryMonitoring(config: CanaryConfig): Promise<void> {
  const alarms = [
    // Error rate alarm
    {
      AlarmName: 'PetPlantr-Canary-ErrorRate',
      AlarmDescription: 'Canary model error rate exceeds threshold',
      MetricName: 'ErrorRate',
      Threshold: config.rollbackThresholds.errorRate,
      ComparisonOperator: 'GreaterThanThreshold'
    },
    // Thumbs down rate alarm (key metric from requirements)
    {
      AlarmName: 'PetPlantr-Canary-ThumbsDownRate',
      AlarmDescription: 'Canary model thumbs down rate exceeds 15%',
      MetricName: 'ThumbsDownRate',
      Threshold: config.rollbackThresholds.thumbsDownRate,
      ComparisonOperator: 'GreaterThanThreshold'
    },
    // Latency alarm
    {
      AlarmName: 'PetPlantr-Canary-Latency',
      AlarmDescription: 'Canary model latency increase exceeds threshold',
      MetricName: 'AverageLatency',
      Threshold: config.rollbackThresholds.latencyIncrease,
      ComparisonOperator: 'GreaterThanThreshold'
    }
  ];
  
  for (const alarm of alarms) {
    await cloudWatch.putMetricAlarm({
      AlarmName: alarm.AlarmName,
      AlarmDescription: alarm.AlarmDescription,
      ActionsEnabled: true,
      MetricName: alarm.MetricName,
      Namespace: 'PetPlantr/CanaryDeployment',
      Statistic: 'Average',
      Period: 300, // 5 minutes
      EvaluationPeriods: 2,
      Threshold: alarm.Threshold,
      ComparisonOperator: alarm.ComparisonOperator,
      AlarmActions: [
        // SNS topic for automatic rollback
        process.env.CANARY_ROLLBACK_SNS_TOPIC || ''
      ].filter(Boolean)
    }).promise();
  }
  
  console.log('Canary monitoring alarms created');
}

async function scheduleCanaryEvaluation(
  config: CanaryConfig,
  jobId: string
): Promise<void> {
  const eventBridge = new AWS.EventBridge();
  
  const ruleName = `petplantr-canary-evaluation-${jobId}`;
  const evaluationTime = new Date(Date.now() + config.monitoringDuration * 60000);
  
  // Create scheduled rule for canary evaluation
  await eventBridge.putRule({
    Name: ruleName,
    Description: `Evaluate canary deployment for job ${jobId}`,
    ScheduleExpression: `at(${evaluationTime.toISOString().slice(0, -5)})`,
    State: 'ENABLED'
  }).promise();
  
  // Add target to trigger evaluation lambda
  await eventBridge.putTargets({
    Rule: ruleName,
    Targets: [{
      Id: '1',
      Arn: process.env.TRAFFIC_SHIFT_LAMBDA_ARN || '',
      Input: JSON.stringify({
        action: 'evaluateCanary',
        jobId,
        canaryConfig: config
      })
    }]
  }).promise();
  
  console.log(`Canary evaluation scheduled for ${evaluationTime.toISOString()}`);
}

async function notifySlackCanaryDeployed(
  jobId: string,
  config: CanaryConfig
): Promise<void> {
  try {
    const slackWebhook = process.env.SLACK_WEBHOOK_MODEL;
    if (!slackWebhook) {
      console.log('No Slack webhook configured');
      return;
    }
    
    const message = {
      text: '🚀 Canary Deployment Successful',
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Fine-tune succeeded & canary at ${config.trafficSplit}%*`
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
              text: `*Traffic Split:*\n${config.trafficSplit}% canary`
            },
            {
              type: 'mrkdwn',
              text: `*Monitoring Duration:*\n${config.monitoringDuration / 60} hours`
            },
            {
              type: 'mrkdwn',
              text: `*Model Key:*\n${config.candidateModelKey}`
            }
          ]
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Rollback Thresholds:*\n• Error Rate: ${config.rollbackThresholds.errorRate}%\n• Thumbs Down: ${config.rollbackThresholds.thumbsDownRate}%\n• Latency: +${config.rollbackThresholds.latencyIncrease}%`
          }
        }
      ]
    };
    
    const response = await fetch(slackWebhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message)
    });
    
    if (!response.ok) {
      console.error('Failed to send Slack notification');
    }
    
  } catch (error) {
    console.error('Slack notification error:', error);
  }
}

async function notifySlackRollback(jobId: string, reason: string): Promise<void> {
  try {
    const slackWebhook = process.env.SLACK_WEBHOOK_MODEL;
    if (!slackWebhook) return;
    
    const message = {
      text: '⚠️ Canary Deployment Skipped',
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Model training completed but deployment skipped*`
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
              text: `*Reason:*\n${reason}`
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
