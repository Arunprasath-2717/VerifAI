import { NextResponse } from 'next/server';
import { AVAILABLE_MODELS } from '@/lib/chat-store';

export async function GET() {
  try {
    return NextResponse.json({
      status: 'success',
      data: AVAILABLE_MODELS,
    });
  } catch (error) {
    return NextResponse.json(
      { status: 'error', message: 'Failed to retrieve models' },
      { status: 500 }
    );
  }
}
