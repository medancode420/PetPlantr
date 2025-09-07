import { NextResponse } from 'next/server'

// Minimal health endpoint for quick checks
export const runtime = 'nodejs'

export async function GET() {
  return NextResponse.json({ status: 'ok', time: new Date().toISOString() })
}
