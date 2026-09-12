import { NextRequest, NextResponse } from 'next/server';
import { ArunVerificationService } from '@/lib/arun-verification-service';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { text, url, page_title, source_app } = body;

    if (!text || typeof text !== 'string' || !text.trim()) {
      return NextResponse.json(
        { status: 'error', message: 'Text to verify is required' },
        { status: 400 }
      );
    }

    // Forward to Arun's verification engine
    const verification = await ArunVerificationService.createVerification(text.trim(), {
      source: source_app || 'browser_extension',
    });

    const claims = await ArunVerificationService.getClaims(verification.verification_id);

    return NextResponse.json({
      status: 'success',
      data: {
        verification,
        claims,
      },
    });
  } catch (error) {
    console.error('Error in POST /api/v1/extension/verify:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to verify extension selection' },
      { status: 500 }
    );
  }
}
