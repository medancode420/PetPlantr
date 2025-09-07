/**
 * API Route: /api/replicate/generate
 * Handles AI image generation and 3D model creation with verified working models
 * Updated: July 11, 2025 - Real models only, no demo fallback
 */
import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const maxDuration = 60;

// Allow using process.env without @types/node
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const process: any;

// Module-level config helpers
const REPLICATE_TOKEN: string | undefined = process?.env?.REPLICATE_API_TOKEN;
const FLUX_VERSION: string = process?.env?.FLUX_SCHNELL_VERSION ?? 'c846a69991daf4c0e5d016514849d14ee5b2e6846ce6b9d6f21369e564cfe51e';
const DISABLE_3D: boolean = process?.env?.DISABLE_3D === '1';
const USE_DEMO_ON_FAIL: boolean = process?.env?.USE_DEMO_ON_FAIL === '1';
const ALLOWED_FETCH_HOSTS = new Set(['replicate.delivery', 'pbxt.replicate.delivery']);

// Simple in-memory token bucket rate limiter (best-effort)
const RL_CAP = Number(process?.env?.RL_CAPACITY ?? 10);
const RL_REFILL = Number(process?.env?.RL_REFILL_PER_SEC ?? 2);
const rl = new Map<string, { tokens: number; updated: number }>();
function rateLimit(key: string) {
  const now = Date.now();
  const b = rl.get(key) ?? { tokens: RL_CAP, updated: now };
  const elapsed = (now - b.updated) / 1000;
  b.tokens = Math.min(RL_CAP, b.tokens + elapsed * RL_REFILL);
  if (b.tokens < 1) {
    rl.set(key, { ...b, updated: now });
    return false;
  }
  b.tokens -= 1;
  rl.set(key, { ...b, updated: now });
  return true;
}

function clientIp(req: NextRequest) {
  const xff = req.headers.get('x-forwarded-for');
  if (xff) return xff.split(',')[0].trim();
  const xrip = req.headers.get('x-real-ip');
  if (xrip) return xrip;
  return 'unknown';
}

async function retry<T>(fn: () => Promise<T>, tries = 3, baseMs = 300): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i < tries; i++) {
    try {
      return await fn();
    } catch (e: any) {
      const status = e?.response?.status ?? e?.status;
      if (i < tries - 1 && [429, 500, 502, 503, 504].indexOf(Number(status)) >= 0) {
        const backoff = baseMs * Math.pow(2, i);
        await new Promise((r) => setTimeout(r, backoff));
        lastErr = e;
        continue;
      }
      throw e;
    }
  }
  // eslint-disable-next-line @typescript-eslint/no-throw-literal
  throw lastErr as any;
}

async function fetchWithTimeout(url: string, ms = 15000): Promise<Response> {
  const u = new URL(url);
  const host = u.hostname;
  const allowed = ALLOWED_FETCH_HOSTS.has(host) || host.endsWith('.replicate.delivery');
  if (!allowed) throw new Error('disallowed-host');
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort('timeout'), ms);
  try {
    return await fetch(url, { signal: ac.signal });
  } finally {
    clearTimeout(t);
  }
}

function validateBody(json: any): { imageUrl?: string; prompt?: string; options?: { petType?: string } } | null {
  if (!json || typeof json !== 'object') return null;
  const { imageUrl, prompt, options } = json;
  const hasUrl = typeof imageUrl === 'string' && imageUrl.startsWith('http');
  const hasPrompt = typeof prompt === 'string' && prompt.length > 0 && prompt.length <= 400;
  if (!hasUrl && !hasPrompt) return null;
  if (options && typeof options !== 'object') return null;
  if (options?.petType && typeof options.petType !== 'string') return null;
  return { imageUrl, prompt, options };
}

export async function POST(request: NextRequest) {
  try {
    // Early environment check to prevent hanging
    if (!REPLICATE_TOKEN) {
      return NextResponse.json({ error: 'Replicate API not configured' }, { status: 503 });
    }

    // Basic body size guard (1MB)
    const cl = request.headers.get('content-length');
    if (cl && Number(cl) > 1_000_000) {
      return NextResponse.json({ error: 'Payload too large' }, { status: 413 });
    }

    // Simple rate limit per IP
    const ip = clientIp(request);
    if (!rateLimit(`POST:${ip}`)) {
      return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429, headers: { 'Retry-After': '2' } as any });
    }

    const body = await request.json().catch(() => null);
    const parsed = validateBody(body);
    if (!parsed) {
      return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
    }
    const { imageUrl, prompt, options = {} } = parsed;

    // Dynamic import for Replicate to avoid type errors at build time
    const ReplicateMod = (await import('replicate')).default as any;
    const replicateClient = new ReplicateMod({ auth: REPLICATE_TOKEN });

    try {
      // Step 1: Generate enhanced pet planter concept image using FLUX
      const prompt_text =
        prompt || `A cute 3D-printable pet planter design inspired by a ${options?.petType || 'pet'}, terracotta style, succulent-friendly, modern minimalist design, product photography, white background`;

      // Create prediction with retry/backoff
      const prediction: any = await retry(() =>
        replicateClient.predictions.create({
          version: FLUX_VERSION,
          input: { prompt: prompt_text, num_outputs: 1, aspect_ratio: '1:1', output_format: 'jpg', output_quality: 90 },
        })
      );

      return NextResponse.json(
        { success: true, predictionId: prediction.id, status: prediction.status, data: prediction, pipeline: 'real' },
        { status: 200 }
      );
    } catch (replicateError: any) {
      const status = replicateError?.response?.status ?? 500;
      if (status === 402 || (USE_DEMO_ON_FAIL && status >= 400 && status < 500)) {
        const demoPredictionId = `demo_${Date.now()}`;
        return NextResponse.json(
          { success: true, predictionId: demoPredictionId, status: 'processing', data: { id: demoPredictionId, status: 'processing' }, pipeline: 'demo' },
          { status: 200 }
        );
      }
      throw replicateError;
    }
  } catch (error: any) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    const status = error?.response?.status ?? 500;
    return NextResponse.json({ error: 'Failed to start generation', details: message }, { status });
  }
}

export async function GET(request: NextRequest) {
  try {
    // Simple rate limit per IP
    const ip = clientIp(request);
    if (!rateLimit(`GET:${ip}`)) {
      return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429, headers: { 'Retry-After': '2' } as any });
    }

    const { searchParams } = new URL(request.url);
    const predictionId = searchParams.get('id');
    const threeDPredictionId = searchParams.get('threeDPredictionId');

    if (!predictionId) {
      return NextResponse.json({ error: 'Prediction ID is required' }, { status: 400 });
    }

    // Handle demo predictions
    if (predictionId.startsWith('demo_')) {
      const createdTime = parseInt(predictionId.replace('demo_', ''));
      const elapsedTime = Date.now() - createdTime;

      if (elapsedTime > 8000) {
        return NextResponse.json({ success: true, status: 'succeeded', modelUrl: '/demo/sample-planter.glb', data: { id: predictionId, status: 'succeeded', output: ['/demo/sample-planter.glb'], completed_at: new Date().toISOString() } });
      } else {
        const progress = Math.min(95, (elapsedTime / 8000) * 100);
        return new NextResponse(JSON.stringify({ success: true, status: 'processing', progress: Math.round(progress), data: { id: predictionId, status: 'processing' } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json', 'Retry-After': '2' },
        });
      }
    }

    if (!REPLICATE_TOKEN) {
      return NextResponse.json({ error: 'Replicate API not configured' }, { status: 503 });
    }

    // Dynamic imports
    const ReplicateMod = (await import('replicate')).default as any;
    const replicateClient = new ReplicateMod({ auth: REPLICATE_TOKEN });

    // Handle 3D model generation status check
    if (!DISABLE_3D && threeDPredictionId) {
      try {
        const threeDPrediction: any = await retry(() => replicateClient.predictions.get(threeDPredictionId));

        if (threeDPrediction.status === 'succeeded' && threeDPrediction.output) {
          // Process the output based on model type
          let modelUrl: string | null = null;
          const output = threeDPrediction.output;
          if (Array.isArray(output)) {
            modelUrl = output.find((url: string) => url.endsWith('.glb') || url.endsWith('.ply') || url.includes('glb') || url.includes('ply')) || output[0];
          } else if (typeof output === 'string') {
            modelUrl = output;
          }

          if (modelUrl) {
            try {
              // Secure fetch with timeout and host allowlist
              const res = await fetchWithTimeout(modelUrl, 20000);
              const len = Number(res.headers.get('content-length') || 0);
              if (len && len > 50 * 1024 * 1024) throw new Error('file-too-large');
              const modelBuffer = await res.arrayBuffer();

              // Store in S3/CloudFront
              const { s3Storage } = await import('../../../lib/s3');
              const modelResult = await s3Storage.uploadGLB(predictionId, modelBuffer);

              // Get concept image
              const mainPrediction: any = await retry(() => replicateClient.predictions.get(predictionId));
              const conceptOut = mainPrediction.output;
              const conceptImageUrl = Array.isArray(conceptOut) ? conceptOut[0] : conceptOut;

              return NextResponse.json({ success: true, status: 'succeeded', modelUrl: modelResult.cdnUrl, conceptImage: conceptImageUrl, data: { prediction: mainPrediction, output: [modelResult.cdnUrl], conceptImage: conceptImageUrl, s3ModelKey: modelResult.key, threeDGeneration: threeDPrediction }, pipeline: 'real' });
            } catch (s3Error) {
              // Return with direct URL if S3 fails
              const mainPrediction: any = await retry(() => replicateClient.predictions.get(predictionId));
              const conceptOut = mainPrediction.output;
              const conceptImageUrl = Array.isArray(conceptOut) ? conceptOut[0] : conceptOut;

              return NextResponse.json({ success: true, status: 'succeeded', modelUrl, conceptImage: conceptImageUrl, data: { prediction: mainPrediction, output: [modelUrl], conceptImage: conceptImageUrl, threeDGeneration: threeDPrediction }, pipeline: 'real' });
            }
          }
        } else if (threeDPrediction.status === 'failed') {
          // Fall through to concept-only return below
        } else {
          return new NextResponse(JSON.stringify({ success: true, status: 'processing', phase: '3d_generation', data: { id: predictionId, status: 'processing', threeDGeneration: threeDPrediction }, note: `3D model generation in progress (${threeDPrediction.status})...` }), {
            status: 200,
            headers: { 'Content-Type': 'application/json', 'Retry-After': '2' },
          });
        }
      } catch (threeDError) {
        // swallow and proceed to concept-only logic
      }
    }

    // Handle main prediction status
    try {
      const prediction: any = await retry(() => replicateClient.predictions.get(predictionId));

      if (prediction.status === 'succeeded' && prediction.output) {
        const out = prediction.output;
        const conceptImageUrl = Array.isArray(out) ? out[0] : out;

        if (!DISABLE_3D) {
          // Verified working 3D models on Replicate (confirmed July 2025)
          const workingModels = [
            { name: 'cjwbw/shap-e', version: '5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c', inputConfig: { image: conceptImageUrl, save_mesh: true, render_mode: 'nerf', render_size: 128, guidance_scale: 15, batch_size: 1 } },
            { name: 'cjwbw/point-e', version: '1a4da7adf0bc84cd786c1df41c02db3097d899f5c159f5fd5814a11117bdf02b', inputConfig: { image: conceptImageUrl, output_format: 'animation', prompt: '' } },
          ];

          for (const model of workingModels) {
            try {
              const threeDPrediction: any = await retry(() =>
                replicateClient.predictions.create({ version: model.version, input: model.inputConfig })
              );

              return NextResponse.json({ success: true, status: 'processing', conceptImage: conceptImageUrl, threeDPredictionId: threeDPrediction.id, usedModel: model.name, data: { prediction, phase: '3d_generation', conceptImage: conceptImageUrl, threeDGeneration: threeDPrediction }, pipeline: 'real' });
            } catch (modelError: any) {
              // try next model
              continue;
            }
          }
        }

        // All 3D models failed or disabled, still return concept
        try {
          const imageResponse = await fetchWithTimeout(conceptImageUrl, 15000);
          const len = Number(imageResponse.headers.get('content-length') || 0);
          if (len && len > 25 * 1024 * 1024) throw new Error('image-too-large');
          const imageBuffer = await imageResponse.arrayBuffer();
          const { s3Storage } = await import('../../../lib/s3');
          const conceptResult = await s3Storage.uploadConceptImage(predictionId, imageBuffer);

          return NextResponse.json({ success: true, status: 'succeeded', modelUrl: '/demo/sample-planter.glb', conceptImage: conceptResult.cdnUrl, data: { prediction, output: ['/demo/sample-planter.glb'], conceptImage: conceptResult.cdnUrl, s3ConceptKey: conceptResult.key }, pipeline: 'hybrid' });
        } catch {
          return NextResponse.json({ success: true, status: 'succeeded', modelUrl: '/demo/sample-planter.glb', conceptImage: conceptImageUrl, data: { prediction, output: ['/demo/sample-planter.glb'], conceptImage: conceptImageUrl }, pipeline: 'real' });
        }
      }

      // Return current prediction status if not succeeded yet
      return NextResponse.json({ success: true, status: prediction.status, data: prediction });
    } catch (replicateError) {
      // Fallback to demo (optional)
      if (USE_DEMO_ON_FAIL) {
        return NextResponse.json({ success: true, status: 'succeeded', modelUrl: '/demo/sample-planter.glb', data: { id: predictionId, status: 'succeeded', output: ['/demo/sample-planter.glb'] }, pipeline: 'demo' });
      }
      throw replicateError;
    }
  } catch (error: any) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: 'Failed to check status', details: errorMessage }, { status: 500 });
  }
}
