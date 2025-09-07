import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';
import { logger } from '../utils/enhancedLogger';
import { ValidationError } from '../utils/enhancedErrorHandler';
import { lambdaSchemas } from '../utils/validation';

const sns = new SNSClient({ region: 'us-east-1' });

interface NotifyPrinterInput {
  orderId: string;
  userId: string;
  readyStlKey: string;
  sizeTier: string;
  stlBucket?: string;
}

interface NotifyPrinterOutput {
  orderId: string;
  printJobId: string;
  status: string;
  queuedAt: string;
}

export const handler = async (event: NotifyPrinterInput): Promise<NotifyPrinterOutput> => {
  const correlationId = Date.now().toString();
  logger.info('NotifyPrinter Lambda started', { event, correlationId });

  try {
    // Validate input
    const { error, value } = lambdaSchemas.notifyPrinter.validate(event);
    if (error) {
      logger.error('Invalid input data', { error: error.message, correlationId });
      throw new ValidationError(`Invalid input data: ${error.message}`);
    }

    const { orderId, userId, readyStlKey, sizeTier, stlBucket = 'petplantr-stl-ready-dev' } = value;

    // Generate print job ID
    const printJobId = `print-${orderId}-${Date.now()}`;

    // Prepare print job message for K1 Max bridge
    const printJobMessage = {
      bucket: stlBucket,
      key: readyStlKey,
      orderId,
      userId,
      sizeTier,
      printer: "k1max-01", // Route hint for printer selection
      printJobId,
      priority: "normal", // Could be "high" for premium orders
      timestamp: new Date().toISOString()
    };

    // Send to print queue SNS topic
    const topicArn = process.env.PRINT_QUEUE_TOPIC_ARN;
    if (!topicArn) {
      throw new ValidationError('PRINT_QUEUE_TOPIC_ARN environment variable not set');
    }

    const publishCommand = new PublishCommand({
      TopicArn: topicArn,
      Message: JSON.stringify(printJobMessage),
      Subject: `Print Job - Order ${orderId}`,
      MessageAttributes: {
        orderId: {
          DataType: 'String',
          StringValue: orderId
        },
        printer: {
          DataType: 'String', 
          StringValue: 'k1max-01'
        },
        priority: {
          DataType: 'String',
          StringValue: 'normal'
        }
      }
    });

    await sns.send(publishCommand);

    logger.info(`Print job ${printJobId} queued successfully`, { 
      orderId, 
      printJobId, 
      correlationId 
    });

    const result: NotifyPrinterOutput = {
      orderId,
      printJobId,
      status: 'QUEUED',
      queuedAt: new Date().toISOString()
    };

    logger.info('NotifyPrinter Lambda completed', { result, correlationId });
    return result;

  } catch (error) {
    logger.error('NotifyPrinter Lambda failed', { 
      error: error instanceof Error ? error.message : String(error),
      correlationId 
    });
    
    throw error;
  }
};
