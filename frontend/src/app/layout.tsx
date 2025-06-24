import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PetPlantr - Custom 3D Pet Planters',
  description: 'Upload your pet photos and get custom 3D printed planters delivered to your door',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const isDevMode = process.env.NEXT_PUBLIC_DEV_MODE === 'true'

  // In development mode, render without ClerkProvider
  if (isDevMode) {
    return (
      <html lang="en">
        <body className={inter.className}>
          <div className="min-h-screen bg-gray-50">
            <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
              <p className="font-bold">🚧 Development Mode</p>
              <p className="text-sm">Authentication is disabled for testing. Add real Clerk keys to enable auth.</p>
            </div>
            {children}
          </div>
        </body>
      </html>
    )
  }

  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          <div className="min-h-screen bg-gray-50">
            {children}
          </div>
        </body>
      </html>
    </ClerkProvider>
  )
}
