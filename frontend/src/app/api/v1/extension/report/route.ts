import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { url, page_title, reason, html_snippet, timestamp } = body;

    if (!reason) {
      return NextResponse.json(
        { status: 'error', message: 'Report reason is required' },
        { status: 400 }
      );
    }

    const report = {
      url: url || '',
      page_title: page_title || '',
      reason,
      html_snippet: html_snippet ? html_snippet.slice(0, 500) : '',
      timestamp: timestamp || new Date().toISOString(),
    };

    chatStore.addCaptureReport(report);

    return NextResponse.json({
      status: 'success',
      message: 'Capture failure report recorded successfully',
      data: report,
    });
  } catch (error) {
    console.error('Error in POST /api/v1/extension/report:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to record capture report' },
      { status: 500 }
    );
  }
}
