import { NextRequest, NextResponse } from 'next/server';
import { chatStore } from '@/lib/chat-store';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { conversation_id, message, model } = body;

    if (!message || typeof message !== 'string' || !message.trim()) {
      return NextResponse.json(
        { status: 'error', message: 'Message content is required' },
        { status: 400 }
      );
    }

    let conv = conversation_id ? chatStore.getConversation(conversation_id) : null;
    if (!conv) {
      conv = chatStore.createConversation(model || 'gpt-4o');
    }

    // Add user message
    const userMsg = chatStore.addMessage(conv.id, 'user', message.trim(), model);

    // AI Response synthesis based on model & prompt
    const aiResponseText = generateAIResponse(message.trim(), model || conv.model);
    const aiMsg = chatStore.addMessage(conv.id, 'assistant', aiResponseText, model || conv.model);

    return NextResponse.json({
      status: 'success',
      data: {
        conversation_id: conv.id,
        user_message: userMsg,
        ai_message: aiMsg,
      },
    });
  } catch (error) {
    console.error('Error in POST /api/v1/chat:', error);
    return NextResponse.json(
      { status: 'error', message: 'Failed to process chat request' },
      { status: 500 }
    );
  }
}

function generateAIResponse(userMessage: string, model: string): string {
  const lowerMsg = userMessage.toLowerCase();
  
  if (lowerMsg.includes('quantum') || lowerMsg.includes('physics')) {
    return `Quantum computing leverages quantum mechanical phenomena such as superposition and entanglement to perform calculations. Unlike classical bits that store either 0 or 1, qubits can exist in a superposition of states, allowing quantum computers to evaluate complex probabilistic equations simultaneously.`;
  }
  
  if (lowerMsg.includes('climate') || lowerMsg.includes('temperature') || lowerMsg.includes('earth')) {
    return `According to global climate monitoring data, global average surface temperature has increased by approximately 1.1°C to 1.2°C compared to pre-industrial baseline levels (1850–1900). Carbon dioxide atmospheric concentrations recently exceeded 420 parts per million.`;
  }

  if (lowerMsg.includes('who created') || lowerMsg.includes('who wrote') || lowerMsg.includes('python')) {
    return `Python was created by Guido van Rossum and first released on February 20, 1991. It emphasizes code readability with its notable use of significant whitespace.`;
  }

  return `Here is the response using model [${model}]: "${userMessage}". VerifAI enables real-time factual claim verification. Click the "Verify" button below this message to run Arun's core verification pipeline on these assertions.`;
}
