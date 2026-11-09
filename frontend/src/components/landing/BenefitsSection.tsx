import { useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { CheckCircle2, CircleHelp, XCircle } from 'lucide-react';

const reveal = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.14 },
  transition: { duration: 0.6 },
} as const;

export function BenefitsSection() {
  const reduceMotion = useReducedMotion();
  const [orbVideoFailed, setOrbVideoFailed] = useState(false);
  const entrance = reduceMotion ? {} : reveal;

  return (
    <section className="vi-benefits" id="benefits" aria-labelledby="vi-benefits-title">
      <div className="vi-container">
        <motion.header className="vi-benefits-head" {...entrance}>
          <div className="vi-benefits-head-main">
            <h2 id="vi-benefits-title"><span>KEY</span> <em>Benefits.</em></h2>
          </div>
          <p className="vi-benefits-intro">
            Less guesswork. More context. A clearer way to understand whether an AI-generated answer deserves confidence.
          </p>
        </motion.header>

        <div className="vi-benefits-grid">
          <motion.article className="vi-benefit-card vi-benefit-card-left" {...entrance}>
            <h3>Question the confident answer.</h3>
            <div className="vi-benefit-panel" aria-hidden="true">
              <div className="vi-benefit-panel-lines"><span /><span /><span /></div>
              <strong>“Well-written” does not mean “well-supported.”</strong>
            </div>
            <p>
              Break polished responses into testable claims. See what was actually asserted before deciding whether it is trustworthy.
            </p>
          </motion.article>

          <motion.article className="vi-benefit-card vi-benefit-card-center" {...entrance}>
            <div className="vi-benefit-video-wrap">
              {orbVideoFailed ? (
                // Replace the video rather than layering a static image behind it.
                <img
                  className="vi-benefit-video vi-benefit-fallback"
                  src="/cinema/benefits-orb-poster.jpg"
                  alt="Abstract evidence orb"
                />
              ) : (
                <video
                  className="vi-benefit-video"
                  src="/cinema/benefits-orb.mp4"
                  poster="/cinema/benefits-orb-poster.jpg"
                  autoPlay={!reduceMotion} loop={!reduceMotion} muted playsInline preload="auto"
                  onCanPlay={event => {
                    if (!reduceMotion && event.currentTarget.paused) {
                      void event.currentTarget.play().catch(() => {
                        // Autoplay blocked: the video's native poster remains visible.
                      });
                    }
                  }}
                  onError={() => setOrbVideoFailed(true)}
                  aria-label="Abstract animated evidence visual"
                />
              )}
              <div className="vi-benefit-video-fade" aria-hidden="true" />
            </div>
            <div className="vi-benefit-video-copy">
              <h3>Evidence with a paper trail.</h3>
              <p>
                A useful verdict should show its basis. Understand the context, reasoning, and supporting material behind the assessment.
              </p>
            </div>
          </motion.article>

          <motion.article className="vi-benefit-card vi-benefit-card-right" {...entrance}>
            <h3>Make room for what remains unknown.</h3>
            <p>
              Responsible verification does not force every answer into a clean yes-or-no. It separates what is supported, contradicted, and unresolved.
            </p>
            <div className="vi-benefit-outcomes" aria-label="Assessment outcomes">
              <div><CheckCircle2 size={15} strokeWidth={1.7} aria-hidden="true" /><span>Supported</span></div>
              <div><XCircle size={15} strokeWidth={1.7} aria-hidden="true" /><span>Contradicted</span></div>
              <div><CircleHelp size={15} strokeWidth={1.7} aria-hidden="true" /><span>Unresolved</span></div>
            </div>
          </motion.article>
        </div>
      </div>
    </section>
  );
}
