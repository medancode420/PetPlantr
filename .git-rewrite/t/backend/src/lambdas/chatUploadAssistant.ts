import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { ChatOpenAI } from '@langchain/openai';
import { PromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { RunnableSequence } from '@langchain/core/runnables';

interface ChatRequest {
  message: string;
  conversationHistory?: Array<{ role: 'user' | 'assistant'; content: string }>;
  uploadContext?: {
    hasPhotos: boolean;
    photoCount: number;
    detectedBreed?: string;
  };
}

const UPLOAD_ASSISTANT_PROMPT = `You are PetPlantr's friendly Upload Assistant, helping customers take perfect photos of their pets for 3D planter creation.

CONTEXT: PetPlantr creates personalized 3D pet planters from customer photos. Quality photos are crucial for generating accurate 3D models.

REQUIRED PHOTOS:
1. Front view (pet facing camera, full body visible)
2. 45-degree angle view (side profile with some front visibility)  
3. Top view (looking down at pet, shows head shape and back)

PHOTO GUIDELINES:
- Good lighting (natural daylight preferred, avoid harsh shadows)
- Pet should be stationary and alert
- Clear background (not mandatory but helpful)
- Avoid flash (can create harsh shadows or red-eye)
- Take photos at pet's level (crouch down for dogs/cats)
- Ensure all photos show the same pet in similar poses

SUPPORTED BREEDS: All dog and cat breeds are supported. We specialize in capturing unique facial features and body proportions.

TROUBLESHOOTING:
- Blurry photos: Use good lighting, keep pet still, tap to focus
- Dark photos: Move near a window or use soft indoor lighting
- Pet won't cooperate: Use treats, favorite toys, or get help from family

Your role: Answer questions about photo requirements, lighting, breeds, or upload process. Be encouraging, specific, and helpful. If unsure about technical details, recommend contacting support.

Current conversation context: {context}

User question: {question}

Provide a helpful, friendly response focused on getting great photos for their pet planter:`;

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    // Parse request body
    const body: ChatRequest = JSON.parse(event.body || '{}');
    const { message, conversationHistory = [], uploadContext } = body;

    if (!message) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        },
        body: JSON.stringify({ error: 'Message is required' }),
      };
    }

    // Initialize OpenAI
    const llm = new ChatOpenAI({
      model: 'gpt-3.5-turbo',
      temperature: 0.3,
      openAIApiKey: process.env.OPENAI_API_KEY,
    });

    // Create prompt template
    const prompt = PromptTemplate.fromTemplate(UPLOAD_ASSISTANT_PROMPT);

    // Build context from conversation history and upload state
    const contextParts = [];
    if (conversationHistory.length > 0) {
      contextParts.push('Previous conversation:');
      conversationHistory.slice(-3).forEach(msg => {
        contextParts.push(`${msg.role}: ${msg.content}`);
      });
    }
    
    if (uploadContext?.hasPhotos) {
      contextParts.push(`User has uploaded ${uploadContext.photoCount || 0} photos.`);
    }
    
    if (uploadContext?.detectedBreed) {
      contextParts.push(`Pet breed detected: ${uploadContext.detectedBreed}`);
    }

    const context = contextParts.length > 0 ? contextParts.join('\n') : 'Starting new conversation.';

    // Create the chain
    const chain = RunnableSequence.from([
      prompt,
      llm,
      new StringOutputParser(),
    ]);

    // Generate response
    const response = await chain.invoke({
      context,
      question: message,
    });

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      },
      body: JSON.stringify({
        answer: response,
        suggestions: generateSuggestions(message, uploadContext || {}),
      }),
    };

  } catch (error) {
    console.error('Upload Assistant Error:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      },
      body: JSON.stringify({
        error: 'Failed to process chat request',
        fallback: 'I\'m having trouble right now. For photo guidelines, remember: take front, 45-degree, and top views with good lighting. Avoid flash and keep your pet still!',
      }),
    };
  }
};

function generateSuggestions(
  message: string, 
  uploadContext: { hasPhotos?: boolean; photoCount?: number }
): string[] {
  const lowerMessage = message.toLowerCase();
  const suggestions = [];

  // Context-aware suggestions
  if (lowerMessage.includes('lighting') || lowerMessage.includes('dark')) {
    suggestions.push('Try natural window light instead of flash');
    suggestions.push('Move to a brighter room');
  }

  if (lowerMessage.includes('blurry') || lowerMessage.includes('focus')) {
    suggestions.push('Tap your phone screen to focus on your pet');
    suggestions.push('Get closer and ensure good lighting');
  }

  if (lowerMessage.includes('won\'t') || lowerMessage.includes('move')) {
    suggestions.push('Use treats to keep your pet interested');
    suggestions.push('Try taking photos during calm moments');
  }

  if (!uploadContext.hasPhotos) {
    suggestions.push('Start with a front-facing photo');
    suggestions.push('Make sure your pet is looking at the camera');
  } else if ((uploadContext.photoCount || 0) < 3) {
    suggestions.push('Remember to get all 3 angles: front, side, top');
    suggestions.push('Each photo should show your pet clearly');
  }

  // Default suggestions if no specific context
  if (suggestions.length === 0) {
    suggestions.push('Take photos at your pet\'s eye level');
    suggestions.push('Use natural lighting when possible');
    suggestions.push('Keep your pet engaged with treats or toys');
  }

  return suggestions.slice(0, 3); // Limit to 3 suggestions
}
