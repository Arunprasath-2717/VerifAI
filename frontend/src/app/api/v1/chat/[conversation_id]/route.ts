import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';

export async function GET(
  req: NextRequest,
  { params }: { params: { conversation_id: string } }
) {
  try {
    const { conversation_id } = params;

    if (conversation_id === 'all') {
      const conversations = chatStore.getConversations();
      return NextResponse.json({ status: 'success', data: conversations });
    }

    const conversation = chatStore.getConversation(conversation_id);
    if (!conversation) {
      return NextResponse.json(
        { status: 'error', message: `Conversation with ID ${conversation_id} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      status: 'success',
      data: conversation,
    });
  } catch (error) {
    console.error('Error in GET /api/v1/chat/[conversation_id]:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to retrieve conversation' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: { conversation_id: string } }
) {
  try {
    const { conversation_id } = params;

    const deleted = chatStore.deleteConversation(conversation_id);
    if (!deleted) {
      return NextResponse.json(
        { status: 'error', message: `Conversation ${conversation_id} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      status: 'success',
      message: `Conversation ${conversation_id} deleted successfully`,
    });
  } catch (error) {
    console.error('Error in DELETE /api/v1/chat/[conversation_id]:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to delete conversation' },
      { status: 500 }
    );
  }
}
