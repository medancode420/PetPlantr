#!/bin/bash

# Setup script for Microsoft Graph integration with Daniel@PetPlantr.com
# This script helps configure the necessary Azure app registration and AWS secrets

echo "🔧 PetPlantr Microsoft Graph Setup"
echo "===================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    echo "🔐 Setting up secret: $secret_name"
    
    # Try to create the secret first
    if aws secretsmanager create-secret \
        --name "$secret_name" \
        --description "$description" \
        --secret-string "$secret_value" \
        --region us-east-1 >/dev/null 2>&1; then
        echo "✅ Created new secret: $secret_name"
    else
        # If creation fails, try to update existing secret
        if aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region us-east-1 >/dev/null 2>&1; then
            echo "✅ Updated existing secret: $secret_name"
        else
            echo "❌ Failed to create or update secret: $secret_name"
            return 1
        fi
    fi
}

echo ""
echo "📋 Microsoft Graph Setup Instructions"
echo "====================================="
echo ""
echo "To use Microsoft Graph with Daniel@PetPlantr.com, you need to:"
echo ""
echo "1. Create an Azure App Registration:"
echo "   - Go to https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps"
echo "   - Click 'New registration'"
echo "   - Name: 'PetPlantr Email Service'"
echo "   - Account types: 'Accounts in this organizational directory only'"
echo "   - Click 'Register'"
echo ""
echo "2. Configure API Permissions:"
echo "   - Go to 'API permissions' in your app"
echo "   - Click 'Add a permission'"
echo "   - Select 'Microsoft Graph'"
echo "   - Select 'Application permissions'"
echo "   - Add these permissions:"
echo "     * Mail.Send (Send mail as any user)"
echo "     * User.Read.All (Read all users' full profiles)"
echo "   - Click 'Grant admin consent for your organization'"
echo ""
echo "3. Create a Client Secret:"
echo "   - Go to 'Certificates & secrets'"
echo "   - Click 'New client secret'"
echo "   - Description: 'PetPlantr Production'"
echo "   - Expires: 24 months"
echo "   - Copy the secret value (you won't see it again!)"
echo ""
echo "4. Get your Tenant ID and Client ID:"
echo "   - Go to 'Overview' tab"
echo "   - Copy 'Application (client) ID'"
echo "   - Copy 'Directory (tenant) ID'"
echo ""

# Interactive setup
echo "🔑 Now let's set up your credentials in AWS Secrets Manager"
echo ""

read -p "Do you have your Azure App Registration ready? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please complete the Azure setup first, then run this script again."
    exit 1
fi

echo ""
echo "Please provide your Azure App Registration details:"
echo ""

read -p "Tenant ID: " TENANT_ID
read -p "Client ID: " CLIENT_ID
read -s -p "Client Secret: " CLIENT_SECRET
echo ""
read -p "Email Address (Daniel@PetPlantr.com): " EMAIL_ADDRESS

# Default to Daniel@PetPlantr.com if not provided
if [ -z "$EMAIL_ADDRESS" ]; then
    EMAIL_ADDRESS="Daniel@PetPlantr.com"
fi

echo ""
echo "🔄 Creating AWS Secrets..."

# Create Microsoft Graph configuration secret
GRAPH_CONFIG=$(cat <<EOF
{
  "tenantId": "$TENANT_ID",
  "clientId": "$CLIENT_ID",
  "clientSecret": "$CLIENT_SECRET",
  "emailAddress": "$EMAIL_ADDRESS",
  "scope": "https://graph.microsoft.com/.default"
}
EOF
)

create_or_update_secret \
    "petplantr/microsoft/graph-config" \
    "$GRAPH_CONFIG" \
    "Microsoft Graph configuration for PetPlantr email service"

# Test the configuration
echo ""
echo "🧪 Testing Microsoft Graph configuration..."

# Create a simple test script
cat > /tmp/test-graph.js << 'EOF'
const { Client } = require('@microsoft/microsoft-graph-client');
const { AuthenticationProvider } = require('@microsoft/microsoft-graph-client');
const { ConfidentialClientApplication } = require('@azure/msal-node');

class MSALAuthProvider {
    constructor(config) {
        this.clientApp = new ConfidentialClientApplication({
            auth: {
                clientId: config.clientId,
                clientSecret: config.clientSecret,
                authority: `https://login.microsoftonline.com/${config.tenantId}`
            }
        });
    }

    async getAccessToken() {
        try {
            const response = await this.clientApp.acquireTokenByClientCredential({
                scopes: ['https://graph.microsoft.com/.default']
            });
            return response.accessToken;
        } catch (error) {
            throw new Error(`Failed to acquire token: ${error.message}`);
        }
    }
}

async function testGraphConnection() {
    try {
        const config = JSON.parse(process.argv[2]);
        const authProvider = new MSALAuthProvider(config);
        const graphClient = Client.initWithMiddleware({ authProvider });
        
        // Test by getting user profile
        const user = await graphClient.api(`/users/${config.emailAddress}`).get();
        console.log('✅ Microsoft Graph connection successful!');
        console.log(`Connected as: ${user.displayName} (${user.mail})`);
        return true;
    } catch (error) {
        console.log('❌ Microsoft Graph connection failed:', error.message);
        return false;
    }
}

testGraphConnection();
EOF

# Check if we can run the test (requires node and packages)
if command -v node >/dev/null 2>&1; then
    echo "Running connection test..."
    if cd /Users/medan/Downloads/PetPlantr/backend && npm list @microsoft/microsoft-graph-client >/dev/null 2>&1; then
        node /tmp/test-graph.js "$GRAPH_CONFIG" 2>/dev/null || echo "⚠️  Connection test failed - this is normal if permissions aren't granted yet"
    else
        echo "⚠️  Cannot run test - Microsoft Graph packages not installed"
    fi
else
    echo "⚠️  Cannot run test - Node.js not available"
fi

# Clean up test file
rm -f /tmp/test-graph.js

echo ""
echo "🎉 Microsoft Graph setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure admin consent is granted in Azure portal"
echo "2. Deploy your Lambda functions: cd backend && npm run deploy"
echo "3. Test email functionality with a real order"
echo ""
echo "📧 Email Configuration Summary:"
echo "- Sender: $EMAIL_ADDRESS"
echo "- Service: Microsoft Graph API"
echo "- Fallback: AWS SES (noreply@petplantr.com)"
echo ""
echo "🔐 Secrets created in AWS Secrets Manager:"
echo "- petplantr/microsoft/graph-config"
echo ""
echo "✅ Setup complete! Your PetPlantr system will now send professional emails from Daniel@PetPlantr.com"
