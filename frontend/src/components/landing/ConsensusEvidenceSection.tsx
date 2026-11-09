import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { ArrowRight, RotateCcw, XCircle } from 'lucide-react';

const echoes = [
  { letter: 'A', statement: 'Lightning never strikes the same place twice.' },
  { letter: 'B', statement: 'A location cannot receive a second lightning strike.' },
  { letter: 'C', statement: 'Lightning always chooses a different point.' },
] as const;

export function ConsensusEvidenceSection() {
  const [evidenceShown, setEvidenceShown] = useState(false);

  return (
    <section className="vi-chorus" id="consensus" aria-labelledby="vi-consensus-title">
      <div className="vi-container">
        <div className="vi-chorus-heading">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: .7 }}>
            <h2 id="vi-consensus-title">THREE VOICES.<br /><em>One mistake.</em></h2>
          </motion.div>
          <div className="vi-chorus-context">
            <p>Three different phrasings. One shared misconception. See why agreement among AI answers should never be mistaken for independent proof.</p>
          </div>
        </div>

        <p className="vi-example-disclosure">The three responses below are hypothetical examples, not live model outputs.</p>
        <div className="vi-chorus-board vm-chorus-board">
          <div className="vi-chorus-voices">
            {echoes.map((voice, i) => (
              <motion.article key={voice.letter} className="vi-chorus-voice vm-chorus-voice"
                initial={{ opacity: 0, y: 25 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: .22 }}
                transition={{ duration: .55, delay: i * .1 }}>
                <div className="vi-chorus-voice-top"><strong>{voice.letter}</strong></div>
                <p>“{voice.statement}”</p>
              </motion.article>
            ))}
          </div>
          <div className="vi-chorus-connector" aria-hidden="true"><i /><i /><i /><span /></div>
          <div className="vi-chorus-statement">
            <div><strong>3 of 3 agree.</strong></div>
            <p>But agreement doesn’t test reality.</p>
            <button className="vi-chorus-action" type="button" onClick={() => setEvidenceShown((v) => !v)} aria-expanded={evidenceShown} aria-controls="vi-chorus-reveal">
              {evidenceShown ? 'Hide the evidence' : 'Reveal the evidence'} {evidenceShown ? <RotateCcw size={18} strokeWidth={1.6} /> : <ArrowRight size={18} strokeWidth={1.6} />}
            </button>
          </div>
          <AnimatePresence initial={false}>
            {evidenceShown && (
              <motion.div id="vi-chorus-reveal" key="evidence"
                initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }} transition={{ duration: .45 }}
                className="vi-chorus-reveal" aria-live="polite">
                <div className="vi-chorus-reveal-inner">
                  <div className="vi-chorus-reveal-mark"><XCircle size={27} strokeWidth={1.5} aria-hidden="true" /><span>Contradicted</span></div>
                  <p className="vi-chorus-reveal-head">Reality has<br /><em>a different answer.</em></p>
                  <div className="vi-chorus-reveal-text">
                    <p>Lightning can strike the same place repeatedly. Tall structures, such as towers, may be struck many times. All three example answers are wrong.</p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
