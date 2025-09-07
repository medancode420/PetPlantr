# Upload Assistant Integration

This document outlines the Upload Assistant feature that helps users take better photos for their 3D pet planters.

## Features

✅ **Real-time Chat Interface**: Interactive chat UI with message history
✅ **LangChain Integration**: Powered by OpenAI GPT models via AWS Lambda
✅ **Smart Suggestions**: Context-aware suggestions for common questions
✅ **Responsive Design**: Works seamlessly on desktop and mobile devices
✅ **Authentication Ready**: Optional Clerk authentication middleware
✅ **Error Handling**: Graceful error handling with user-friendly messages

## Architecture

```
Frontend (Next.js) → API Route → AWS Lambda → OpenAI API
     ↓                  ↓           ↓           ↓
  Chat UI         Auth Proxy    LangChain    GPT Model
```

## Components

### `UploadAssistantChat.tsx`
- Main chat interface component
- Handles message sending/receiving
- Displays chat history and suggestions
- Responsive design with loading states

### `chat-config.ts`
- Configuration and utilities for chat functionality
- API endpoint management
- Common suggestions and helper functions

### `/api/chat/upload/route.ts`
- Next.js API route that proxies requests to Lambda
- Optional authentication middleware
- Error handling and request validation

## API Endpoints

### Local API Route: `/api/chat/upload`
- **Method**: POST
- **Auth**: Optional (Clerk middleware available)
- **Body**: `{ message: string, context?: string }`
- **Response**: `{ answer: string, suggestions?: string[] }`

### AWS Lambda: `https://t2tugpetrj.execute-api.us-east-1.amazonaws.com/prod/api/chat/upload`
- **Method**: POST
- **Auth**: None (CORS enabled)
- **Body**: `{ message: string, context?: string }`
- **Response**: `{ answer: string, suggestions?: string[] }`

## Usage

1. **Frontend Integration**: The chat component is automatically included on the `/upload` page
2. **User Interaction**: Users can type messages or click suggestion buttons
3. **AI Response**: The assistant provides helpful guidance about photo taking
4. **Context Awareness**: The AI understands it's helping with pet planter photos

## Configuration

### Environment Variables
No additional environment variables needed - the component uses relative API calls.

### Authentication (Optional)
To enable authentication, uncomment the auth check in `/api/chat/upload/route.ts`:

```typescript
const user = await currentUser()
if (!user) {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
}
```

### Customization

#### Styling
- Uses Tailwind CSS classes
- Follows existing design system with `primary-*` colors
- Fully responsive with mobile-first approach

#### Suggestions
- Edit `COMMON_SUGGESTIONS` in `chat-config.ts`
- Suggestions appear below assistant messages
- Random suggestions used as fallback

#### API Endpoint
- Change `getChatAPIUrl()` in `chat-config.ts` to use different endpoints
- Can switch between local API route and direct Lambda calls

## Testing

1. **Start Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Navigate to Upload Page**: 
   - Go to `http://localhost:3000/upload` (requires auth)
   - The chat assistant appears on the right side

3. **Test Chat Functionality**:
   - Type a message about photo taking
   - Click on suggestion buttons
   - Verify responses are relevant and helpful

## Production Deployment

1. **Verify Lambda Function**: Ensure the Lambda is deployed and accessible
2. **Update API URLs**: Update URLs in `chat-config.ts` if needed
3. **Enable Authentication**: Uncomment auth middleware if desired
4. **Build and Deploy**: Standard Next.js deployment process

## Next Steps

- **Status Bot**: Create similar chat interface for order status inquiries
- **DevOps Bot**: Add technical support chat for developers
- **Chat History**: Persist chat history across sessions
- **File Upload**: Allow users to upload photos directly in chat
- **Voice Messages**: Add voice-to-text functionality

## Troubleshooting

### Common Issues

1. **API Errors**: Check Lambda function logs in CloudWatch
2. **CORS Issues**: Verify CORS is enabled on Lambda function
3. **Auth Issues**: Check Clerk configuration and API route auth
4. **Styling Issues**: Verify Tailwind CSS is properly configured

### Debug Steps

1. Check browser console for JavaScript errors
2. Verify API responses in Network tab
3. Test Lambda function directly with curl
4. Check CloudWatch logs for Lambda errors
