import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';

export async function POST(
  req: NextRequest,
  { params }: { params: { conversation_id: string } }
) {
  try {
    const { conversation_id } = params;
    const body = await req.json();
    const { message, model } = body;

    if (!message || typeof message !== 'string' || !message.trim()) {
      return NextResponse.json(
        { status: 'error', message: 'Message text is required' },
        { status: 400 }
      );
    }

    const conversation = chatStore.getConversation(conversation_id);
    if (!conversation) {
      return NextResponse.json(
        { status: 'error', message: `Conversation ${conversation_id} not found` },
        { status: 404 }
      );
    }

    const userMessage = chatStore.addMessage(conversation_id, 'user', message.trim(), model);

    // Generate AI answer
    const aiText = `Response to message: "${message.trim()}". Standard AI assistant output with factual statements available for verification.`;
    const aiMessage = chatStore.addMessage(conversation_id, 'assistant', aiText, model || conversation.model);

    return NextResponse.json({
      status: 'success',
      data: {
        user_message: userMessage,
        ai_message: aiMessage,
      },
    });
  } catch (error) {
    console.error('Error in POST /api/v1/chat/[conversation_id]/messages:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to append message' },
      { status: 500 }
    );
  }
}
