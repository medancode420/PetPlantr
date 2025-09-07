import UploadAssistantChat from '@/components/UploadAssistantChat'

export default function TestChatPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🌱 Upload Assistant Test
          </h1>
          <p className="text-gray-600">
            Test the AI-powered photo upload assistant for PetPlantr
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg p-6 border">
            <h2 className="text-xl font-semibold mb-4">📸 Photo Upload Tips</h2>
            <div className="space-y-3 text-sm text-gray-600">
              <p>• Take photos in good natural lighting</p>
              <p>• Include front, side, and 45-degree angle views</p>
              <p>• Keep your pet still and alert</p>
              <p>• Use a clear, uncluttered background</p>
              <p>• Make sure your pet's face is clearly visible</p>
              <p>• Include full body shots when possible</p>
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                💡 <strong>Pro tip:</strong> Ask the assistant on the right for personalized advice about your specific situation!
              </p>
            </div>
          </div>

          <div>
            <UploadAssistantChat />
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            This is a test page for the Upload Assistant feature. 
            In production, this will be integrated into the main upload flow.
          </p>
        </div>
      </div>
    </div>
  )
}
