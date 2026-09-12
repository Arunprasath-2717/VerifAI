import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';
import { ArunVerificationService } from '@/lib/arun-verification-service';

export async function POST(
  req: NextRequest,
  { params }: { params: { conversation_id: string } }
) {
  try {
    const { conversation_id } = params;
    const conversation = chatStore.getConversation(conversation_id);

    if (!conversation) {
      return NextResponse.json(
        { status: 'error', message: `Conversation ${conversation_id} not found` },
        { status: 404 }
      );
    }

    // Extract conversation content text to verify
    const contentToVerify = conversation.messages
      .filter((m) => m.role === 'assistant')
      .map((m) => m.content)
      .join('\n\n');

    if (!contentToVerify) {
      return NextResponse.json(
        { status: 'error', message: 'No AI responses found in conversation to verify' },
        { status: 400 }
      );
    }

    // Forward request to Arun's core verification service
    const verification = await ArunVerificationService.createVerification(contentToVerify, {
      conversation_id,
      source: 'chat_conversation',
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
    console.error('Error in POST /api/v1/chat/[conversation_id]/verify:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to initiate conversation verification' },
      { status: 500 }
    );
  }
}
