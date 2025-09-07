import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

// Define public routes that don't require authentication
const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/upload',
  '/api/v1/ops/(.*)',
  '/healthz',
  '/favicon.ico',
  '/robots.txt',
  '/demo(.*)',
  '/api/public(.*)',
])

export default clerkMiddleware((auth, request) => {
  // In development mode, bypass Clerk entirely
  if (process.env.NEXT_PUBLIC_DEV_MODE === 'true') {
    return NextResponse.next()
  }

  // Always allow CORS preflight
  if (request.method === 'OPTIONS') {
    return NextResponse.next()
  }

  // Allow public routes without authentication
  if (isPublicRoute(request)) {
    return NextResponse.next()
  }

  // Protect all other routes
  auth().protect()

  // Explicit pass-through when protected
  return NextResponse.next()
})

export const config = {
  matcher: [
    '/((?!.+\\.[\\w]+$|_next).*)',
    '/(api|trpc)(.*)',
  ],
}
