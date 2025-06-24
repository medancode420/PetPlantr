import { NextRequest, NextResponse } from 'next/server'
import { currentUser } from '@clerk/nextjs/server'

// Lambda endpoint URL
const LAMBDA_URL = 'https://t2tugpetrj.execute-api.us-east-1.amazonaws.com/prod/api/chat/upload'

export async function POST(req: NextRequest) {
  try {
    // Check authentication (optional - uncomment to require auth)
    // const user = await currentUser()
    // if (!user) {
    //   return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    // }

    const body = await req.json()
    const { message, context } = body

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 })
    }

    // Proxy request to Lambda function
    const response = await fetch(LAMBDA_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        context: context || 'User is asking about photo upload process for creating 3D pet planters'
      }),
    })

    if (!response.ok) {
      throw new Error(`Lambda function error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    )
  }
}
