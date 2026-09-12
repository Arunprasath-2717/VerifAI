import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';
import { ArunVerificationService } from '@/lib/arun-verification-service';

export async function POST(
  req: NextRequest,
  { params }: { params: { conversation_id: string; message_id: string } }
) {
  try {
    const { conversation_id, message_id } = params;

    const conversation = chatStore.getConversation(conversation_id);
    if (!conversation) {
      return NextResponse.json(
        { status: 'error', message: `Conversation ${conversation_id} not found` },
        { status: 404 }
      );
    }

    const message = conversation.messages.find((m) => m.id === message_id);
    if (!message) {
      return NextResponse.json(
        { status: 'error', message: `Message ${message_id} not found in conversation` },
        { status: 404 }
      );
    }

    // Update status to pending
    chatStore.updateMessageVerification(conversation_id, message_id, '', 'pending');

    // Forward verification to Arun's service
    const verificationResult = await ArunVerificationService.createVerification(message.content, {
      conversation_id,
      message_id,
      source: 'chat_message',
    });

    // Update message with exact verification ID from Arun
    chatStore.updateMessageVerification(
      conversation_id,
      message_id,
      verificationResult.verification_id,
      'completed'
    );

    const claims = await ArunVerificationService.getClaims(verificationResult.verification_id);

    return NextResponse.json({
      status: 'success',
      data: {
        verification: verificationResult,
        claims,
      },
    });
  } catch (error) {
    console.error('Error in message verification endpoint:', error);
    chatStore.updateMessageVerification(params.conversation_id, params.message_id, '', 'failed');
    return NextResponse.json(
      { status: 'error', message: 'Failed to verify message content' },
      { status: 500 }
    );
  }
}
