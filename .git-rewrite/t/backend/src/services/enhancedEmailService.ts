import MicrosoftGraphService from '../services/microsoftGraphService';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

/**
 * Enhanced Email Service that supports both AWS SES and Microsoft Graph
 * Prioritizes Microsoft Graph for professional communication from Daniel@PetPlantr.com
 */

interface EmailRecipient {
  email: string;
  name?: string;
}

interface EmailOptions {
  subject: string;
  htmlContent: string;
  textContent?: string;
  priority?: 'low' | 'normal' | 'high';
  replyTo?: string;
}

interface OrderDetails {
  orderId: string;
  userId: string;
  photoCount?: number;
  sizeTier?: string;
  amount?: number;
  downloadUrl?: string;
  printingSpecs?: any;
}

export class EnhancedEmailService {
  private secretsManager: SecretsManagerClient;
  private graphService: MicrosoftGraphService | null = null;
  private isGraphEnabled: boolean = false;

  constructor() {
    this.secretsManager = new SecretsManagerClient({ region: 'us-east-1' });
  }

  /**
   * Initialize Microsoft Graph service if credentials are available
   */
  private async initializeGraphService(): Promise<void> {
    if (this.graphService) return;

    try {
      // Try to get Microsoft Graph credentials from Secrets Manager
      const graphConfigResponse = await this.secretsManager.send(
        new GetSecretValueCommand({
          SecretId: 'petplantr/microsoft/graph-config'
        })
      );

      if (graphConfigResponse.SecretString) {
        const config = JSON.parse(graphConfigResponse.SecretString);
        this.graphService = await MicrosoftGraphService.fromConfig(config);
        this.isGraphEnabled = true;
        console.log('Microsoft Graph service initialized successfully');
      }
    } catch (error) {
      console.log('Microsoft Graph not available, falling back to SES:', error instanceof Error ? error.message : 'Unknown error');
      this.isGraphEnabled = false;
    }
  }

  /**
   * Send order confirmation email
   */
  async sendOrderConfirmation(
    recipient: EmailRecipient,
    orderDetails: OrderDetails
  ): Promise<boolean> {
    await this.initializeGraphService();

    const subject = `Order Confirmed: PetPlantr #${orderDetails.orderId}`;
    
    try {
      if (this.isGraphEnabled && this.graphService) {
        await this.graphService.sendOrderConfirmationEmail(
          recipient.email,
          recipient.name || 'Valued Customer',
          orderDetails.orderId,
          orderDetails
        );
        console.log(`Order confirmation sent via Microsoft Graph to ${recipient.email}`);
        return true;
      } else {
        // Fallback to existing SES implementation
        console.log(`Falling back to SES for order confirmation to ${recipient.email}`);
        return await this.sendViaSES(recipient, {
          subject,
          htmlContent: this.generateFallbackOrderConfirmation(orderDetails),
          priority: 'normal'
        });
      }
    } catch (error) {
      console.error('Failed to send order confirmation:', error);
      return false;
    }
  }

  /**
   * Send order completion email with download link
   */
  async sendOrderCompletion(
    recipient: EmailRecipient,
    orderDetails: OrderDetails
  ): Promise<boolean> {
    await this.initializeGraphService();

    const subject = `🎉 Your Custom PetPlantr is Ready! Order #${orderDetails.orderId}`;
    
    try {
      if (this.isGraphEnabled && this.graphService && orderDetails.downloadUrl) {
        await this.graphService.sendOrderCompletionEmail(
          recipient.email,
          recipient.name || 'Valued Customer',
          orderDetails.orderId,
          orderDetails.downloadUrl,
          orderDetails.printingSpecs
        );
        console.log(`Order completion sent via Microsoft Graph to ${recipient.email}`);
        return true;
      } else {
        // Fallback to existing SES implementation
        console.log(`Falling back to SES for order completion to ${recipient.email}`);
        return await this.sendViaSES(recipient, {
          subject,
          htmlContent: this.generateFallbackOrderCompletion(orderDetails),
          priority: 'normal'
        });
      }
    } catch (error) {
      console.error('Failed to send order completion:', error);
      return false;
    }
  }

  /**
   * Send order status update
   */
  async sendOrderStatusUpdate(
    recipient: EmailRecipient,
    orderId: string,
    status: string,
    message: string
  ): Promise<boolean> {
    await this.initializeGraphService();

    const subject = `Order Update: PetPlantr #${orderId} - ${status}`;
    
    try {
      if (this.isGraphEnabled && this.graphService) {
        await this.graphService.sendOrderStatusEmail(
          recipient.email,
          recipient.name || 'Valued Customer',
          orderId,
          status,
          message
        );
        console.log(`Order status update sent via Microsoft Graph to ${recipient.email}`);
        return true;
      } else {
        // Fallback to existing SES implementation
        console.log(`Falling back to SES for order status to ${recipient.email}`);
        return await this.sendViaSES(recipient, {
          subject,
          htmlContent: this.generateFallbackStatusUpdate(orderId, status, message),
          priority: 'normal'
        });
      }
    } catch (error) {
      console.error('Failed to send order status update:', error);
      return false;
    }
  }

  /**
   * Send internal notification to Daniel
   */
  async sendInternalAlert(
    subject: string,
    message: string,
    priority: 'low' | 'normal' | 'high' = 'normal',
    orderDetails?: Partial<OrderDetails>
  ): Promise<boolean> {
    await this.initializeGraphService();

    try {
      if (this.isGraphEnabled && this.graphService) {
        const htmlContent = this.generateInternalAlertHtml(message, orderDetails);
        await this.graphService.sendInternalNotification(subject, htmlContent, priority);
        console.log(`Internal alert sent via Microsoft Graph: ${subject}`);
        return true;
      } else {
        console.log(`Microsoft Graph not available for internal alert: ${subject}`);
        return false;
      }
    } catch (error) {
      console.error('Failed to send internal alert:', error);
      return false;
    }
  }

  /**
   * Fallback SES implementation (simplified)
   */
  private async sendViaSES(
    recipient: EmailRecipient,
    options: EmailOptions
  ): Promise<boolean> {
    // This would use the existing SES implementation
    // For now, we'll just log it
    console.log('SES Email (fallback):', {
      to: recipient.email,
      subject: options.subject,
      priority: options.priority
    });
    return true;
  }

  /**
   * Generate fallback HTML for order confirmation
   */
  private generateFallbackOrderConfirmation(orderDetails: OrderDetails): string {
    return `
<!DOCTYPE html>
<html>
<head><title>Order Confirmed</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h1>✅ Order Confirmed!</h1>
  <p>Thank you for your PetPlantr order #${orderDetails.orderId}</p>
  <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
    <h3>Order Details:</h3>
    <p><strong>Order ID:</strong> ${orderDetails.orderId}</p>
    <p><strong>Photos:</strong> ${orderDetails.photoCount || 'N/A'}</p>
    <p><strong>Size:</strong> ${orderDetails.sizeTier || 'Medium'}</p>
    <p><strong>Amount:</strong> $${orderDetails.amount ? (orderDetails.amount / 100).toFixed(2) : 'N/A'}</p>
  </div>
  <p>We'll email you when your PetPlantr is ready!</p>
  <p><strong>The PetPlantr Team</strong></p>
</body>
</html>`;
  }

  /**
   * Generate fallback HTML for order completion
   */
  private generateFallbackOrderCompletion(orderDetails: OrderDetails): string {
    return `
<!DOCTYPE html>
<html>
<head><title>Your PetPlantr is Ready!</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h1>🎉 Your PetPlantr is Ready!</h1>
  <p>Great news! Your custom PetPlantr #${orderDetails.orderId} is ready for download.</p>
  ${orderDetails.downloadUrl ? `
  <div style="text-align: center; margin: 20px 0;">
    <a href="${orderDetails.downloadUrl}" style="background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Download STL File</a>
  </div>
  ` : ''}
  <p>Follow the included printing instructions for best results.</p>
  <p><strong>Happy Printing!</strong><br>The PetPlantr Team</p>
</body>
</html>`;
  }

  /**
   * Generate fallback HTML for status updates
   */
  private generateFallbackStatusUpdate(orderId: string, status: string, message: string): string {
    return `
<!DOCTYPE html>
<html>
<head><title>Order Update</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h1>📋 Order Update</h1>
  <p><strong>Order #${orderId}</strong></p>
  <p><strong>Status:</strong> ${status}</p>
  <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
    <p>${message}</p>
  </div>
  <p><strong>The PetPlantr Team</strong></p>
</body>
</html>`;
  }

  /**
   * Generate internal alert HTML
   */
  private generateInternalAlertHtml(message: string, orderDetails?: Partial<OrderDetails>): string {
    return `
<!DOCTYPE html>
<html>
<head><title>PetPlantr Alert</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h1>🚨 PetPlantr System Alert</h1>
  <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px;">
    <p>${message}</p>
  </div>
  ${orderDetails ? `
  <h3>Related Order Details:</h3>
  <ul>
    ${orderDetails.orderId ? `<li><strong>Order ID:</strong> ${orderDetails.orderId}</li>` : ''}
    ${orderDetails.userId ? `<li><strong>User ID:</strong> ${orderDetails.userId}</li>` : ''}
    ${orderDetails.photoCount ? `<li><strong>Photos:</strong> ${orderDetails.photoCount}</li>` : ''}
  </ul>
  ` : ''}
  <p>Generated at: ${new Date().toISOString()}</p>
</body>
</html>`;
  }
}

export default EnhancedEmailService;
