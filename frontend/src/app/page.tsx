export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            🐕 PetPlantr
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Transform your pet photos into beautiful 3D planters using AI. 
            Upload a photo, get a custom planter design, and 3D print your creation!
          </p>

          <div className="grid md:grid-cols-3 gap-8 mt-12 max-w-4xl mx-auto">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-4xl mb-4">📱</div>
              <h3 className="text-lg font-semibold mb-3">Upload Photo</h3>
              <p className="text-gray-600">Upload a clear photo of your pet</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-lg font-semibold mb-3">AI Processing</h3>
              <p className="text-gray-600">Our AI creates a custom 3D model</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-4xl mb-4">🌱</div>
              <h3 className="text-lg font-semibold mb-3">Get Your Planter</h3>
              <p className="text-gray-600">Download and 3D print your planter</p>
            </div>
          </div>

          <div className="mt-12">
            <button className="bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-8 rounded-lg text-lg transition-colors shadow-lg">
              Get Started - Upload Your Pet Photo
            </button>
          </div>

          <div className="mt-16 text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">How It Works</h2>
            <div className="max-w-3xl mx-auto text-gray-600">
              <p className="mb-4">
                PetPlantr uses advanced AI to analyze your pet photo and generate a custom 3D planter design 
                that captures your pet\'s unique features and personality.
              </p>
              <p>
                Simply upload a photo, wait for our AI to work its magic, and download your STL file 
                ready for 3D printing. Create a beautiful planter that celebrates your beloved pet!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
