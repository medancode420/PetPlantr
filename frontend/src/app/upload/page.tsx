import { currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { UserButton } from '@clerk/nextjs'
import UploadForm from '@/components/UploadForm'
import UploadAssistantChat from '@/components/UploadAssistantChat'

export default async function UploadPage() {
  const isDevMode = process.env.NEXT_PUBLIC_DEV_MODE === 'true'
  let user

  if (isDevMode) {
    // In development mode, create a mock user
    user = {
      id: 'demo-user-id',
      firstName: 'Demo',
      lastName: 'User',
      emailAddresses: [{ emailAddress: 'demo@example.com' }]
    }
  } else {
    user = await currentUser()
    if (!user) {
      redirect('/sign-in')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                🌱 PetPlantr
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user.firstName || user.emailAddresses?.[0]?.emailAddress || 'User'}
              </span>
              {!isDevMode ? (
                <UserButton />
              ) : (
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-600">
                    {user.firstName?.[0] || 'D'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Upload Your Pet Photos
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Upload clear photos of your pet from different angles. Our AI will create a custom 3D planter 
            design that captures their unique features. Each planter is $29.99 and includes shipping.
          </p>
        </div>

        <section className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 order-2 lg:order-1">
            <UploadForm userId={user.id} />
          </div>
          <div className="lg:col-span-1 order-1 lg:order-2">
            <div className="lg:sticky lg:top-8">
              <UploadAssistantChat />
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
