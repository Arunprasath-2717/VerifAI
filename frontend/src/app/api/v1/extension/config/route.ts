import { NextResponse } from 'next/server';
import { DEFAULT_EXTENSION_CONFIG } from '@/lib/chat-store';

export async function GET() {
  try {
    return NextResponse.json({
      status: 'success',
      data: DEFAULT_EXTENSION_CONFIG,
    });
  } catch (error) {
    return NextResponse.json(
      { status: 'error', message: 'Failed to fetch extension configuration' },
      { status: 500 }
    );
  }
}
