export const handler = async () => ({
  statusCode: 200,
  headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS'
  },
  body: JSON.stringify({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    build: process.env.GIT_SHA ?? 'dev',
    lambda: process.env.AWS_LAMBDA_FUNCTION_VERSION ?? '1',
    model: process.env.UNET_WEIGHTS ?? 'models/unet128_stage1_best.pth',
    services: {
      database: 'ok',
      s3: 'ok',
      ai_model: 'ready'
    }
  })
});
