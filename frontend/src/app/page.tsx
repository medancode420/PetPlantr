import { 
  SignInButton, 
  SignUpButton, 
  UserButton, 
  SignedIn, 
  SignedOut 
} from '@clerk/nextjs'
import Link from 'next/link'

export default function HomePage() {
  const isDevMode = process.env.NEXT_PUBLIC_DEV_MODE === 'true'

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full mx-auto p-8 bg-white rounded-xl shadow-lg">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🌱 PetPlantr
          </h1>
          <p className="text-gray-600">
            Transform your pet photos into custom 3D printed planters
          </p>
        </div>

        {isDevMode ? (
          <div className="space-y-4">
            <div className="text-center text-sm text-yellow-700 bg-yellow-50 p-3 rounded-lg">
              Development Mode - Authentication Disabled
            </div>
            
            <Link href="/upload">
              <button className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-colors">
                Go to Upload (Demo)
              </button>
            </Link>
            
            <Link href="/test-chat">
              <button className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-3 px-4 rounded-lg transition-colors">
                Test Chat Assistant
              </button>
            </Link>
          </div>
        ) : (
          <>
            <SignedOut>
              <div className="space-y-4">
                <div className="w-full">
                  <SignInButton mode="modal">
                    <button className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-colors">
                      Sign In
                    </button>
                  </SignInButton>
                </div>
                
                <div className="w-full">
                  <SignUpButton mode="modal">
                    <button className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-3 px-4 rounded-lg transition-colors">
                      Create Account
                    </button>
                  </SignUpButton>
                </div>
              </div>
            </SignedOut>

            <SignedIn>
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-4">
                  <UserButton />
                  <span className="text-gray-600">Welcome back!</span>
                </div>
                
                <Link href="/upload">
                  <button className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-colors">
                    Upload Pet Photos
                  </button>
                </Link>
              </div>
            </SignedIn>
          </>
        )}

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Upload photos → Get custom planters → Delivered to your door</p>
        </div>
      </div>
    </div>
  )
}
