import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { CheckCircle2, CircleHelp, XCircle } from 'lucide-react';

const examples = [
  {
    title: 'The familiar myth', category: 'Observation',
    claim: 'The Great Wall of China is visible from the Moon with the naked eye.',
    note: 'The wall is too narrow and lacks sufficient contrast to be identified from lunar distance without optical assistance.',
    assessment: 'Contradicted',
    takeaway: 'A widely repeated statement is not necessarily a supported one.',
    signal: 'Astronaut observations · optical limits', icon: XCircle, status: 'contradicted',
  },
  {
    title: 'The established fact', category: 'Astronomy',
    claim: 'Earth completes an orbit around the Sun in approximately one year.',
    note: 'The period of Earth’s orbit is well established through independent astronomical observation.',
    assessment: 'Supported',
    takeaway: 'Reliable evidence can support a claim without requiring artificial certainty.',
    signal: 'Astronomical measurements · observations', icon: CheckCircle2, status: 'supported',
  },
  {
    title: 'The absolute prediction', category: 'Future claims',
    claim: 'The next generation of AI models will never make a factual mistake.',
    note: 'A claim about the behaviour of future systems cannot be demonstrated by current evidence, particularly when it guarantees “never.”',
    assessment: 'Not established',
    takeaway: 'Uncertainty is a valid conclusion when sufficient evidence does not exist.',
    signal: 'Insufficient testable evidence', icon: CircleHelp, status: 'unknown',
  },
] as const;

export function ClaimExhibitSection() {
  const [activeIndex, setActiveIndex] = useState(0);
  const example = examples[activeIndex];
  const StatusIcon = example.icon;

  return (
    <section className="vi-exhibit" id="difference" aria-labelledby="vi-difference-title">
      <div className="vi-container">
        <div className="vi-exhibit-intro">
          <motion.div initial={{ opacity: 0, y: 22 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: .7 }}>
            <h2 id="vi-difference-title">SOUNDS TRUE.<br /><em>Is it?</em></h2>
          </motion.div>
          <div className="vi-exhibit-dek">
            <span className="vi-exhibit-rule" aria-hidden="true" />
            <p>An answer can be fluent, familiar and completely wrong. Read a claim like a case file: separate the statement from the evidence.</p>
          </div>
        </div>

        <div className="vi-exhibit-paper vm-exhibit-paper" onPointerMove={(event)=>{const rect=event.currentTarget.getBoundingClientRect();event.currentTarget.style.setProperty("--mx",(event.clientX-rect.left)+"px");event.currentTarget.style.setProperty("--my",(event.clientY-rect.top)+"px");}}>
          <div className="vi-exhibit-sheet">
            <div className="vi-exhibit-statement">
              <AnimatePresence mode="wait">
                <motion.blockquote
                  key={activeIndex}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: .24 }}
                >
                  “{example.claim}”
                </motion.blockquote>
              </AnimatePresence>
            </div>
          </div>

          <div className="vi-exhibit-analysis">
            <AnimatePresence mode="wait">
              <motion.div className="vi-exhibit-analysis-body" key={activeIndex}
                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                transition={{ duration: .24 }}
              >
                <div className={'vi-exhibit-verdict is-' + example.status}><StatusIcon size={26} strokeWidth={1.5} aria-hidden="true" />{example.assessment}</div>
                <p>{example.note}</p>
                <div className="vi-exhibit-source">
                  <strong>{example.signal}</strong>
                </div>
                <div className="vi-exhibit-takeaway"><p>{example.takeaway}</p></div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        <p className="vi-example-disclosure">Illustrative examples only — not live verification results.</p>
        <div className="vi-exhibit-index" aria-label="Choose an illustrative claim">
          {examples.map((item, i) => (
            <button key={item.title} type="button" onClick={() => setActiveIndex(i)}
              aria-pressed={activeIndex === i}
              className={'vi-exhibit-index-item vm-exhibit-tab' + (activeIndex === i ? ' is-active' : '')}>
              <span className="vi-exhibit-index-copy"><strong>{item.title}</strong></span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
