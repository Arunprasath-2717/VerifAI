import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { captured_text, url, page_title, source_app, selector } = body;

    if (!captured_text || typeof captured_text !== 'string' || !captured_text.trim()) {
      return NextResponse.json(
        { status: 'error', message: 'captured_text is required' },
        { status: 400 }
      );
    }

    const item = chatStore.addExtensionCapture({
      captured_text: captured_text.trim(),
      url,
      page_title,
      source_app,
      selector,
    });

    return NextResponse.json({
      status: 'success',
      data: item,
    });
  } catch (error) {
    console.error('Error in POST /api/v1/extension/capture:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to capture content' },
      { status: 500 }
    );
  }
}
