import { useEffect, useRef } from 'react';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';
import { motion, useReducedMotion, useScroll } from 'motion/react';
import { GlacierHero, GlacierDock } from './GlacierHero';
import { SkyToOceanDescent } from './SkyToOceanDescent';
import './LandingPage.css';

interface LandingPageProps { isAuthenticated: boolean }

export function LandingPage({ isAuthenticated }: LandingPageProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const platformRef = useRef<HTMLElement>(null);
  const pillarRef = useRef<HTMLElement>(null);
  const reducedMotion = useReducedMotion();

  const launchPath = isAuthenticated ? '/dashboard' : '/login';
  const accountPath = isAuthenticated ? '/dashboard' : '/login';
  const chatPath = isAuthenticated ? '/chat' : '/login';
  const verifyPath = isAuthenticated ? '/verify' : '/login';

  const { scrollYProgress: pageProgress } = useScroll();
  // Use the ACTUAL section boundary, not 'end end' (one viewport early).
  // That premature endpoint caused the motionless gap seen in the screencast.
  const { scrollYProgress: descentProgress } = useScroll({
    target: platformRef,
    offset: ['start start', 'end start'],
  });
  // Finish the pillar video at the bottom of the landing page.
  // Without a fourth section, 'end end' lands on the video's final frame
  // at the last possible scroll position.
  const { scrollYProgress: pillarProgress } = useScroll({
    target: pillarRef,
    offset: ['start start', 'end end'],
  });

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const previousTitle = document.title;
    document.title = 'VerifAI — Beyond the Answer';
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const finePointer = window.matchMedia('(pointer:fine)').matches;
    const lenis = finePointer && !reduced.matches
      ? new Lenis({ autoRaf:true, lerp:0.075, smoothWheel:true, anchors:{ offset:-55 }, respectReducedMotion:true })
      : null;
    const clickAnchor = (event:MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest<HTMLAnchorElement>('a[href^="#"]');
      if (!anchor || !root.contains(anchor)) return;
      const href = anchor.getAttribute('href');
      if (!href || href === '#') return;
      const destination = document.getElementById(href.slice(1));
      if (!destination) return;
      event.preventDefault();
      if (lenis && !reduced.matches) lenis.scrollTo(destination, { offset:0, duration:1.3 });
      else destination.scrollIntoView({ behavior:reduced.matches ? 'instant' : 'smooth', block:'start' });
      history.replaceState(null, '', href);
    };
    root.addEventListener('click', clickAnchor);
    return () => {
      document.title = previousTitle;
      lenis?.destroy();
      root.removeEventListener('click', clickAnchor);
    };
  }, []);

  return <div className="verifai-landing va-page va-four-section-page" ref={rootRef}>
    <a className="va-skip" href="#main-content">Skip to content</a>
    <motion.div className="va-scrollbar" style={{ scaleX: pageProgress }} aria-hidden="true" />
    <GlacierDock launchPath={launchPath} accountPath={accountPath} />

    <main id="main-content">
      <div className="va-sky-journey">
        {/* SECTION 1: Birds flying above the clouds. */}
        <GlacierHero
          launchPath={launchPath}
          accountPath={accountPath}
          chatPath={chatPath}
          verifyPath={verifyPath}
          descent={descentProgress}
        />
        <div className="va-sky-hero-hold" aria-hidden="true" />

        {/* SECTIONS 2 + 3 share one sticky cinematic stage and one ocean video. */}
        <SkyToOceanDescent
          platformRef={platformRef}
          pillarRef={pillarRef}
          progress={descentProgress}
          pillarProgress={pillarProgress}
          reducedMotion={!!reducedMotion}
          launchPath={launchPath}
          verifyPath={verifyPath}
        />
      </div>

    </main>
  </div>;
}
