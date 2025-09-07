import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import EnhancedEmailService from '../services/enhancedEmailService';

const ses = new SESClient({ region: 'us-east-1' });
const s3 = new S3Client({ region: 'us-east-1' });
const emailService = new EnhancedEmailService();

interface NotifyCustomerInput {
  orderId: string;
  userId: string;
  readyStlKey: string;
  status: string;
  printingSpecs?: {
    layerHeight: number;
    infill: number;
    supports: boolean;
    estimatedPrintTime: string;
    filamentUsage: string;
  };
}

interface NotifyCustomerOutput {
  orderId: string;
  userId: string;
  status: string;
  notifiedAt: string;
  notificationsSent: string[];
}

export const handler = async (event: NotifyCustomerInput): Promise<NotifyCustomerOutput> => {
  console.log('NotifyCustomer Lambda Input:', JSON.stringify(event, null, 2));

  const { orderId, userId, readyStlKey, status, printingSpecs } = event;

  try {
    // Validate input
    if (!orderId || !userId || !readyStlKey) {
      throw new Error('Missing required parameters');
    }

    const notificationsSent: string[] = [];

    // Generate presigned URL for STL download
    const downloadUrl = await getSignedUrl(
      s3,
      new GetObjectCommand({
        Bucket: 'petplantr-stl-ready-dev', // Use appropriate bucket
        Key: readyStlKey,
      }),
      { expiresIn: 7 * 24 * 60 * 60 } // 7 days
    );

    // Mock customer email (in real app, fetch from Clerk)
    const customerEmail = process.env.MOCK_CUSTOMER_EMAIL || 'customer@example.com';
    const customerName = 'Valued Customer'; // In real app, get from Clerk API

    // Send professional email via Microsoft Graph (Daniel@PetPlantr.com)
    const emailSuccess = await emailService.sendOrderCompletion(
      { email: customerEmail, name: customerName },
      {
        orderId,
        userId,
        downloadUrl,
        printingSpecs
      }
    );

    if (emailSuccess) {
      notificationsSent.push(`email:${customerEmail}`);
      // Don't assume Microsoft Graph was used - the service handles fallback internally
    } else {
      console.warn('Failed to send email via enhanced service, trying fallback...');
      
      // Fallback to original SES implementation
      if (process.env.SES_ENABLED === 'true') {
        try {
          const emailContent = generateCompletionEmail(orderId, readyStlKey, printingSpecs);
          const sendEmailCommand = new SendEmailCommand({
            Source: process.env.SENDER_EMAIL || 'noreply@petplantr.com',
            Destination: {
              ToAddresses: [customerEmail],
            },
            Message: {
              Subject: {
                Data: `🎉 Your PetPlantr is Ready! Order #${orderId}`,
                Charset: 'UTF-8',
              },
              Body: {
                Html: {
                  Data: emailContent.html,
                  Charset: 'UTF-8',
                },
                Text: {
                  Data: emailContent.text,
                  Charset: 'UTF-8',
                },
              },
            },
          });

          await ses.send(sendEmailCommand);
          notificationsSent.push(`email:${customerEmail}`);
          console.log(`Fallback SES email sent to ${customerEmail}`);
        } catch (emailError) {
          console.error('Failed to send fallback email:', emailError);
        }
      }
    }

    // Send Slack notification to ops team
    if (process.env.SLACK_WEBHOOK_URL) {
      try {
        const slackMessage = {
          text: `🎉 PRINT_DONE – order *${orderId}* auto-ejected on P1P-01`,
          channel: '#ops-alerts',
          attachments: [
            {
              color: 'good',
              fields: [
                { title: 'Order ID', value: orderId, short: true },
                { title: 'User ID', value: userId, short: true },
                { title: 'Status', value: status, short: true },
                { title: 'STL File', value: readyStlKey, short: false },
                {
                  title: 'Print Specs',
                  value: printingSpecs
                    ? `Layer: ${printingSpecs.layerHeight}mm, Infill: ${printingSpecs.infill}%, Time: ${printingSpecs.estimatedPrintTime}`
                    : 'N/A',
                  short: false,
                },
              ],
            },
          ],
        };

        const response = await fetch(process.env.SLACK_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(slackMessage),
        });

        if (response.ok) {
          notificationsSent.push('slack:ops-team');
          console.log('Slack notification sent');
        }
      } catch (slackError) {
        console.error('Failed to send Slack notification:', slackError);
      }
    }

    // Log completion
    console.log(`Order ${orderId} completed successfully. Notifications sent: ${notificationsSent.join(', ')}`);

    const result: NotifyCustomerOutput = {
      orderId,
      userId,
      status: 'NOTIFIED',
      notifiedAt: new Date().toISOString(),
      notificationsSent,
    };

    console.log('NotifyCustomer Lambda Output:', JSON.stringify(result, null, 2));
    return result;

  } catch (error) {
    console.error('NotifyCustomer Lambda Error:', error);
    
    throw {
      errorType: 'NotifyCustomerError',
      errorMessage: error instanceof Error ? error.message : 'Unknown error',
      orderId,
      userId,
      timestamp: new Date().toISOString(),
    };
  }
};

function generateCompletionEmail(orderId: string, readyStlKey: string, printingSpecs?: any) {
  const text = `
Hi there!

Great news! Your custom PetPlantr is ready for 3D printing!

Order Details:
- Order ID: ${orderId}
- STL File: ${readyStlKey}
${printingSpecs ? `
Printing Specifications:
- Layer Height: ${printingSpecs.layerHeight}mm
- Infill: ${printingSpecs.infill}%
- Supports: ${printingSpecs.supports ? 'Yes' : 'No'}
- Estimated Print Time: ${printingSpecs.estimatedPrintTime}
- Filament Usage: ${printingSpecs.filamentUsage}
` : ''}

Next Steps:
1. Download your STL file from the link in your account
2. Load it into your 3D printer software
3. Print with the recommended settings above
4. Enjoy your custom PetPlantr!

If you have any questions, feel free to reach out to our support team.

Happy printing!
The PetPlantr Team
`;

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Your PetPlantr is Ready!</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #2E7D32;">🎉 Your PetPlantr is Ready!</h1>
    
    <p>Great news! Your custom PetPlantr is ready for 3D printing!</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
      <h3>Order Details</h3>
      <p><strong>Order ID:</strong> ${orderId}</p>
      <p><strong>STL File:</strong> ${readyStlKey}</p>
    </div>
    
    ${printingSpecs ? `
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
      <h3>Printing Specifications</h3>
      <ul>
        <li><strong>Layer Height:</strong> ${printingSpecs.layerHeight}mm</li>
        <li><strong>Infill:</strong> ${printingSpecs.infill}%</li>
        <li><strong>Supports:</strong> ${printingSpecs.supports ? 'Yes' : 'No'}</li>
        <li><strong>Estimated Print Time:</strong> ${printingSpecs.estimatedPrintTime}</li>
        <li><strong>Filament Usage:</strong> ${printingSpecs.filamentUsage}</li>
      </ul>
    </div>
    ` : ''}
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
      <h3>Next Steps</h3>
      <ol>
        <li>Download your STL file from the link in your account</li>
        <li>Load it into your 3D printer software</li>
        <li>Print with the recommended settings above</li>
        <li>Enjoy your custom PetPlantr!</li>
      </ol>
    </div>
    
    <p>If you have any questions, feel free to reach out to our support team.</p>
    
    <p>Happy printing!<br>
    <strong>The PetPlantr Team</strong></p>
  </div>
</body>
</html>
`;

  return { text, html };
}
