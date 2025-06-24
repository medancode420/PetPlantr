import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

// Define public routes that don't require authentication
const isPublicRoute = createRouteMatcher([
  '/',
  '/test-chat',
  '/api/chat/upload',
  '/sign-in(.*)',
  '/sign-up(.*)',
])

export default function middleware(req: any) {
  // In development mode, bypass Clerk entirely
  if (process.env.NEXT_PUBLIC_DEV_MODE === 'true') {
    return NextResponse.next()
  }

  // Use Clerk middleware for production
  return clerkMiddleware((auth, request) => {
    // Allow public routes without authentication
    if (isPublicRoute(request)) {
      return
    }
    
    // Protect all other routes
    auth().protect()
  })(req)
}

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}
