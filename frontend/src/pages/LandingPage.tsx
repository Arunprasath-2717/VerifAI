import { useEffect, useRef } from 'react';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';
import { animate } from 'animejs';
import {
  motion, useReducedMotion, useScroll, useSpring, useTransform,
} from 'motion/react';
import {
  ArrowDown, ArrowRight, ArrowUpRight, Check, CheckCheck,
  CircleHelp, FileCheck2, Fingerprint, GitCompareArrows,
  LockKeyhole, Search, ShieldCheck, Sparkles, X,
} from 'lucide-react';
import './LandingPage.css';

interface LandingPageProps { isAuthenticated: boolean }

const pipeline = [
  {
    step: '01',
    verb: 'Extract',
    title: 'Find the claims hiding in the answer.',
    description: 'The response becomes a set of testable statements — not a single confidence score.',
    detail: 'Each factual claim gets its own trail.',
  },
  {
    step: '02',
    verb: 'Investigate',
    title: 'Follow the trail to its sources.',
    description: 'Look up evidence in private knowledge or permitted web sources and preserve where it came from.',
    detail: 'Provenance matters as much as the result.',
  },
  {
    step: '03',
    verb: 'Decide',
    title: 'Tell the truth, even when it is uncertain.',
    description: 'Evidence can support a claim, contradict it, or leave it unresolved. Agreement alone is never proof.',
    detail: 'UNKNOWN is a responsible outcome.',
  },
];

const reveal = {
  initial: { opacity: 0.64, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.18 },
  transition: { duration: 0.85, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
};

function Logo() {
  return (
    <span className="vc-logo">
      <span className="vc-logo-mark" aria-hidden="true"><ShieldCheck size={19} strokeWidth={2.3} /></span>
      <span>verif<span>ai</span><i>.</i></span>
    </span>
  );
}

function VerificationTheatre() {
  return (
    <div className="vc-theatre" aria-label="Illustrative 3D verification sequence">
      <div className="vc-theatre-aura" aria-hidden="true" />
      <div className="vc-orbit vc-orbit-one" aria-hidden="true"><i /><b /></div>
      <div className="vc-orbit vc-orbit-two" aria-hidden="true" />
      <div className="vc-orbit vc-orbit-three" aria-hidden="true" />
      <div className="vc-model-node vc-model-node-one" aria-hidden="true">
        <span>MODEL 01</span><strong>Agreement</strong><i><b /></i>
      </div>
      <div className="vc-model-node vc-model-node-two" aria-hidden="true">
        <span>MODEL 02</span><strong>Agreement</strong><i><b /></i>
      </div>
      <div className="vc-model-node vc-model-node-three" aria-hidden="true">
        <span>MODEL 03</span><strong>Agreement</strong><i><b /></i>
      </div>
      <div className="vc-proof-object">
        <div className="vc-proof-topline">
          <span><ShieldCheck size={15} /> VERIFAI / EVIDENCE ENGINE</span>
          <span>FIG. 01</span>
        </div>
        <div className="vc-proof-content">
          <div className="vc-proof-question">Three models agree.<br /><span>Is it true?</span></div>
          <div className="vc-proof-divider" />
          <div className="vc-proof-signal">
            <span>MODEL CONSENSUS</span>
            <strong><span className="vc-signal-bars"><i/><i/><i/><i/></span> HIGH</strong>
          </div>
          <div className="vc-proof-signal">
            <span>INDEPENDENT EVIDENCE</span>
            <strong>INSUFFICIENT</strong>
          </div>
          <div className="vc-proof-result">
            <span>VERIFICATION OUTCOME</span>
            <strong><CircleHelp size={25} /> UNKNOWN</strong>
            <small>Agreement is a signal, not a source.</small>
          </div>
        </div>
        <div className="vc-proof-foot"><span>ILLUSTRATIVE TRACE</span><span>NOT A LIVE VERDICT</span></div>
      </div>
      <div className="vc-theatre-crosshair vc-crosshair-one" aria-hidden="true" />
      <div className="vc-theatre-crosshair vc-crosshair-two" aria-hidden="true" />
    </div>
  );
}

function CompareVisual() {
  return (
    <div className="vc-compare-visual" aria-hidden="true">
      <div className="vc-compare-top"><span><i /> LIVE COMPARISON / PREVIEW</span><span>03 CHANNELS</span></div>
      <div className="vc-compare-prompt"><span>YOUR QUESTION</span><strong>What can we actually verify?</strong><ArrowUpRight size={22}/></div>
      <div className="vc-model-lanes">
        {['01', '02', '03'].map((id, i) => (
          <div className="vc-lane" key={id}>
            <span className="vc-lane-label">MODEL {id}</span>
            <div className="vc-lane-lines"><i /><i /><i /></div>
            <span className="vc-lane-state">{i === 1 ? 'DISAGREES' : 'RESPONDED'}</span>
          </div>
        ))}
      </div>
      <div className="vc-compare-merge"><span><Sparkles size={17}/> COMBINED ANALYSIS</span><span>COMPARE • SYNTHESIZE • VERIFY</span></div>
    </div>
  );
}

function VerifyVisual() {
  return (
    <div className="vc-verify-visual" aria-hidden="true">
      <div className="vc-source-orbit"><div/><div/></div>
      <div className="vc-source-document">
        <div className="vc-doc-head"><span><FileCheck2 size={18}/> INPUT / CLAIMS</span><span>TEXT</span></div>
        <p>AI-generated text contains many things that sound correct.</p>
        <div className="vc-highlight-line">A factual statement can be checked.<span>CLAIM DETECTED</span></div>
        <div className="vc-doc-line"/><div className="vc-doc-line short"/>
      </div>
      <div className="vc-verdict-stamp"><CheckCheck size={18}/><span>CLAIM-LEVEL<br/>EVIDENCE TRAIL</span></div>
      <div className="vc-source-pill pill-one"><Search size={14}/> SOURCE RETRIEVED</div>
      <div className="vc-source-pill pill-two"><Fingerprint size={14}/> PROVENANCE KEPT</div>
    </div>
  );
}

export function LandingPage({ isAuthenticated }: LandingPageProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const filmRef = useRef<HTMLElement>(null);
  const processRef = useRef<HTMLElement>(null);
  const reducedMotion = useReducedMotion();
  const accountPath = isAuthenticated ? '/dashboard' : '/login';
  const launchPath = isAuthenticated ? '/dashboard' : '/login';
  const verifyPath = isAuthenticated ? '/verify' : '/login';
  const chatPath = isAuthenticated ? '/chat' : '/login';

  const { scrollYProgress: fullProgress } = useScroll();
  const { scrollYProgress: heroProgress } = useScroll({
    target: filmRef, offset: ['start start', 'end end'],
  });
  const eased = useSpring(heroProgress, { stiffness: 90, damping: 30, mass: 0.45 });
  const theatreY = useTransform(eased, [0, 0.38, 0.85, 1], [0, 0, -30, -70]);
  const theatreScale = useTransform(eased, [0, 0.34, 0.8, 1], [0.9, 1, 1.26, 1.38]);
  const theatreRotateY = useTransform(eased, [0, 0.42, 0.85, 1], [-16, -9, 15, 20]);
  const theatreRotateX = useTransform(eased, [0, 0.55, 1], [6, 0, -4]);
  const theatreOpacity = useTransform(eased, [0, 0.82, 1], [1, 1, 0.05]);
  const heroCopyOpacity = useTransform(eased, [0, 0.22, 0.38], [1, 1, 0]);
  const heroCopyY = useTransform(eased, [0, 0.4], [0, -65]);
  const secondActOpacity = useTransform(eased, [0.29, 0.47, 0.68, 0.89], [0, 1, 1, 0]);
  const secondActY = useTransform(eased, [0.3, 0.57, 0.9], [55, 0, -90]);
  const { scrollYProgress: processProgress } = useScroll({
    target: processRef, offset: ['start 70%', 'end 40%'],
  });

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const priorTitle = document.title;
    document.title = 'VerifAI — Beyond the answer';
    window.scrollTo({ top: 0, behavior: 'instant' });

    const isFinePointer = window.matchMedia('(pointer: fine)').matches;
    const lenis = isFinePointer ? new Lenis({
      autoRaf: true, lerp: 0.075, smoothWheel: true,
      touchMultiplier: 1, anchors: { offset: -12 },
      respectReducedMotion: true, stopInertiaOnNavigate: true,
    }) : null;

    const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');

    let orbitAnimation: ReturnType<typeof animate> | undefined;
    const orbit = root.querySelector<HTMLElement>('.vc-orbit-one');
    if (orbit && !motionPreference.matches) {
      orbitAnimation = animate(orbit, {
        rotate: '1turn', duration: 48000, ease: 'linear', loop: true,
      });
    }
    const onMotionChange = () => {
      if (motionPreference.matches) orbitAnimation?.pause();
      else orbitAnimation?.play();
    };
    const onVisibilityChange = () => {
      if (document.hidden) orbitAnimation?.pause();
      else if (!motionPreference.matches) orbitAnimation?.play();
    };
    motionPreference.addEventListener('change', onMotionChange);
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => {
      document.title = priorTitle;
      lenis?.destroy();
      motionPreference.removeEventListener('change', onMotionChange);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      orbitAnimation?.pause();
    };
  }, []);

  return (
    <div className="verifai-landing vc-page" ref={rootRef}>
      <a className="vc-skip" href="#vc-main">Skip to content</a>
      <motion.div className="vc-scroll-progress" style={{ scaleX: fullProgress }} aria-hidden="true" />

      <header className="vc-nav">
        <div className="vc-width vc-nav-content">
          <a href="#top" aria-label="VerifAI home" className="vc-logo-link"><Logo /></a>
          <nav aria-label="Main navigation" className="vc-nav-links">
            <a href="#experience">Experience</a><a href="#approach">Our approach</a>
          </nav>
          <div className="vc-nav-end">
            <a className="vc-nav-login" href={accountPath}>{isAuthenticated ? 'Dashboard' : 'Log in'}</a>
            <a className="vc-nav-button" href={launchPath}>Enter VerifAI <ArrowUpRight size={17}/></a>
          </div>
        </div>
      </header>

      <main id="vc-main">
        <section id="top" className="vc-film" ref={filmRef} aria-label="VerifAI cinematic introduction">
          <div className="vc-film-frame">
            <div className="vc-film-light" aria-hidden="true" />
            <div className="vc-film-vignette" aria-hidden="true" />
            <div className="vc-film-axis" aria-hidden="true"><span/><span/></div>

            <div className="vc-width vc-film-layout">
              <motion.div className="vc-film-copy" style={reducedMotion ? undefined : { opacity: heroCopyOpacity, y: heroCopyY }}>
                <h1>Beyond<br/>the <em>answer.</em></h1>
                <p>AI can sound certain about anything. VerifAI helps you see what the evidence actually says.</p>
                <div className="vc-hero-actions">
                  <a href={launchPath} className="vc-action vc-action-light">Explore VerifAI <ArrowUpRight size={19}/></a>
                  <a href="#experience" className="vc-action vc-action-outline">See the experience <ArrowDown size={19}/></a>
                </div>
                <div className="vc-scene-footnote"><span className="vc-glow-dot"/> Built for evidence, not blind confidence.</div>
              </motion.div>

              <motion.div className="vc-film-object" style={reducedMotion ? undefined : {
                opacity: theatreOpacity, y: theatreY, scale: theatreScale,
                rotateX: theatreRotateX, rotateY: theatreRotateY,
              }}>
                <VerificationTheatre />
              </motion.div>
            </div>

            <motion.div className="vc-film-act-two" aria-hidden="true" style={reducedMotion ? {opacity: 0} : { opacity: secondActOpacity, y: secondActY }}>
              <div className="vc-width">
                <p>Three answers.<br/>One question.</p>
                <h2>Where is<br/><em>the proof?</em></h2>
              </div>
            </motion.div>

            <div className="vc-film-caption vc-width">
              <span>VERIFAI / AN EVIDENCE-FIRST EXPERIENCE</span>
              <span className="vc-film-scroll-note">SCROLL TO EXPLORE <ArrowDown size={15}/></span>
            </div>
          </div>
        </section>

        <section className="vc-manifesto" id="experience" aria-labelledby="vc-manifesto-title">
          <div className="vc-width">
            <motion.div {...reveal} className="vc-manifesto-inner">
              <h2 id="vc-manifesto-title">Sounding right<br/>isn’t the same as<br/><em>being right.</em></h2>
              <div className="vc-manifesto-aside">
                <span className="vc-index">THE DIFFERENCE</span>
                <p>VerifAI separates polished language from provable facts. Compare model responses, question every claim, and keep uncertainty visible when sources fall short.</p>
                <span className="vc-manifesto-arrow"><ArrowDown size={34} strokeWidth={1.4}/></span>
              </div>
            </motion.div>
            <div className="vc-verdict-ticker" aria-label="Supported, contradicted, or unknown">
              <span><Check size={21}/> SUPPORTED</span><i/>
              <span><X size={21}/> CONTRADICTED</span><i/>
              <span><CircleHelp size={21}/> UNKNOWN</span>
            </div>
          </div>
        </section>

        <section className="vc-products" aria-label="VerifAI products">
          <div className="vc-width">
            <div className="vc-products-heading">
              <motion.h2 {...reveal}>One question.<br/><em>More clarity.</em></motion.h2>
              <motion.p {...reveal}>Two connected experiences. Both designed to move from plausible output to inspectable evidence.</motion.p>
            </div>

            <article className="vc-product-feature vc-compare-feature">
              <motion.div {...reveal} className="vc-product-copy">
                <span className="vc-product-number">01 / COMPARE</span>
                <h3>Put the models<br/>in conversation.</h3>
                <p>Send one prompt to up to three selected AI models, compare their responses, and bring the best thinking together — without mistaking consensus for truth.</p>
                <a className="vc-arrow-link" href={chatPath}>Explore AI Chat <span><ArrowUpRight size={21}/></span></a>
              </motion.div>
              <motion.div {...reveal} className="vc-product-visual-holder vc-product-compare-holder">
                <CompareVisual />
              </motion.div>
            </article>

            <article className="vc-product-feature vc-verify-feature">
              <motion.div {...reveal} className="vc-product-visual-holder vc-product-verify-holder">
                <VerifyVisual />
              </motion.div>
              <motion.div {...reveal} className="vc-product-copy">
                <span className="vc-product-number">02 / VERIFY</span>
                <h3>Make every<br/>claim answerable.</h3>
                <p>Paste an AI response or any text. Extract checkable claims, retrieve evidence, and explore what’s supported, contradicted, or unresolved.</p>
                <a className="vc-arrow-link" href={verifyPath}>Explore Paste &amp; Verify <span><ArrowUpRight size={21}/></span></a>
              </motion.div>
            </article>
          </div>
        </section>

        <section className="vc-method" ref={processRef} id="approach" aria-labelledby="vc-method-title">
          <div className="vc-width vc-method-grid">
            <div className="vc-method-sticky">
              <span className="vc-index">BEHIND THE RESULT</span>
              <h2 id="vc-method-title">Trust is a<br/><em>process.</em></h2>
              <p>Not a score. Not a guess. An evidence trail you can follow from first claim to final decision.</p>
              <a href={verifyPath} className="vc-method-link">Try a verification <ArrowUpRight size={20}/></a>
              <div className="vc-method-indicator" aria-hidden="true"><span/><motion.i style={{scaleX: processProgress}}/></div>
            </div>
            <div className="vc-method-steps">
              {pipeline.map((step) => (
                <motion.article key={step.step} {...reveal} className="vc-method-step">
                  <div className="vc-method-step-top"><span>{step.step}</span><span>{step.verb.toUpperCase()}</span></div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                  <small>{step.detail}</small>
                  <div className="vc-method-step-art" aria-hidden="true">
                    {step.step === '01' ? <><div className="vc-method-art-line wide"/><div className="vc-method-art-line"/><div className="vc-method-art-line lit"/><div className="vc-method-art-line short"/></> :
                      step.step === '02' ? <><div className="vc-method-art-node"/><div className="vc-method-art-bridge"/><div className="vc-method-art-node"/><div className="vc-method-art-bridge"/><div className="vc-method-art-node"/></> :
                      <><span><Check size={18}/></span><span><X size={18}/></span><span><CircleHelp size={18}/></span></>}
                  </div>
                </motion.article>
              ))}
            </div>
          </div>
        </section>

        <section className="vc-last" aria-labelledby="vc-last-title">
          <div className="vc-last-shape" aria-hidden="true"><span/><span/><span/></div>
          <div className="vc-width vc-last-inner">
            <motion.div {...reveal}>
              <h2 id="vc-last-title">The future<br/>needs <em>proof.</em></h2>
              <p>Bring a question. Leave with something you can inspect.</p>
              <a href={launchPath} className="vc-last-button">Launch VerifAI <ArrowUpRight size={22}/></a>
            </motion.div>
            <span className="vc-last-caption">DON’T JUST TRUST THE ANSWER.</span>
          </div>
        </section>
      </main>

      <footer className="vc-footer">
        <div className="vc-width vc-footer-content">
          <a href="#top" aria-label="Return to top" className="vc-logo-link"><Logo/></a>
          <p>Evidence first. Uncertainty preserved.</p>
          <div><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href={accountPath}>{isAuthenticated ? 'Dashboard' : 'Sign in'}</a></div>
          <small>© 2026 VerifAI</small>
        </div>
      </footer>
    </div>
  );
}

