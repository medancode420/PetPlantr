export const runtime = 'nodejs'

// Basic Prometheus text exposition for liveness.
export async function GET() {
  const body = [
    '# HELP petplantr_frontend_info Static info about the PetPlantr Frontend',
    '# TYPE petplantr_frontend_info gauge',
    'petplantr_frontend_info{app="frontend",version="1.0.0"} 1',
    ''
  ].join('\n')
  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
    }
  })
}
