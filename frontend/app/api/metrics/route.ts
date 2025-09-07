import { NextResponse } from 'next/server'
import client from 'prom-client'

export const runtime = 'nodejs'

// Create a Registry to register the metrics
const register = new client.Registry()
client.collectDefaultMetrics({ register })

export async function GET() {
  try {
    const metrics = await register.metrics()
    return new NextResponse(metrics, {
      status: 200,
      headers: {
        'Content-Type': register.contentType,
        'Cache-Control': 'no-cache',
      },
    })
  } catch (err) {
    const body = `# HELP petplantr_frontend_info Static info about the PetPlantr frontend\n# TYPE petplantr_frontend_info gauge\npetplantr_frontend_info{version="dev"} 1\n`
    return new NextResponse(body, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
        'Cache-Control': 'no-cache',
      },
    })
  }
}
