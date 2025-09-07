import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { z } from 'zod'

// Ensure Node runtime (uses Clerk getToken and server-side fetch)
export const runtime = 'nodejs'

// Backend target (trim trailing slashes)
const BACKEND_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.BACKEND_URL ?? 'http://localhost:8000').replace(/\/+$/, '')
const API_PATH = `${BACKEND_URL}/api/v1/generate-enhanced-3d-simple`

// Validation schema for incoming request
const RequestSchema = z.object({
  image_url: z.string().url().min(1),
  quality_level: z.enum(['standard', 'high', 'ultra-high', 'production']).default('ultra-high'),
  breed: z
    .union([z.string(), z.literal('')])
    .optional()
    .transform((v: string | undefined) => (v && v.length > 0 ? v : undefined)),
  options: z
    .union([z.string(), z.record(z.any())])
    .optional()
    .transform((val: unknown) => {
      if (typeof val === 'string') {
        const s = val.trim()
        if (!s) return {}
        try {
          return JSON.parse(s)
        } catch {
          return {}
        }
      }
      return val && typeof val === 'object' ? (val as Record<string, unknown>) : {}
    }),
})

export async function POST(req: NextRequest) {
  const { userId, getToken } = auth()
  const devMode = process.env.NEXT_PUBLIC_DEV_MODE === 'true'

  // Auth check (bypass in dev)
  if (!devMode && !userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Parse multipart/form-data from the client
  const formData = await req.formData()
  const body = {
    image_url: String(formData.get('image_url') ?? ''),
    quality_level: String(formData.get('quality_level') ?? 'ultra-high'),
    breed: formData.get('breed') ? String(formData.get('breed')) : undefined,
    options: formData.get('options') ?? '{}',
  }

  const parsed = RequestSchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid request', details: parsed.error.flatten() }, { status: 400 })
  }

  // Prepare proxy form for backend
  const proxyForm = new FormData()
  proxyForm.append('image_url', parsed.data.image_url)
  proxyForm.append('quality_level', parsed.data.quality_level)
  if (parsed.data.breed) proxyForm.append('breed', parsed.data.breed)
  proxyForm.append('options', JSON.stringify(parsed.data.options))

  // Build headers with token when not in dev
  const headers: Record<string, string> = {}
  if (devMode) {
    headers['Authorization'] = 'Bearer pk_dev'
  } else {
    try {
      const token = (await getToken?.({ template: 'backend' })) ?? (await getToken?.())
      if (token) headers['Authorization'] = `Bearer ${token}`
    } catch {
      // No token available; proceed without header
    }
  }

  // Proxy to backend
  let res: Response
  try {
    res = await fetch(API_PATH, {
      method: 'POST',
      headers,
      body: proxyForm,
    })
  } catch (err: unknown) {
    return NextResponse.json(
      { error: 'Fetch error', details: err instanceof Error ? err.message : String(err) },
      { status: 502 },
    )
  }

  const contentType = res.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await res.json().catch(() => null) : await res.text()

  if (!res.ok) {
    return NextResponse.json({ error: 'Backend error', details: payload }, { status: res.status })
  }

  return NextResponse.json(payload)
}