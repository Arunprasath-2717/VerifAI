import { NextRequest } from 'next/server';
import { chatStore } from '@/lib/chat-store';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { conversation_id, message, model } = body;

    if (!message || typeof message !== 'string' || !message.trim()) {
      return new Response(
        JSON.stringify({ status: 'error', message: 'Message content is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    let conv = conversation_id ? chatStore.getConversation(conversation_id) : null;
    if (!conv) {
      conv = chatStore.createConversation(model || 'gpt-4o');
    }

    // Add user message to conversation store
    const userMsg = chatStore.addMessage(conv.id, 'user', message.trim(), model);

    const fullResponse = getStreamTextResponse(message.trim(), model || conv.model);
    const tokens = fullResponse.split(/(\s+)/); // split by words & spaces for natural chunking

    const encoder = new TextEncoder();

    const stream = new ReadableStream({
      async start(controller) {
        // Send initial metadata
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ type: 'start', conversation_id: conv.id, user_message: userMsg })}\n\n`)
        );

        let accumulatedText = '';

        for (const token of tokens) {
          accumulatedText += token;
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ type: 'chunk', content: token })}\n\n`)
          );
          // Micro delay for realistic token streaming rate
          await new Promise((r) => setTimeout(r, 25));
        }

        // Save AI response to chat store upon completion
        const aiMsg = chatStore.addMessage(conv.id, 'assistant', accumulatedText, model || conv.model);

        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ type: 'done', ai_message: aiMsg })}\n\n`)
        );
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Error in POST /api/v1/chat/stream:', error);
    return new Response(
      JSON.stringify({ status: 'error', message: 'Failed to establish streaming response' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

function getStreamTextResponse(prompt: string, model: string): string {
  const p = prompt.toLowerCase();
  if (p.includes('apollo') || p.includes('moon') || p.includes('nasa')) {
    return `NASA's Apollo 11 mission landed the first humans on the Moon on July 20, 1969. Commander Neil Armstrong and Lunar Module Pilot Buzz Aldrin landed the Apollo Lunar Module Eagle. Armstrong became the first person to walk on the lunar surface six hours and 39 minutes later on July 21.`;
  }
  if (p.includes('vaccine') || p.includes('mrna') || p.includes('dna')) {
    return `mRNA vaccines operate by delivering a small strand of messenger RNA into host cells. This instructs cells to temporarily synthesize a harmless target protein (such as the viral spike protein), triggering an adaptive immune response without introducing live virus particles.`;
  }
  return `Analyzing query using [${model}]: "${prompt}". The statement provides key claims regarding domain concepts. You can verify these factual assertions directly using Arun's verification engine by clicking "Verify".`;
}
