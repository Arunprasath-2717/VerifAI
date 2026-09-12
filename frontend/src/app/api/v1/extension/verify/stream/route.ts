import { NextRequest } from 'next/server';
import { ArunVerificationService } from '@/lib/arun-verification-service';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { text, url } = body;

    if (!text || typeof text !== 'string' || !text.trim()) {
      return new Response(
        JSON.stringify({ status: 'error', message: 'Text to verify is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const encoder = new TextEncoder();

    // Trigger Arun verification
    const initialVerification = await ArunVerificationService.createVerification(text.trim(), {
      source: 'extension_stream',
    });

    const stream = new ReadableStream({
      async start(controller) {
        // Step 1: Initializing verification
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              step: 'INIT',
              status: 'queued',
              message: 'Initializing verification with Arun core engine...',
              verification_id: initialVerification.verification_id,
            })}\n\n`
          )
        );
        await new Promise((r) => setTimeout(r, 400));

        // Step 2: Extracting Claims
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              step: 'CLAIM_EXTRACTION',
              status: 'processing',
              message: 'Extracting factual assertions from captured text...',
              verification_id: initialVerification.verification_id,
            })}\n\n`
          )
        );
        await new Promise((r) => setTimeout(r, 500));

        // Fetch claims
        const claims = await ArunVerificationService.getClaims(initialVerification.verification_id);

        // Step 3: Evidence Search
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              step: 'EVIDENCE_SEARCH',
              status: 'processing',
              message: 'Cross-referencing evidence databases and authoritative sources...',
              verification_id: initialVerification.verification_id,
              claims_count: claims.length,
            })}\n\n`
          )
        );
        await new Promise((r) => setTimeout(r, 600));

        // Step 4: Verification Finalized
        const finalVerification = await ArunVerificationService.getVerification(initialVerification.verification_id);

        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              step: 'COMPLETED',
              status: 'completed',
              verification: finalVerification,
              claims: claims,
            })}\n\n`
          )
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
    console.error('Error in POST /api/v1/extension/verify/stream:', error);
    return new Response(
      JSON.stringify({ status: 'error', message: 'Failed to establish extension verification stream' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
