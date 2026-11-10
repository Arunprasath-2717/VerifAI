import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion, useScroll, useSpring, useTransform } from 'motion/react';
import Lenis from 'lenis';
import {
  ArrowUpRight, Check, CheckCircle2, CircleHelp, SearchCheck, XCircle, Menu, X,
} from 'lucide-react';
import { BenefitsSection } from '../components/landing/BenefitsSection';
import { ScrollFloat } from '../components/landing/ScrollFloat';
import { ScrollReveal } from '../components/landing/ScrollReveal';
import './LandingPage.css';
import './LandingDisplay.css';
import './LandingEditorial.css';
import './LandingBenefits.css';
import './LandingPalette.css';
import './LandingClean.css';
import './LandingReimagined.css';
import './LandingStickyNav.css';
import './LandingLight.css';
import './LandingAfterDark.css';
import './LandingMonochromeHero.css';
import './LandingSectionFlow.css';
import './LandingMidnight.css';
import './LandingInk.css';
import './LandingOrbEditorial.css';
import './LandingPaper.css';
import './LandingCreamContrast.css';
import './LandingNavGlass.css';
import './LandingForestSilver.css';
import './LandingLiquidMotion.css';
import './LandingFullWidth.css';
import './LandingLiquidFill.css';
import './LandingReferenceLiquid.css';

interface LandingPageProps { isAuthenticated: boolean }

const cases = [
  {
    label: 'A familiar myth', domain: 'Observation',
    claim: 'The Great Wall of China is visible from the Moon with the naked eye.',
    verdict: 'Contradicted', kind: 'contradicted',
    note: 'Its narrow width and low contrast make the wall impossible to distinguish with the unaided eye from lunar distance.',
    insight: 'A statement can be familiar without being factual.', icon: XCircle,
  },
  {
    label: 'An established fact', domain: 'Astronomy',
    claim: 'Earth completes an orbit around the Sun in approximately one year.',
    verdict: 'Supported', kind: 'supported',
    note: 'Independent astronomical observations establish Earth’s orbital period at roughly one year.',
    insight: 'Strong conclusions follow repeated, independent observations.', icon: CheckCircle2,
  },
  {
    label: 'An absolute prediction', domain: 'AI systems',
    claim: 'Future AI models will never make a factual error.',
    verdict: 'Unresolved', kind: 'unresolved',
    note: 'An absolute statement about unknown future systems cannot be established by evidence available today.',
    insight: '“Not established” is often the most useful answer.', icon: CircleHelp,
  },
] as const;

const principles = [
  { title: 'Isolate the claim.', detail: 'Pull apart a polished answer until each factual assertion can stand on its own.' },
  { title: 'Trace the evidence.', detail: 'Follow the reasoning back to independent material that actually addresses the claim.' },
  { title: 'Keep uncertainty visible.', detail: 'Show what is supported, contradicted, or still impossible to conclude.' },
] as const;

const voices = [
  { letter: 'A', line: 'Lightning never strikes the same place twice.' },
  { letter: 'B', line: 'A location cannot receive a second lightning strike.' },
  { letter: 'C', line: 'Lightning always chooses a different point.' },
] as const;

function StickyLandingNav({ isAuthenticated }: LandingPageProps) {
  const [scrolled, setScrolled] = useState(false);
  const [overHero, setOverHero] = useState(true);
  const [active, setActive] = useState('#top');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [hovered, setHovered] = useState<string | null>(null);
  const reducedMotion = useReducedMotion();
  const highlighted = hovered ?? active;
  const launch = isAuthenticated ? '/dashboard' : '/login';
  const items = [
    { text: 'Home', href: '#top' },
    { text: 'Difference', href: '#difference' },
    { text: 'Key Benefits', href: '#benefits' },
    { text: 'Consensus', href: '#consensus' },
    { text: 'Approach', href: '#approach' },
  ];
  useEffect(() => {
    const update = () => {
      setScrolled(window.scrollY > 38);
      const hero = document.querySelector('#top');
      setOverHero(Boolean(hero && hero.getBoundingClientRect().bottom > 118));
      let current = '#top';
      for (const id of ['#difference', '#benefits', '#consensus', '#approach', '#footer']) {
        const el = document.querySelector(id);
        if (el && el.getBoundingClientRect().top < window.innerHeight * .42) current = id;
      }
      setActive(current === '#footer' ? '#approach' : current);
    };
    const dismiss = (event: KeyboardEvent) => { if (event.key === 'Escape') setMobileOpen(false); };
    const resize = () => { if (window.innerWidth > 720) setMobileOpen(false); };
    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('keydown', dismiss);
    window.addEventListener('resize', resize, { passive: true });
    return () => {
      window.removeEventListener('scroll', update);
      window.removeEventListener('keydown', dismiss);
      window.removeEventListener('resize', resize);
    };
  }, []);
  return (
    <header className={'vrs-nav' + (scrolled ? ' vrs-nav--scrolled' : '') + (mobileOpen ? ' vrs-nav--open' : '') + (overHero ? ' vrs-nav--over-hero' : '')}>
      <div className="vrs-nav__inner">
        <a className="vrs-nav__logo" href="#top" aria-label="VerifAI home" onClick={() => setMobileOpen(false)}>
          <img src="/brand/owl-mark.svg" width="52" height="52" alt=""/>
        </a>
        <nav
          className="vrs-nav__links"
          aria-label="Primary navigation"
          onPointerMove={event => {
            if (event.pointerType !== 'mouse') return;
            const rect = event.currentTarget.getBoundingClientRect();
            const glint = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100));
            event.currentTarget.style.setProperty('--vrs-liquid-glint', `${glint.toFixed(1)}%`);
          }}
          onPointerLeave={event => event.currentTarget.style.removeProperty('--vrs-liquid-glint')}
        >
          <span className="vrs-nav__liquid-bath" aria-hidden="true">
            <span className="vrs-nav__liquid-wave" />
          </span>
          {items.map(item => (
            <a
              href={item.href}
              className={[active === item.href ? 'active' : '', highlighted === item.href ? 'is-lit' : ''].filter(Boolean).join(' ')}
              aria-current={active === item.href ? 'page' : undefined}
              key={item.href}
              onPointerEnter={event => { if (event.pointerType === 'mouse') setHovered(item.href); }}
              onPointerLeave={() => setHovered(null)}
              onFocus={() => setHovered(item.href)}
              onBlur={() => setHovered(null)}
            >
              {highlighted === item.href && (
                <motion.span
                  className="vrs-nav__liquid-lens"
                  layoutId={reducedMotion ? undefined : 'vrs-nav-active-lens'}
                  transition={reducedMotion ? { duration: 0 } : { type: 'spring', stiffness: 420, damping: 32, mass: .55 }}
                  aria-hidden="true"
                />
              )}
              <span className="vrs-nav__label">{item.text}</span>
            </a>
          ))}
        </nav>
        <a className="vrs-nav__sign-in" href={launch}>{isAuthenticated ? 'Workspace' : 'Sign in'}</a>
        <button className="vrs-nav__burger" type="button" aria-label={mobileOpen ? 'Close menu' : 'Open menu'} aria-expanded={mobileOpen} aria-controls="vrs-mobile-navigation" onClick={() => setMobileOpen(open => !open)}>
          {mobileOpen ? <X size={21} strokeWidth={1.8}/> : <Menu size={21} strokeWidth={1.8}/>}
        </button>
      </div>
      {mobileOpen && <>
        <button aria-label="Close navigation" type="button" className="vrs-nav__scrim" onClick={() => setMobileOpen(false)}/>
        <nav id="vrs-mobile-navigation" className="vrs-nav__mobile" aria-label="Mobile navigation">
          {items.map(item => <a href={item.href} key={item.href} onClick={() => setMobileOpen(false)}>{item.text}<ArrowUpRight size={17}/></a>)}
          <a href={launch} onClick={() => setMobileOpen(false)} className="vrs-nav__mobile-action">{isAuthenticated ? 'Workspace' : 'Sign in'}<ArrowUpRight size={17}/></a>
        </nav>
      </>}
    </header>
  );
}

/** The hero is a complete framework-free HTML/CSS/JS document.
 * Its links open the parent app; the rest of VerifAI remains React. */
function Hero() {
  const heroRef = useRef<HTMLElement>(null);
  const reducedMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] });
  const smoothExit = useSpring(scrollYProgress, { stiffness: 120, damping: 30, mass: .45 });
  const veilOpacity = useTransform(smoothExit, [0, .12, .35, .58, 1], [0, .42, .90, 1, 1]);
  return (
    <section ref={heroRef} className="vr-hero-static" id="top" aria-label="VerifAI — Evidence Before Confidence">
      <iframe
        className="vr-hero-static__frame"
        title="VerifAI — Evidence Before Confidence"
        src="/hero-static/index.html?embedded=1"
        loading="eager"
        allow="autoplay"
      />
      {!reducedMotion && (
        <motion.div className="vr-hero-static__scroll-veil" style={{ opacity: veilOpacity }} aria-hidden="true"/>
      )}
    </section>
  );
}

function Difference() {
  const [index, setIndex] = useState(0);
  const reduced = useReducedMotion();
  const item = cases[index];
  const VerdictIcon = item.icon;
  return (
    <section className="vr-difference vr-section" id="difference" aria-labelledby="vr-difference-heading">
      <div className="vr-container">
        <div className="vr-section__heading vr-difference__heading">
          <motion.div initial={reduced ? false : { opacity: 0, y: 35 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .22 }} transition={{ duration: .8 }}>
            <h2 id="vr-difference-heading"><ScrollFloat>A claim is not</ScrollFloat> <em>a conclusion.</em></h2>
          </motion.div>
          <p>Look beyond how an answer sounds. The difference is knowing what can actually be demonstrated.</p>
        </div>
        <div className="vr-forensic" onPointerMove={event => {
          const rect = event.currentTarget.getBoundingClientRect();
          event.currentTarget.style.setProperty('--pointer-x', `${event.clientX - rect.left}px`);
          event.currentTarget.style.setProperty('--pointer-y', `${event.clientY - rect.top}px`);
        }}>
          <div className="vr-forensic__index" role="group" aria-label="Choose an example claim">
            {cases.map((choice, i) => <button key={choice.label} type="button" aria-pressed={i === index} className={i === index ? 'selected' : ''} onClick={() => setIndex(i)}>
              <span>{choice.label}</span><ArrowUpRight size={19}/>
            </button>)}
          </div>
          <div className="vr-forensic__reading">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div key={index} initial={reduced ? false : { opacity: 0, y: 23, filter: 'blur(5px)' }} animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }} exit={reduced ? undefined : { opacity: 0, y: -17 }} transition={{ duration: .3 }}>
                <blockquote>“{item.claim}”</blockquote>
                <div className="vr-forensic__verdict" role="status"><VerdictIcon size={26} strokeWidth={1.5}/><strong>{item.verdict}</strong></div>
                <p>{item.note}</p>
                <p className="vr-forensic__insight">{item.insight}</p>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
        <p className="vr-disclaimer">Illustrative examples, not live verification results.</p>
      </div>
    </section>
  );
}

function Consensus() {
  const [showEvidence, setShowEvidence] = useState(false);
  const reduced = useReducedMotion();
  return (
    <section className="vr-consensus vr-section" id="consensus" aria-labelledby="vr-consensus-heading">
      <div className="vr-container">
        <div className="vr-section__heading vr-consensus__heading">
          <motion.h2 id="vr-consensus-heading" initial={reduced ? false : { opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: .75 }}>
            AGREEMENT <em>ISN'T PROOF.</em>
          </motion.h2>
          <p><ScrollReveal>Three models can repeat the same mistake. An independent source matters more than an agreement count.</ScrollReveal></p>
        </div>
        <div className="vr-consensus__lines" aria-label="Three hypothetical model answers">
          {voices.map((voice, i) => <motion.div key={voice.letter} className="vr-consensus__voice" initial={reduced ? false : { opacity: 0, x: i % 2 ? 24 : -24 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: .63, delay: i * .08 }}>
            <span>MODEL {voice.letter}</span>
            <blockquote>“{voice.line}”</blockquote>
            <Check size={22} strokeWidth={1.4} aria-label="Agrees with the other examples" />
          </motion.div>)}
        </div>
        <div className="vr-consensus__decision">
          <div><strong>3 / 3 agree.</strong><p>That doesn't make it true.</p></div>
          <button type="button" className="vr-button vr-button--outline" aria-expanded={showEvidence} aria-controls="vr-consensus-evidence" onClick={() => setShowEvidence(value => !value)}>
            {showEvidence ? 'Hide evidence' : 'Reveal the evidence'} <ArrowUpRight size={18}/>
          </button>
        </div>
        <AnimatePresence initial={false}>
          {showEvidence && <motion.div id="vr-consensus-evidence" className="vr-consensus__evidence" role="region" aria-label="Evidence explanation"
            initial={reduced ? false : { opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={reduced ? undefined : { opacity: 0, height: 0 }} transition={{ duration: .45 }}>
            <div className="vr-consensus__evidence-inner"><XCircle size={32} strokeWidth={1.5}/><div><strong>The shared claim is false.</strong><p>Lightning can strike the same place many times. The three responses above are deliberately hypothetical and wrong.</p></div></div>
          </motion.div>}
        </AnimatePresence>
        <p className="vr-disclaimer">A demonstration using hypothetical responses—not output from live models.</p>
      </div>
    </section>
  );
}

function Approach() {
  const reduced = useReducedMotion();
  return <section className="vr-approach vr-section" id="approach" aria-labelledby="vr-approach-heading">
    <div className="vr-container">
      <div className="vr-section__heading vr-approach__heading">
        <h2 id="vr-approach-heading">A BETTER <em>WAY TO KNOW.</em></h2>
        <p>The best answer should show how it reached its conclusion.</p>
      </div>
      <div className="vr-approach__layout">
        <div className="vr-approach__steps">
          {principles.map((item, i) => <motion.article key={item.title} initial={reduced ? false : { opacity: 0, y: 25 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .25 }} transition={{ duration: .6, delay: i * .09 }}>
            <span aria-hidden="true">0{i + 1}</span><div><h3>{item.title}</h3><p>{item.detail}</p></div><ArrowUpRight size={22} strokeWidth={1.4} aria-hidden="true"/>
          </motion.article>)}
        </div>
        <motion.aside className="vr-approach__statement" initial={reduced ? false : { opacity: 0, x: 28 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, amount: .2 }} transition={{ duration: .7 }}>
          <SearchCheck size={41} strokeWidth={1.2} aria-hidden="true" />
          <p>Trust is not the absence of questions. <em>It's knowing where to look.</em></p>
          <span className="vr-approach__rule" aria-hidden="true"/>
        </motion.aside>
      </div>
    </div>
  </section>;
}

function Footer({ isAuthenticated }: LandingPageProps) {
  const launchPath = isAuthenticated ? '/dashboard' : '/login';
  return (
    <footer className="vr-finale" id="footer" aria-label="VerifAI footer">
      <div className="vr-finale__atmosphere" aria-hidden="true" />
      <div className="vr-finale__grain" aria-hidden="true" />

      <div className="vr-finale__inner">
        <div className="vr-finale__lead">
          <div className="vr-finale__lead-title">
            <p className="vr-finale__overline">
              <span className="vr-finale__light" aria-hidden="true" />
              FROM QUESTION TO CLARITY
            </p>
            <h2>Know more.<br/><em>Assume less.</em></h2>
          </div>
          <div className="vr-finale__lead-action">
            <p>Don't stop at a convincing answer. Find the claim, follow the evidence, and know what remains uncertain.</p>
            <a className="vr-finale__cta" href={launchPath}>
              <span>{isAuthenticated ? 'Open your workspace' : 'Start verifying'}</span>
              <ArrowUpRight size={21} strokeWidth={1.8} aria-hidden="true"/>
            </a>
          </div>
        </div>

        <div className="vr-finale__directory">
          <div className="vr-finale__identity">
            <a className="vr-finale__logo" href="#top" aria-label="VerifAI home">
              <span className="vr-finale__logo-mark"><img src="/brand/owl-mark.svg" width="33" height="33" alt=""/></span>
              <span>Verif<span>AI</span></span>
            </a>
            <p>Independent thinking deserves<br/>visible evidence.</p>
          </div>

          <nav className="vr-finale__column" aria-label="Explore the website">
            <h3>Explore</h3>
            <a href="#difference">The Difference</a>
            <a href="#benefits">Key Benefits</a>
            <a href="#consensus">Why Consensus Matters</a>
            <a href="#approach">Our Approach</a>
          </nav>
          <nav className="vr-finale__column" aria-label="Platform">
            <h3>Platform</h3>
            <a href={launchPath}>{isAuthenticated ? 'Workspace' : 'Get Started'}</a>
            {!isAuthenticated && <a href="/login">Sign in</a>}
            <a href="#difference">Claim verification</a>
            <a href="#consensus">Model comparison</a>
          </nav>
          <nav className="vr-finale__column" aria-label="Information">
            <h3>Information</h3>
            <a href="#approach">How it works</a>
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms of use</a>
            <a href="#top">Back to top</a>
          </nav>
        </div>

        <div className="vr-finale__signature" aria-label="VerifAI">
          VERIF<span>AI</span>
        </div>

        <div className="vr-finale__closing">
          <span>© {new Date().getFullYear()} VerifAI. All rights reserved.</span>
          <span className="vr-finale__motto"><span aria-hidden="true" /> Evidence before confidence.</span>
          <a href="#top">Return to top <ArrowUpRight size={16} aria-hidden="true"/></a>
        </div>
      </div>
    </footer>
  );
}

export function LandingPage({ isAuthenticated }: LandingPageProps) {
  const reduced = useReducedMotion();
  useEffect(() => {
    const title = document.title;
    document.title = 'VerifAI — Evidence Before Confidence';
    return () => { document.title = title; };
  }, []);
  useEffect(() => {
    const lenis = reduced ? null : new Lenis({
      autoRaf: true,
      smoothWheel: true,
      lerp: .095,
      wheelMultiplier: .95,
      anchors: { offset: -92 },
    });
    const relay = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.source !== document.querySelector<HTMLIFrameElement>('.vr-hero-static__frame')?.contentWindow) return;
      if (event.data?.type !== 'verifai:hero-scroll') return;
      const delta = Number(event.data.delta);
      if (!Number.isFinite(delta) || !delta) return;
      const bounded = Math.max(-400, Math.min(400, delta));
      if (lenis) lenis.scrollTo(lenis.targetScroll + bounded, { lerp: .095 });
      else window.scrollBy({ top: bounded, behavior: 'instant' });
    };
    window.addEventListener('message', relay);
    return () => { window.removeEventListener('message', relay); lenis?.destroy(); };
  }, [reduced]);
  return (
    <div className="verifai-landing vr-root">
      <StickyLandingNav isAuthenticated={isAuthenticated}/>
      <main>
        <Hero />
        <Difference />
        <BenefitsSection />
        <Consensus />
        <Approach />
      </main>
      <Footer isAuthenticated={isAuthenticated} />
    </div>
  );
}
