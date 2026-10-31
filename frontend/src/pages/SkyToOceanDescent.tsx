import { type Ref } from 'react';
import { motion, useTransform, type MotionValue } from 'motion/react';
import { ArrowDown, ArrowUpRight, ShieldCheck, Sparkles, Mail, Github } from 'lucide-react';
import { CinematicScrollBackdrop } from './CinematicScrollBackdrop';

interface SkyToOceanDescentProps {
  platformRef: Ref<HTMLElement>;
  pillarRef: Ref<HTMLElement>;
  progress: MotionValue<number>;
  pillarProgress: MotionValue<number>;
  reducedMotion: boolean;
  launchPath: string;
  verifyPath: string;
}

/** Piecewise opacity calculated in JS to avoid native scroll-timeline drift. */
function scrollFade(value: number, stops: number[], values: number[]) {
  if (value <= stops[0]) return values[0];
  for (let i=1;i<stops.length;i++) {
    if (value <= stops[i]) {
      const t=(value-stops[i-1])/(stops[i]-stops[i-1]);
      return values[i-1]+t*(values[i]-values[i-1]);
    }
  }
  return values[values.length-1];
}

/**
 * The SECOND section reveals the platform after a downward cloud descent.
 * The THIRD section continues the already-moving pillar from the SAME film layer.
 * Both use one sticky camera viewport, so there is no repeated platform or cut.
 */
export function SkyToOceanDescent({
  platformRef, pillarRef, progress, pillarProgress, reducedMotion, launchPath, verifyPath,
}: SkyToOceanDescentProps) {
    const oceanOpacity = useTransform(() => scrollFade(progress.get(),[0,.06,.20,.43,1],[0,0,.68,1,1]));
    const oceanScale = useTransform(() => scrollFade(progress.get(),[0,.14,.43,.68,1],[1.13,1.11,1.025,1,1]));
    // Motion in the original footage starts around 2 seconds. Scrub the
    // nearly-still opening frames during the END of Section 2, so the
    // pillar begins rising at the exact Section 2 -> Section 3 handoff.
    // One continuous MotionValue drives the same video in both sections.
    const filmProgress = useTransform(() => {
      const platform = progress.get();
      const pillar = pillarProgress.get();
      const preRoll = 0.20; // ~2 seconds into the 10-second original video
      if (pillar > 0) return preRoll + pillar * (1 - preRoll);
      const overlap = Math.max(0, Math.min(1, (platform - 0.73) / 0.27));
      return overlap * preRoll;
    });
    // Reveal the film over the identical still before the preroll starts.
    const videoOpacity = useTransform(() => scrollFade(progress.get(),[0,.61,.75,1],[0,0,1,1]));
    // Crossfade video into the identical still before preroll; no visual pop.
    const farOpacity = useTransform(() => scrollFade(progress.get(),[0,.05,.16,.30,.48,.57,1],[0,0,.42,.33,.08,0,0]));
    const midOpacity = useTransform(() => scrollFade(progress.get(),[0,.07,.18,.32,.47,.57,1],[0,0,.46,.36,.08,0,0]));
    const nearOpacity = useTransform(() => scrollFade(progress.get(),[0,.10,.22,.32,.47,.57,1],[0,0,.47,.31,.07,0,0]));
    const hazeOpacity = useTransform(() => scrollFade(progress.get(),[0,.03,.16,.29,.44,.55,1],[0,0,.14,.21,.05,0,0]));
    const farY = useTransform(progress, [0,.22,.70,1], ['23%','16%','-30%','-55%']);
    const midY = useTransform(progress, [0,.25,.70,1], ['58%','34%','-44%','-89%']);
    const nearY = useTransform(progress, [0,.34,.72,1], ['85%','47%','-58%','-132%']);
    const farScale = useTransform(progress, [0,1], [1,1.38]);
    const nearScale = useTransform(progress, [0,1], [1,1.65]);
    // Restore the natural ocean contrast as atmospheric effects clear.
    const oceanGradeOpacity = useTransform(() => scrollFade(progress.get(),[0,.34,.65,1],[0,0,1,1]));
    const cueOpacity = useTransform(() => scrollFade(progress.get(),[0,.07,.16,.27,.42,1],[0,.8,.9,.28,0,0]));
    const cueY = useTransform(progress, [0,.55], [34,-75]);
    // An atmospheric veil bridges warm sunset lighting and cooler sea tones.
    const colorBridgeOpacity = useTransform(() => scrollFade(progress.get(),[0,.04,.18,.34,.48,.56,1],[0,.06,.23,.11,.02,0,0]));
    // Match the amber hero's final cloud bank to a dusk-blue horizon,
    // then remove all color treatment once the platform is revealed.
    const atmosphereGradeOpacity = useTransform(() =>
      scrollFade(progress.get(), [0,.06,.19,.31,.42,.51,1],
        [.31,.55,.67,.40,.14,0,0]));
    const sunsetHaloOpacity = useTransform(() =>
      scrollFade(progress.get(), [0,.08,.18,.29,.41,.5,1],
        [.45,.57,.48,.22,.06,0,0]));
    // Show the platform copy during the reveal; fade it as the film's
    // first movement begins, without a blank stationary scroll interval.
    const platformHeadlineOpacity = useTransform(() => scrollFade(progress.get(),[0,.23,.39,.52,.74,1],[0,0,.64,1,1,0]));
    const platformHeadlineY = useTransform(() => scrollFade(progress.get(),[0,.45,1],[34,0,0]));
    const platformTopOpacity = useTransform(() => scrollFade(progress.get(),[0,.3,.5,.82,1],[0,0,1,1,0]));
    // Section 3 content enters while the pillar rises, not afterwards.
    const pillarHeadlineOpacity = useTransform(() => scrollFade(pillarProgress.get(),[0,.055,.23,.41,1],[0,.13,.77,1,1]));
    const pillarHeadlineY = useTransform(pillarProgress,[0,.40],[32,0]);
    const pillarChromeOpacity = useTransform(() => scrollFade(pillarProgress.get(),[0,.015,.07,.14],[0,0,.65,1]));
    const pillarPanelPointerEvents = useTransform(() => pillarProgress.get() > .15 ? 'auto' : 'none');
    // The footer is a glass overlay at the very END of Section 3, not a
    // separate section. The final encoded pillar frame remains visible.
    const pillarBottomOpacity = useTransform(() =>
      scrollFade(pillarProgress.get(),[0,.015,.07,.14,.91,.95],[0,0,.65,1,1,0]));
    const endFooterOpacity = useTransform(() =>
      scrollFade(pillarProgress.get(),[0,.91,.96,1],[0,0,.7,1]));
    const endFooterVisibility = useTransform(() => pillarProgress.get() > .91 ? 'visible' : 'hidden');
    const contactEmail = (import.meta.env.VITE_CONTACT_EMAIL || '').trim();
    const contactHref = contactEmail
      ? `mailto:${contactEmail}`
      : 'https://github.com/Arunprasath-2717/VerifAI/issues/new';


    return <div className="va-film-journey">
      <div className="va-descent-sticky">
        <motion.div className="va-descent-ocean"
          style={reducedMotion?undefined:{opacity:oceanOpacity,scale:oceanScale}}>
          <img src="/landing/evidence-ocean-first-frame.jpg" alt="" draggable={false}/>
          <motion.div className="va-descent-film"
            style={reducedMotion?{display:'none'}:{opacity:videoOpacity}}>
            <CinematicScrollBackdrop progress={filmProgress} reducedMotion={reducedMotion}/>
          </motion.div>
          <motion.div className="va-descent-ocean-grade" style={{opacity:oceanGradeOpacity}}/>
        </motion.div>
        {!reducedMotion && <div aria-hidden="true">
          <motion.div className="va-atmosphere-grade" style={{opacity:atmosphereGradeOpacity}}/>
          <motion.div className="va-atmosphere-sunset" style={{opacity:sunsetHaloOpacity}}/>
          <motion.div className="va-descent-bridge" style={{opacity:colorBridgeOpacity}}/>
          <motion.div className="va-descent-cloud va-descent-cloud-far"
            style={{opacity:farOpacity,y:farY,scale:farScale}}/>
          <motion.div className="va-descent-cloud va-descent-cloud-mid"
            style={{opacity:midOpacity,y:midY}}/>
          <motion.div className="va-descent-cloud va-descent-cloud-near"
            style={{opacity:nearOpacity,y:nearY,scale:nearScale}}/>
          <motion.div className="va-descent-haze" style={{opacity:hazeOpacity}}/>
          <motion.div className="va-descent-cue" style={{opacity:cueOpacity,y:cueY}}>
            <span>BEYOND THE CLOUDS</span>
            <ArrowDown size={24} strokeWidth={1}/>
          </motion.div>
        </div>}
        <motion.div className="va-platform-reveal-overlay"
          style={reducedMotion?undefined:{opacity:platformHeadlineOpacity,y:platformHeadlineY}}>
          <div className="va-platform-copy">
            <span>LOOK BENEATH THE SURFACE</span>
            <h2 id="va-platform-reveal-title">Where the<br/><em>evidence begins.</em></h2>
            <p>The platform is revealed. Keep scrolling to see what rises from it.</p>
            <span className="va-platform-down">DESCEND TO THE PILLAR <ArrowDown size={17}/></span>
          </div>
          <motion.span className="va-platform-reveal-counter"
            style={reducedMotion?undefined:{opacity:platformTopOpacity}}>02 / 03</motion.span>
        </motion.div>
        <div className="va-pillar-content">
          <motion.div className="va-pillar-topline" style={reducedMotion?undefined:{opacity:pillarChromeOpacity}}>
            <span><i/> 03 / THE PILLAR</span><span>FROM ANSWERS TO EVIDENCE</span>
          </motion.div>
          <motion.div className="va-pillar-panel"
            style={reducedMotion?undefined:{opacity:pillarHeadlineOpacity,y:pillarHeadlineY,pointerEvents:pillarPanelPointerEvents}}>
            <span className="va-pillar-kicker"><Sparkles size={15}/> VERIFICATION INTELLIGENCE</span>
            <h2 id="va-pillar-title">A HIGHER<br/><em>STANDARD</em><br/>OF TRUST.</h2>
            <p>Compare AI perspectives. Trace claims to evidence. Keep uncertainty visible.</p>
            <div className="va-pillar-buttons">
              <a className="va-pillar-launch" href={launchPath}>Launch VerifAI <ArrowUpRight size={21}/></a>
              <a className="va-pillar-secondary" href={verifyPath}>Explore verification <ArrowUpRight size={16}/></a>
            </div>
          </motion.div>
          <motion.div className="va-pillar-bottomline" style={reducedMotion?undefined:{opacity:pillarBottomOpacity}}><span><ShieldCheck size={16}/> EVIDENCE FIRST</span><span>03 / 03</span></motion.div>
          <motion.footer
            className="va-end-footer"
            aria-label="VerifAI copyright and contact"
            style={reducedMotion ? undefined : {opacity:endFooterOpacity,visibility:endFooterVisibility}}
          >
            <div className="va-end-footer-brand">
              <strong>VERIF<span>AI</span>.</strong>
              <small>© {new Date().getFullYear()} VerifAI. All rights reserved.</small>
            </div>
            <div className="va-end-footer-links">
              <span className="va-end-footer-tagline">AI HALLUCINATES. WE INVESTIGATE.</span>
              <a href={contactHref} className="va-end-footer-contact"
                target={contactEmail ? undefined : '_blank'}
                rel={contactEmail ? undefined : 'noopener noreferrer'}>
                <Mail size={16} aria-hidden="true"/>
                {contactEmail || 'Contact via GitHub'}
                <ArrowUpRight size={14} aria-hidden="true"/>
              </a>
              <a href="https://github.com/Arunprasath-2717/VerifAI"
                className="va-end-footer-github" target="_blank" rel="noopener noreferrer"
                aria-label="VerifAI on GitHub"><Github size={18}/></a>
            </div>
          </motion.footer>
        </div>
      </div>

      {/* SECTION 2: Sky descent ends on the ORIGINAL platform opening frame. */}
      <section id="platform" ref={platformRef} className="va-platform-reveal va-film-scene"
        aria-labelledby="va-platform-reveal-title">
        <div className="va-platform-scrollspace" aria-hidden="true"/>
      </section>

      {/* SECTION 3: The SAME video transforms the platform into a pillar. */}
      <section id="pillar" ref={pillarRef} className="va-pillar-sequence va-film-scene"
        aria-labelledby="va-pillar-title">
        <div className="va-pillar-scrollspace" aria-hidden="true"/>
      </section>
    </div>;
}
