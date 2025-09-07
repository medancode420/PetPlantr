import { Client } from '@microsoft/microsoft-graph-client';
import { AuthenticationProvider } from '@microsoft/microsoft-graph-client';
import { ConfidentialClientApplication } from '@azure/msal-node';

/**
 * Microsoft Graph Service for Office 365 Integration
 * Handles email sending through Daniel@PetPlantr.com account
 */

interface MicrosoftGraphConfig {
  tenantId: string;
  clientId: string;
  clientSecret: string;
  emailAddress: string;
}

interface GraphEmailMessage {
  subject: string;
  body: {
    contentType: 'HTML' | 'Text';
    content: string;
  };
  toRecipients: Array<{
    emailAddress: {
      address: string;
      name?: string;
    };
  }>;
  ccRecipients?: Array<{
    emailAddress: {
      address: string;
      name?: string;
    };
  }>;
  bccRecipients?: Array<{
    emailAddress: {
      address: string;
      name?: string;
    };
  }>;
  importance?: 'low' | 'normal' | 'high';
}

class MSALAuthProvider implements AuthenticationProvider {
  private clientApp: ConfidentialClientApplication;

  constructor(config: MicrosoftGraphConfig) {
    this.clientApp = new ConfidentialClientApplication({
      auth: {
        clientId: config.clientId,
        clientSecret: config.clientSecret,
        authority: `https://login.microsoftonline.com/${config.tenantId}`
      }
    });
  }

  async getAccessToken(): Promise<string> {
    try {
      const response = await this.clientApp.acquireTokenByClientCredential({
        scopes: ['https://graph.microsoft.com/.default']
      });
      
      if (!response?.accessToken) {
        throw new Error('No access token received from MSAL');
      }
      
      return response.accessToken;
    } catch (error) {
      throw new Error(`Failed to acquire Microsoft Graph token: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

export class MicrosoftGraphService {
  private client: Client;
  private fromEmail: string;
  private config: MicrosoftGraphConfig;

  constructor(config: MicrosoftGraphConfig) {
    this.config = config;
    this.fromEmail = config.emailAddress;
    
    const authProvider = new MSALAuthProvider(config);
    this.client = Client.initWithMiddleware({ authProvider });
  }

  /**
   * Create MicrosoftGraphService from configuration
   */
  static async fromConfig(config: MicrosoftGraphConfig): Promise<MicrosoftGraphService> {
    return new MicrosoftGraphService(config);
  }

  /**
   * Send email through Microsoft Graph API
   */
  async sendEmail(message: Omit<GraphEmailMessage, 'from'>): Promise<string> {
    try {
      console.log(`Sending email via Microsoft Graph from ${this.fromEmail}`, {
        to: message.toRecipients.map(r => r.emailAddress.address),
        subject: message.subject
      });

      const emailMessage = {
        message: {
          ...message,
          from: {
            emailAddress: {
              address: this.fromEmail,
              name: 'Daniel from PetPlantr'
            }
          }
        },
        saveToSentItems: true
      };

      await this.client.api('/me/sendMail').post(emailMessage);
      
      console.log('Email sent successfully via Microsoft Graph');
      return 'SUCCESS';
    } catch (error) {
      console.error('Failed to send email via Microsoft Graph:', error);
      throw new Error(`Microsoft Graph email failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Send order completion notification
   */
  async sendOrderCompletionEmail(
    customerEmail: string,
    customerName: string,
    orderId: string,
    downloadUrl: string,
    printingSpecs?: any
  ): Promise<string> {
    const emailContent = this.generateOrderCompletionEmail(orderId, downloadUrl, printingSpecs);
    
    const message: Omit<GraphEmailMessage, 'from'> = {
      subject: `🎉 Your Custom PetPlantr is Ready! Order #${orderId}`,
      body: {
        contentType: 'HTML',
        content: emailContent.html
      },
      toRecipients: [{
        emailAddress: {
          address: customerEmail,
          name: customerName
        }
      }],
      importance: 'normal'
    };

    return await this.sendEmail(message);
  }

  /**
   * Send order confirmation email
   */
  async sendOrderConfirmationEmail(
    customerEmail: string,
    customerName: string,
    orderId: string,
    orderDetails: any
  ): Promise<string> {
    const emailContent = this.generateOrderConfirmationEmail(orderId, orderDetails);
    
    const message: Omit<GraphEmailMessage, 'from'> = {
      subject: `Order Confirmed: PetPlantr #${orderId}`,
      body: {
        contentType: 'HTML',
        content: emailContent.html
      },
      toRecipients: [{
        emailAddress: {
          address: customerEmail,
          name: customerName
        }
      }],
      importance: 'normal'
    };

    return await this.sendEmail(message);
  }

  /**
   * Send order status update email
   */
  async sendOrderStatusEmail(
    customerEmail: string,
    customerName: string,
    orderId: string,
    status: string,
    message: string
  ): Promise<string> {
    const emailContent = this.generateOrderStatusEmail(orderId, status, message);
    
    const emailMessage: Omit<GraphEmailMessage, 'from'> = {
      subject: `Order Update: PetPlantr #${orderId} - ${status}`,
      body: {
        contentType: 'HTML',
        content: emailContent.html
      },
      toRecipients: [{
        emailAddress: {
          address: customerEmail,
          name: customerName
        }
      }],
      importance: 'normal'
    };

    return await this.sendEmail(emailMessage);
  }

  /**
   * Send internal notification to Daniel
   */
  async sendInternalNotification(
    subject: string,
    htmlContent: string,
    priority: 'low' | 'normal' | 'high' = 'normal'
  ): Promise<string> {
    const message: Omit<GraphEmailMessage, 'from'> = {
      subject: `[PetPlantr Alert] ${subject}`,
      body: {
        contentType: 'HTML',
        content: htmlContent
      },
      toRecipients: [{
        emailAddress: {
          address: 'Daniel@PetPlantr.com',
          name: 'Daniel (PetPlantr)'
        }
      }],
      importance: priority
    };

    return await this.sendEmail(message);
  }

  /**
   * Generate order completion email content
   */
  private generateOrderCompletionEmail(orderId: string, downloadUrl: string, printingSpecs?: any) {
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Your PetPlantr is Ready!</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #2E7D32, #4CAF50); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .download-btn { background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; }
    .specs-table { width: 100%; border-collapse: collapse; }
    .specs-table td { padding: 10px; border-bottom: 1px solid #eee; }
    .specs-table td:first-child { font-weight: bold; color: #2E7D32; }
    .footer { text-align: center; padding: 20px; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎉 Your PetPlantr is Ready!</h1>
      <p>Order #${orderId}</p>
    </div>
    
    <div class="content">
      <div class="section">
        <h2>Great news!</h2>
        <p>Your custom PetPlantr has been processed and is ready for 3D printing. Our AI has successfully converted your pet photos into a beautiful, printable planter design.</p>
        
        <div style="text-align: center; margin: 25px 0;">
          <a href="${downloadUrl}" class="download-btn">Download Your STL File</a>
        </div>
      </div>

      ${printingSpecs ? `
      <div class="section">
        <h3>🔧 Recommended Print Settings</h3>
        <table class="specs-table">
          <tr><td>Layer Height</td><td>${printingSpecs.layerHeight}mm</td></tr>
          <tr><td>Infill</td><td>${printingSpecs.infill}%</td></tr>
          <tr><td>Supports</td><td>${printingSpecs.supports ? 'Required' : 'Not needed'}</td></tr>
          <tr><td>Estimated Print Time</td><td>${printingSpecs.estimatedPrintTime}</td></tr>
          <tr><td>Filament Usage</td><td>${printingSpecs.filamentUsage}</td></tr>
        </table>
      </div>
      ` : ''}

      <div class="section">
        <h3>📋 Next Steps</h3>
        <ol>
          <li><strong>Download</strong> your STL file using the button above</li>
          <li><strong>Import</strong> the file into your 3D printing software (Cura, PrusaSlicer, etc.)</li>
          <li><strong>Apply</strong> the recommended print settings</li>
          <li><strong>Print</strong> your custom PetPlantr</li>
          <li><strong>Add soil and plants</strong> to complete your project!</li>
        </ol>
      </div>

      <div class="section">
        <h3>💡 Tips for Best Results</h3>
        <ul>
          <li>Use PLA filament for best results and plant safety</li>
          <li>Ensure proper bed adhesion before starting the print</li>
          <li>Consider adding drainage holes if not included in the design</li>
          <li>Share your finished PetPlantr on social media and tag us!</li>
        </ul>
      </div>
    </div>

    <div class="footer">
      <p>Questions? Reply to this email or contact our support team.</p>
      <p><strong>Daniel & the PetPlantr Team</strong></p>
      <p>🌱 Bringing your pets to life in planters 🌱</p>
    </div>
  </div>
</body>
</html>`;

    return { html };
  }

  /**
   * Generate order confirmation email content
   */
  private generateOrderConfirmationEmail(orderId: string, orderDetails: any) {
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Order Confirmed - PetPlantr</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #1976D2, #2196F3); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .timeline { display: flex; justify-content: space-between; align-items: center; margin: 20px 0; }
    .timeline-step { text-align: center; flex: 1; }
    .timeline-step.active { color: #1976D2; font-weight: bold; }
    .footer { text-align: center; padding: 20px; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>✅ Order Confirmed!</h1>
      <p>Thank you for choosing PetPlantr</p>
      <h2>Order #${orderId}</h2>
    </div>
    
    <div class="content">
      <div class="section">
        <h3>🎯 What happens next?</h3>
        <div class="timeline">
          <div class="timeline-step active">
            <div>✅</div>
            <div>Order Received</div>
          </div>
          <div class="timeline-step">
            <div>🤖</div>
            <div>AI Processing</div>
          </div>
          <div class="timeline-step">
            <div>📐</div>
            <div>3D Model Creation</div>
          </div>
          <div class="timeline-step">
            <div>🎉</div>
            <div>Ready to Print</div>
          </div>
        </div>
      </div>

      <div class="section">
        <h3>📋 Order Details</h3>
        <p><strong>Photos Uploaded:</strong> ${orderDetails.photoCount || 'N/A'} images</p>
        <p><strong>Planter Size:</strong> ${orderDetails.sizeTier || 'Medium'}</p>
        <p><strong>Amount Paid:</strong> $${(orderDetails.amount / 100).toFixed(2)} USD</p>
        <p><strong>Processing Time:</strong> Typically 5-15 minutes</p>
      </div>

      <div class="section">
        <h3>⏱️ Expected Timeline</h3>
        <ul>
          <li><strong>AI Processing:</strong> 2-5 minutes</li>
          <li><strong>3D Model Generation:</strong> 3-10 minutes</li>
          <li><strong>Quality Check:</strong> 1-2 minutes</li>
          <li><strong>Email Delivery:</strong> Immediately after completion</li>
        </ul>
      </div>

      <div class="section">
        <h3>📧 We'll Keep You Updated</h3>
        <p>You'll receive an email with your downloadable STL file as soon as your PetPlantr is ready. The file will be optimized for 3D printing with recommended settings included.</p>
      </div>
    </div>

    <div class="footer">
      <p>Questions about your order? Just reply to this email!</p>
      <p><strong>Daniel & the PetPlantr Team</strong></p>
    </div>
  </div>
</body>
</html>`;

    return { html };
  }

  /**
   * Generate order status email content
   */
  private generateOrderStatusEmail(orderId: string, status: string, message: string) {
    const statusColors = {
      'PROCESSING': '#FF9800',
      'COMPLETED': '#4CAF50',
      'FAILED': '#F44336',
      'CANCELLED': '#9E9E9E'
    };

    const statusIcons = {
      'PROCESSING': '⚙️',
      'COMPLETED': '✅',
      'FAILED': '❌',
      'CANCELLED': '⏹️'
    };

    const color = statusColors[status as keyof typeof statusColors] || '#2196F3';
    const icon = statusIcons[status as keyof typeof statusIcons] || '📋';

    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Order Update - PetPlantr</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: ${color}; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
    .section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .footer { text-align: center; padding: 20px; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>${icon} Order Update</h1>
      <h2>Order #${orderId}</h2>
      <p>Status: ${status}</p>
    </div>
    
    <div class="content">
      <div class="section">
        <h3>Update Details</h3>
        <p>${message}</p>
      </div>
    </div>

    <div class="footer">
      <p>Questions? Reply to this email or contact our support team.</p>
      <p><strong>Daniel & the PetPlantr Team</strong></p>
    </div>
  </div>
</body>
</html>`;

    return { html };
  }
}

export default MicrosoftGraphService;
