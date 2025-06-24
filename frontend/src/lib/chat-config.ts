// API configuration for different environments
export const API_CONFIG = {
  // Lambda endpoint URL for direct calls (fallback)
  LAMBDA_URL: 'https://t2tugpetrj.execute-api.us-east-1.amazonaws.com/prod/api/chat/upload',
  
  // Local API route (preferred)
  LOCAL_API_URL: '/api/chat/upload',
}

// Helper to get the appropriate API endpoint
export function getChatAPIUrl(): string {
  // In development or when using the local API route
  return API_CONFIG.LOCAL_API_URL
}

// Helper to format chat messages
export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  suggestions?: string[]
  timestamp?: Date
}

// Predefined helpful suggestions for common questions
export const COMMON_SUGGESTIONS = [
  "What photos do I need?",
  "Tips for better lighting",
  "How to keep my pet still",
  "Best camera angles",
  "Indoor vs outdoor photos",
  "Multiple pets in one photo"
]

// Helper to get random suggestions when none are provided
export function getRandomSuggestions(count: number = 3): string[] {
  const shuffled = [...COMMON_SUGGESTIONS].sort(() => 0.5 - Math.random())
  return shuffled.slice(0, count)
}
