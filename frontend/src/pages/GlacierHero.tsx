import { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion, useTransform, type MotionValue } from 'motion/react';
import { ArrowUpRight, Compass, Home, Layers3, ShieldCheck, ArrowDown, Volume2, VolumeX, Github, Network, FileCheck2 } from 'lucide-react';

type HeroProps = { launchPath: string; accountPath: string; chatPath: string; verifyPath: string; descent: MotionValue<number> };
type DockProps = { launchPath: string; accountPath: string };

const ease = [0.19, 1, 0.22, 1] as const;

export function GlacierDock({ launchPath, accountPath }: DockProps) {
  const [active, setActive] = useState(() => window.location.hash || '#top');
  const items = [
    { key:'#top', Icon:Home, label:'Home', href:'#top' },
    { key:'#platform', Icon:Layers3, label:'Platform', href:'#platform' },
    { key:'#pillar', Icon:Compass, label:'The pillar', href:'#pillar' },
  ];
  useEffect(() => {
    let frame = 0;
    const updateActiveSection = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const midpoint = window.innerHeight * .10;
        const activeSection = ['#pillar','#platform','#top'].find(id => {
          const element = document.querySelector(id);
          if (!element) return false;
          const rect = element.getBoundingClientRect();
          return rect.top <= midpoint && rect.bottom >= midpoint;
        }) || '#top';
        setActive(current => current === activeSection ? current : activeSection);
      });
    };
    window.addEventListener('hashchange', updateActiveSection);
    window.addEventListener('scroll', updateActiveSection, { passive:true });
    window.addEventListener('resize', updateActiveSection);
    updateActiveSection();
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('hashchange', updateActiveSection);
      window.removeEventListener('scroll', updateActiveSection);
      window.removeEventListener('resize', updateActiveSection);
    };
  }, []);

  return (
    <div className="vg-navigation">
      <motion.nav className="vg-dock" aria-label="Primary navigation"
        initial={{ opacity:0, y:-15 }} animate={{ opacity:1, y:0 }}
        transition={{ duration:.65, ease }}>
        {items.map(({key,Icon,label,href}) => (
          <a href={href} key={key} aria-label={label} title={label}
            aria-current={active === key ? 'page' : undefined}
            className={'vg-dock-item' + (active === key ? ' is-active' : '')}
            onClick={() => setActive(key)}>
            {active === key && <motion.span layoutId="verifai-glacier-dock-active" className="vg-dock-active"
              transition={{ type:'spring', stiffness:420, damping:36 }} />}
            <Icon size={19} strokeWidth={1.7} aria-hidden="true" />
          </a>
        ))}
      </motion.nav>
      <div className="vg-dock-corner">
        <a className="vg-dock-signin" href={accountPath}>{accountPath === '/login' ? 'Sign in' : 'Dashboard'}</a>
        <a className="vg-dock-launch" href={launchPath}>Launch app <ArrowUpRight size={14}/></a>
      </div>
    </div>
  );
}

export function GlacierHero({ launchPath, accountPath, chatPath, verifyPath, descent }:HeroProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const reducedMotion = useReducedMotion();
  const [muted,setMuted] = useState(true);
  const [hasAudio,setHasAudio] = useState(false);
  const [videoError,setVideoError] = useState(false);
  // Hold a single sky video DOM node throughout the hero AND the descent.
  // Moving the sky upward and magnifying it sells a downward camera movement.
  const skyY = useTransform(descent, [0,.28,.65,1], ['0%', '-2%', '-8%', '-13%']);
  const skyScale = useTransform(descent, [0,.28,.65,1], [1,1.06,1.19,1.30]);
  // Evaluate fade directly against scroll: the browser's native timeline can
  // lag behind the shared pinned video and leave ghosted hero text over water.
  const contentOpacity = useTransform(() => {
    const amount = descent.get();
    if (amount <= .025) return 1;
    if (amount >= .115) return 0;
    const t = (amount - .025) / .09;
    return 1 - t * t * (3 - 2 * t);
  });
  const contentY = useTransform(descent, [0,.25,.6,1], [0,-22,-130,-170]);
  // Warm sunset gently cools as the camera descends toward the ocean.
  // This begins at the actual scroll handoff: the hero stays rich gold initially.
  const skyColorGradeOpacity = useTransform(() => {
    const position = descent.get();
    if(position <= 0) return 0;
    return Math.max(0, Math.min(.8, position * 3.0));
  });


  useEffect(() => {
    const video=videoRef.current;
    if (!video || reducedMotion) return;
    video.muted=muted;
    // Only present sound controls when the browser reports an audio track.
    const audioVideo = video as HTMLVideoElement & { audioTracks?: { length:number } };
    setHasAudio(Boolean(audioVideo.audioTracks?.length));
    const onError = () => setVideoError(true);
    video.addEventListener('error',onError);
    const play=video.play();
    if(play && typeof play.catch === 'function') void play.catch(() => {});
    return () => video.removeEventListener('error',onError);
  },[reducedMotion,muted]);

  return (
    <section id="top" className="vg-hero" aria-labelledby="vg-hero-title">
      <motion.div className="vg-hero-background" style={reducedMotion?undefined:{y:skyY,scale:skyScale}} aria-hidden="true">
        {!reducedMotion && !videoError && <video ref={videoRef} src="/landing/glacier-sky-hero.mp4"
          poster="/landing/glacier-sky-poster.jpg" preload="auto" autoPlay muted={muted} loop playsInline
          disablePictureInPicture />}
      </motion.div>
      <div className="vg-overlay vg-overlay-base" aria-hidden="true"/>
      <div className="vg-overlay vg-overlay-gradient" aria-hidden="true"/>
      <div className="vg-overlay vg-overlay-edges" aria-hidden="true"/>
      <div className="vg-overlay vg-overlay-glow" aria-hidden="true"/>
      <motion.div className="vg-atmosphere-grade"
        style={reducedMotion?undefined:{opacity:skyColorGradeOpacity}}
        aria-hidden="true"/>

      <motion.div className="vg-hero-content-wrap" style={reducedMotion?undefined:{opacity:contentOpacity,y:contentY}}>
        <div className="vg-center">
          <motion.div className="vg-brand" initial={reducedMotion?false:{opacity:0,y:12}} animate={{opacity:1,y:0}}
            transition={{duration:.7,delay:.09,ease}}>
            <span className="vg-brand-rule" aria-hidden="true"/>
            <span className="vg-brand-mark"><ShieldCheck size={22} strokeWidth={1.45} aria-hidden="true"/><span>VERIFAI</span></span>
            <span className="vg-brand-rule" aria-hidden="true"/>
          </motion.div>

          <div className="vg-headline-wrap">
            <svg className="vg-orbit" viewBox="0 0 1100 360" preserveAspectRatio="none" fill="none" aria-hidden="true">
              {/* Reference-matched, deliberately open editorial sweep. The
                  star and path share the same (968, 116) anchor, so resizing
                  never detaches the star from the orbit. */}
              <path className="vg-orbit-arc"
                d="M 755 50 C 865 45 953 71 968 116
                   C 980 156 879 231 682 278
                   C 461 355 206 360 145 287
                   C 102 259 174 189 316 155"
                stroke="currentColor" strokeWidth="1" vectorEffect="non-scaling-stroke"
                strokeLinecap="round" />
              <path className="vg-orbit-star-halo"
                d="M 968 90 C 971 106 976 111 992 116 C 976 121 971 126 968 143 C 964 126 958 121 942 116 C 958 111 964 106 968 90 Z"
                fill="currentColor" />
              <path className="vg-orbit-star"
                d="M 968 97 C 971 109 975 113 987 116 C 975 119 971 123 968 135 C 965 123 961 119 949 116 C 961 113 965 109 968 97 Z"
                fill="currentColor" />
            </svg>
            <motion.h1 id="vg-hero-title" className="vg-title"
              initial={reducedMotion?false:{opacity:0,y:26}} animate={{opacity:1,y:0}}
              transition={{duration:.95,delay:.24,ease}}>
              <span className="vg-title-first">BEYOND</span>
              <span className="vg-title-second">THE ANSWER</span>
            </motion.h1>
          </div>

          <motion.p className="vg-subtitle"
            initial={reducedMotion?false:{opacity:0,y:16}} animate={{opacity:1,y:0}}
            transition={{duration:.85,delay:.39,ease}}>
            <span className="vg-subtitle-main">AI hallucinates. We <em>investigate.</em></span>
            <span className="vg-subtitle-detail">Where every answer meets the evidence.</span>
          </motion.p>

          <motion.a className="vg-enter" href={launchPath}
            initial={reducedMotion?false:{opacity:0,y:18}} animate={{opacity:1,y:0}}
            transition={{duration:.75,delay:.51,ease}}
            whileHover={{scale:1.035}}
            whileTap={{scale:.98}}>
            ENTER VERIFAI <ArrowUpRight size={17} strokeWidth={1.7}/>
          </motion.a>
        </div>

        <motion.div className="vg-editorial-bottom">
          <div className="vg-feature-rail" aria-label="VerifAI features">
            <a href={chatPath}><Network size={20} strokeWidth={1.65} aria-hidden="true"/><span>MULTI-MODEL PERSPECTIVES</span></a>
            <a href={verifyPath}><FileCheck2 size={20} strokeWidth={1.65} aria-hidden="true"/><span>EVIDENCE-FIRST VERIFICATION</span></a>
            <a href="#pillar"><ShieldCheck size={20} strokeWidth={1.65} aria-hidden="true"/><span>UNCERTAINTY PRESERVED</span></a>
          </div>
          <footer className="vg-editorial-footer" aria-label="VerifAI links and copyright">
            <div className="vg-editorial-branding">
              <a className="vg-editorial-wordmark" href="#top">VERIFAI<span>.</span></a>
              <span className="vg-editorial-brand-divider" aria-hidden="true"/>
              <span className="vg-editorial-tagline">AI HALLUCINATES. WE INVESTIGATE.</span>
              <span className="vg-editorial-copyright vg-editorial-copyright-mobile">© {new Date().getFullYear()} VerifAI</span>
            </div>
            <div className="vg-editorial-links">
              <a href="#top">Back to top <ArrowUpRight className="vg-back-top-icon" size={13}/></a>
              <a href={accountPath}>{accountPath === '/login' ? 'Sign in' : 'Dashboard'}</a>
              <a href="/privacy">Privacy</a>
              <a href="/terms">Terms</a>
              <a href="https://github.com/Arunprasath-2717/VerifAI" target="_blank" rel="noopener noreferrer" aria-label="VerifAI GitHub repository"><Github size={18}/></a>
              {hasAudio ? (
                <button type="button" aria-label={muted?'Unmute background video':'Mute background video'} onClick={() => setMuted(v=>!v)}>
                  {muted?<VolumeX size={17}/>:<Volume2 size={17}/>}
                </button>
              ) : null}
              <span className="vg-editorial-copyright vg-editorial-copyright-desktop">© {new Date().getFullYear()} VerifAI</span>
            </div>
          </footer>
          <a href="#platform" className="vg-editorial-scroll" aria-label="Scroll to the ocean"><ArrowDown size={14} strokeWidth={1.5}/></a>
        </motion.div>
      </motion.div>
    </section>
  );
}
