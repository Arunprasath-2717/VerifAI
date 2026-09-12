import { NextRequest, NextResponse } from 'next/server';
import { ArunVerificationService } from '@/lib/arun-verification-service';

export async function POST(
  req: NextRequest,
  { params }: { params: { conversation_id: string } }
) {
  try {
    const { conversation_id } = params;
    const body = await req.json().catch(() => ({}));
    const { verification_id } = body;

    if (!verification_id) {
      return NextResponse.json(
        { status: 'error', message: 'verification_id is required for reverification' },
        { status: 400 }
      );
    }

    // Forward request to Arun's reverify API
    const updatedVerification = await ArunVerificationService.reverify(verification_id);
    const updatedClaims = await ArunVerificationService.getClaims(verification_id);

    return NextResponse.json({
      status: 'success',
      data: {
        verification: updatedVerification,
        claims: updatedClaims,
      },
    });
  } catch (error) {
    console.error('Error in POST /api/v1/chat/[conversation_id]/reverify:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to reverify conversation' },
      { status: 500 }
    );
  }
}
