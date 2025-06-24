'use client'

import { useState } from 'react'
import { MessageCircle, Send, Bot, User } from 'lucide-react'
import { ChatMessage, getChatAPIUrl, getRandomSuggestions } from '@/lib/chat-config'

export default function UploadAssistantChat() {
  const [chat, setChat] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text: "Hi! I'm here to help you take the perfect photos for your 3D pet planter. Ask me about photo angles, lighting, or anything else!",
      suggestions: getRandomSuggestions(3)
    }
  ])
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async () => {
    if (!message.trim() || isLoading) return

    const userMessage = message.trim()
    setMessage('')
    
    // Add user message to chat
    const newUserMessage: ChatMessage = { role: 'user', text: userMessage }
    setChat(prev => [...prev, newUserMessage])
    
    setIsLoading(true)

    try {
      // Call the local API route (which proxies to Lambda)
      const response = await fetch(getChatAPIUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          context: 'User is asking about photo upload process for creating 3D pet planters'
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Add assistant response to chat with fallback suggestions
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        text: data.answer,
        suggestions: data.suggestions || getRandomSuggestions(2)
      }
      
      setChat(prev => [...prev, assistantMessage])

    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        text: "Sorry, I'm having trouble responding right now. Please try again in a moment!"
      }
      setChat(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion)
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Photo Upload Assistant</h3>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Get help with taking the perfect photos for your pet planter
        </p>
      </div>

      {/* Chat Messages */}
      <div className="h-80 overflow-y-auto p-4 space-y-4">
        {chat.map((msg, index) => (
          <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary-600" />
                </div>
              </div>
            )}
            
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              <div
                className={`rounded-lg px-3 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {msg.text}
              </div>
              
              {/* Suggestions */}
              {msg.role === 'assistant' && msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="block text-xs text-primary-600 hover:text-primary-700 border border-primary-200 hover:border-primary-300 rounded px-2 py-1 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary-600" />
              </div>
            </div>
            <div className="bg-gray-100 rounded-lg px-3 py-2 text-sm text-gray-900">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about photo tips, angles, lighting..."
            disabled={isLoading}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={!message.trim() || isLoading}
            className="bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
