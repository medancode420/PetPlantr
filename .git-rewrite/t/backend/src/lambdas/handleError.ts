interface HandleErrorInput {
  orderId: string;
  userId: string;
  error: any;
  cause: any;
  status: string;
}

interface HandleErrorOutput {
  orderId: string;
  userId: string;
  status: string;
  handledAt: string;
  errorDetails: {
    type: string;
    message: string;
    step: string;
  };
  notificationsSent: string[];
}

export const handler = async (event: HandleErrorInput): Promise<HandleErrorOutput> => {
  console.log('HandleError Lambda Input:', JSON.stringify(event, null, 2));

  const { orderId, userId, error, cause, status } = event;

  try {
    // Parse error information
    const errorDetails = parseErrorDetails(error, cause);
    const notificationsSent: string[] = [];

    // Log the error
    console.error(`Order processing failed for ${orderId}:`, {
      orderId,
      userId,
      errorType: errorDetails.type,
      errorMessage: errorDetails.message,
      step: errorDetails.step,
      timestamp: new Date().toISOString(),
    });

    // Send Slack alert for operations team
    if (process.env.SLACK_WEBHOOK_URL) {
      try {
        const slackMessage = {
          text: `🚨 Order Processing Failed: ${orderId}`,
          channel: '#ops-alerts',
          attachments: [
            {
              color: 'danger',
              fields: [
                { title: 'Order ID', value: orderId, short: true },
                { title: 'User ID', value: userId, short: true },
                { title: 'Error Type', value: errorDetails.type, short: true },
                { title: 'Failed Step', value: errorDetails.step, short: true },
                { title: 'Error Message', value: errorDetails.message, short: false },
                { title: 'Timestamp', value: new Date().toISOString(), short: true },
              ],
            },
            {
              color: 'warning',
              text: 'Manual intervention may be required. Check order processing pipeline.',
            },
          ],
        };

        const response = await fetch(process.env.SLACK_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(slackMessage),
        });

        if (response.ok) {
          notificationsSent.push('slack:ops-alerts');
          console.log('Error alert sent to Slack');
        }
      } catch (slackError) {
        console.error('Failed to send Slack error alert:', slackError);
      }
    }

    // Send customer notification about the issue (optional)
    if (shouldNotifyCustomer(errorDetails.type)) {
      try {
        await sendCustomerErrorNotification(orderId, userId, errorDetails);
        notificationsSent.push('customer:email');
      } catch (emailError) {
        console.error('Failed to send customer error notification:', emailError);
      }
    }

    // Log error to CloudWatch for monitoring/alerting
    const errorLog = {
      orderId,
      userId,
      errorType: errorDetails.type,
      errorMessage: errorDetails.message,
      step: errorDetails.step,
      timestamp: new Date().toISOString(),
      severity: getSeverityLevel(errorDetails.type),
    };

    // In a real implementation, you might also:
    // 1. Save error to DynamoDB for tracking
    // 2. Trigger retry mechanism for transient errors
    // 3. Create support ticket for manual intervention
    // 4. Update order status in database

    console.log('Error handling complete:', errorLog);

    const result: HandleErrorOutput = {
      orderId,
      userId,
      status: 'ERROR_HANDLED',
      handledAt: new Date().toISOString(),
      errorDetails,
      notificationsSent,
    };

    console.log('HandleError Lambda Output:', JSON.stringify(result, null, 2));
    return result;

  } catch (handlingError) {
    console.error('Error handling failed:', handlingError);
    
    // This is a critical error - error handler itself failed
    throw {
      errorType: 'ErrorHandlingError',
      errorMessage: handlingError instanceof Error ? handlingError.message : 'Unknown error',
      originalError: error,
      orderId,
      userId,
      timestamp: new Date().toISOString(),
    };
  }
};

function parseErrorDetails(error: any, cause: any): { type: string; message: string; step: string } {
  // Try to extract meaningful error information
  let errorType = 'UnknownError';
  let errorMessage = 'An unknown error occurred';
  let step = 'Unknown';

  if (error && typeof error === 'object') {
    errorType = error.errorType || error.Error || 'ProcessingError';
    errorMessage = error.errorMessage || error.Cause || error.message || 'Processing failed';
  }

  if (cause && typeof cause === 'string') {
    try {
      const causeData = JSON.parse(cause);
      if (causeData.errorMessage) {
        errorMessage = causeData.errorMessage;
      }
    } catch {
      // Cause is not JSON, use as-is
      errorMessage = cause;
    }
  }

  // Determine which step failed based on error type
  if (errorType.includes('DownloadPhotos')) {
    step = 'DownloadPhotos';
  } else if (errorType.includes('GenerateSTL')) {
    step = 'GenerateSTL';
  } else if (errorType.includes('ProcessSTL')) {
    step = 'ProcessSTL';
  } else if (errorType.includes('NotifyCustomer')) {
    step = 'NotifyCustomer';
  } else {
    step = 'Validation';
  }

  return { type: errorType, message: errorMessage, step };
}

function shouldNotifyCustomer(errorType: string): boolean {
  // Only notify customer for certain types of errors
  const customerNotificationErrors = [
    'GenerateSTLError',
    'ProcessSTLError',
    'ValidationError'
  ];
  
  return customerNotificationErrors.some(type => errorType.includes(type));
}

async function sendCustomerErrorNotification(orderId: string, userId: string, errorDetails: any): Promise<void> {
  // In a real implementation, this would:
  // 1. Get customer email from Clerk
  // 2. Send apologetic email with next steps
  // 3. Offer refund or reprocessing options
  
  console.log(`Would send customer error notification for order ${orderId}:`, errorDetails);
  
  // Mock implementation
  if (process.env.MOCK_CUSTOMER_EMAIL) {
    console.log(`Customer notification sent to ${process.env.MOCK_CUSTOMER_EMAIL}`);
  }
}

function getSeverityLevel(errorType: string): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
  if (errorType.includes('NotifyCustomer')) {
    return 'LOW'; // Order succeeded but notification failed
  } else if (errorType.includes('DownloadPhotos')) {
    return 'MEDIUM'; // Input validation issue
  } else if (errorType.includes('GenerateSTL') || errorType.includes('ProcessSTL')) {
    return 'HIGH'; // Core processing failure
  } else {
    return 'CRITICAL'; // Unknown or system error
  }
}
