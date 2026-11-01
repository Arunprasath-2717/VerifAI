import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion, useScroll, useTransform } from 'motion/react';
import { ArrowDown, ArrowRight, ArrowUpRight, Braces, Check, ChevronDown, CircleCheck, Fingerprint, GitBranch, Menu, ScanSearch, ShieldCheck, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import './LandingPage.css';

type Props = { isAuthenticated: boolean };
const ease = [0.22, 1, 0.36, 1] as const;
const methods = [
 { icon: Braces, title:'Multiple perspectives', copy:'Compare AI responses side by side before settling on a direction.' },
 { icon: ScanSearch, title:'Claim-by-claim review', copy:'Investigate statements and examine the context supporting them.' },
 { icon: Fingerprint, title:'Evidence-aware synthesis', copy:'See agreement, disagreement, and uncertainty together.' },
];
const risks = [
 {title:'Convincing hallucinations',detail:'Fluent answers can still make unsupported claims.'},
 {title:'Conflicting model outputs',detail:'Different systems may offer incompatible conclusions.'},
 {title:'Missing source context',detail:'A confident summary can obscure where its evidence came from.'},
 {title:'Uncertain conclusions',detail:'The limits of a response deserve to remain visible.'},
];
const solutions = [
 {title:'Compare perspectives',detail:'Review different model responses in a single workspace.',href:'/chat',icon:GitBranch},
 {title:'Inspect the claim',detail:'Look for supporting or conflicting evidence before relying on an answer.',href:'/verify',icon:ScanSearch},
 {title:'Preserve uncertainty',detail:'Synthesize what models agree on, and make unresolved points apparent.',href:'/chat',icon:ShieldCheck},
];

function EnterLink({isAuthenticated,children,className=''}:{isAuthenticated:boolean;children:string;className?:string}){
 return <a className={'rv-enter '+className} href={isAuthenticated?'/dashboard':'/login'}>{children}<ArrowUpRight size={15} aria-hidden="true"/></a>
}
function Header({isAuthenticated}:{isAuthenticated:boolean}){
 const[open,setOpen]=useState(false);
 useEffect(()=>{if(!open)return;const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape')setOpen(false)};window.addEventListener('keydown',onKey);return()=>window.removeEventListener('keydown',onKey)},[open]);
 return <header className="rv-header">
   <a href="#top" className="rv-wordmark" aria-label="VerifAI home"><span className="rv-wordmark-glyph">V</span>VERIF<span>AI</span><b>®</b></a>
   <nav className="rv-header-nav" aria-label="Main navigation">
     <a href="#technology">Technology</a><a href="#challenges">Why VerifAI</a><a href="#solutions">Solutions</a>
   </nav>
   <div className="rv-header-right"><a className="rv-header-signin" href={isAuthenticated?'/dashboard':'/login'}>{isAuthenticated?'Dashboard':'Log in'}</a><EnterLink isAuthenticated={isAuthenticated}>Get started</EnterLink><button type="button" className="rv-menu-btn" aria-label={open?'Close menu':'Open menu'} aria-expanded={open} onClick={()=>setOpen(v=>!v)}>{open?<X size={20}/>:<Menu size={20}/>}</button></div>
   <AnimatePresence>{open&&<motion.nav className="rv-mobile-menu" aria-label="Mobile navigation" initial={{opacity:0,y:-12}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-12}} transition={{duration:.24}}>{[['Technology','#technology'],['Why VerifAI','#challenges'],['Solutions','#solutions'],['Enter VerifAI',isAuthenticated?'/dashboard':'/login']].map(([label,path])=><a key={label} href={path} onClick={()=>setOpen(false)}>{label}<ArrowUpRight size={16}/></a>)}</motion.nav>}</AnimatePresence>
 </header>;
}
function EmeraldFilm({className=''}:{className?:string}){
 const reduced=useReducedMotion();const media=useRef<HTMLVideoElement>(null);
 useEffect(()=>{
  if(reduced||!media.current)return;
  const el=media.current;
  const observer=new IntersectionObserver(([entry])=>{if(entry.isIntersecting){void el.play().catch(()=>{});}else{el.pause()}},{threshold:.04});
  observer.observe(el);
  return()=>observer.disconnect();
 },[reduced]);
 return <div className={'rv-emerald-film '+className} aria-hidden="true">
  {!reduced && <video ref={media} autoPlay muted loop playsInline preload="metadata" poster="/reference-motion/emerald-poster.png"><source src="/reference-motion/emerald-ribbons.mp4" type="video/mp4"/></video>}
  <div className="rv-emerald-fallback"/>
 </div>
}
function CoreChip(){
 const nodes=Array.from({length:28},(_,i)=>i);
 return <div className="rv-chip-perspective" aria-hidden="true"><motion.div className="rv-chip-shell" initial={{rotateX:38,rotateY:-27,scale:.78,opacity:0}} animate={{rotateX:[38,21,27,21],rotateY:[-27,14,-14,14],scale:1,opacity:1}} transition={{rotateX:{duration:14,repeat:Infinity,ease:'easeInOut'},rotateY:{duration:14,repeat:Infinity,ease:'easeInOut'},scale:{duration:1.25,ease},opacity:{duration:.9}}}>
 <div className="rv-chip-top"><div className="rv-chip-connections">{nodes.map(n=><i key={n}/>)}</div><div className="rv-chip-inner"><span>VERIF</span><strong>AI</strong><small>VERIFY / TRUST</small></div><div className="rv-chip-corners"><i/><i/><i/><i/></div></div>
 <div className="rv-chip-depth"/><div className="rv-chip-base"/>
 </motion.div></div>
}
function Hero({isAuthenticated}:{isAuthenticated:boolean}){
 const ref=useRef<HTMLElement>(null),reduce=useReducedMotion();
 const {scrollYProgress:p}=useScroll({target:ref,offset:['start start','end start']});
 const float=useTransform(p,[0,1],[0,-115]);const fade=useTransform(p,[0,.73,1],[1,1,0]);const chipY=useTransform(p,[0,1],[0,-205]);
 return <section className="rv-hero" ref={ref} id="top" aria-labelledby="rv-title"><EmeraldFilm className="rv-hero-background"/><div className="rv-hero-grid" aria-hidden="true"/>
   <div className="rv-hero-content"><motion.div className="rv-chip-position" style={reduce?undefined:{y:chipY}}><CoreChip/></motion.div>
     <motion.div className="rv-hero-copy" style={reduce?undefined:{y:float,opacity:fade}}>
       <motion.h1 id="rv-title" initial={reduce?false:{y:32,opacity:0,filter:'blur(13px)'}} animate={{y:0,opacity:1,filter:'blur(0px)'}} transition={{duration:1.12,delay:.32,ease}}>Verify to <span>trust AI.</span></motion.h1>
       <motion.p initial={reduce?false:{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{delay:.63,duration:.76,ease}}>Compare model perspectives. Investigate claims.<br/>Make evidence part of every answer.</motion.p>
       <motion.div className="rv-hero-cta" initial={reduce?false:{opacity:0,y:14}} animate={{opacity:1,y:0}} transition={{delay:.86,duration:.66}}><EnterLink isAuthenticated={isAuthenticated}>Enter VerifAI</EnterLink></motion.div>
     </motion.div>
     <div className="rv-hero-trust"><span>ONE QUESTION. MORE CLARITY.</span><div><span>COMPARE</span><i/><span>VERIFY</span><i/><span>SYNTHESIZE</span></div></div>
   </div><a href="#technology" className="rv-scroll-cue">SCROLL TO EXPLORE<ArrowDown size={15}/></a>
 </section>
}
function Technology(){
 const ref=useRef<HTMLElement>(null),reduce=useReducedMotion();const {scrollYProgress:p}=useScroll({target:ref,offset:['start end','end start']});
 const x=useTransform(p,[0,1],[-50,50]);const reveal=useTransform(p,[0,.34,1],[.70,1,1]);
 return <section className="rv-tech" id="technology" ref={ref} aria-labelledby="rv-tech-title">
   <div className="rv-tech-inner"><motion.div className="rv-tech-header" style={reduce?undefined:{scale:reveal}}><h2 id="rv-tech-title">Verification changes<br/><span>the answer.</span></h2><p>VerifAI brings the model, the claim, and the evidence into one continuous review.</p></motion.div>
    <div className="rv-verify-track"><span className="rv-verify-spine" aria-hidden="true"/>{methods.map((entry,i)=>{const Icon=entry.icon;return <motion.article className="rv-verify-step" key={entry.title} initial={reduce?false:{y:40,opacity:0}} whileInView={{y:0,opacity:1}} viewport={{once:true,amount:.36}} transition={{delay:i*.14,duration:.74,ease}}><span className="rv-verify-node"><Icon size={32} strokeWidth={1.1}/></span><span className="rv-verify-no">0{i+1} / 03</span><h3>{entry.title}</h3><p>{entry.copy}</p></motion.article>})}</div>
    <motion.p className="rv-tech-outro" style={reduce?undefined:{x}}>NOT ANOTHER ASSUMPTION. A REASON TO TRUST.</motion.p>
   </div>
 </section>;
}
function Challenge(){
 const reduce=useReducedMotion();return <section className="rv-challenge" id="challenges" aria-labelledby="rv-challenge-title">
 <div className="rv-challenge-shell"><motion.div className="rv-challenge-heading" initial={reduce?false:{opacity:0,y:32}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.45}} transition={{duration:.78,ease}}><span className="rv-mini-pill">The challenge</span><h2 id="rv-challenge-title">More AI answers.<br/><em>More questions.</em></h2><p>Generative models can sound certain even when the evidence is incomplete. Better decisions require a way to examine what lies underneath.</p></motion.div>
 <div className="rv-challenge-grid"><div className="rv-challenge-art"><EmeraldFilm className="rv-challenge-media"/><span className="rv-challenge-art-title">What lies<br/><i>beneath?</i></span><div className="rv-challenge-orb" aria-hidden="true"/><span className="rv-challenge-art-meta">INSPECT THE SIGNAL / 001</span></div>
  <div className="rv-challenge-detail"><div className="rv-challenge-detail-top"><h3>The hard part<br/>isn't the question.</h3><ScanSearch size={30} strokeWidth={1.25}/></div><div className="rv-risk-list">{risks.map((r,i)=><motion.div key={r.title} className="rv-risk-row" initial={reduce?false:{opacity:0,x:24}} whileInView={{opacity:1,x:0}} viewport={{once:true,amount:.55}} transition={{delay:i*.10,duration:.55,ease}}><span><ArrowRight size={15}/></span><div><strong>{r.title}</strong><small>{r.detail}</small></div></motion.div>)}</div><a href="#solutions" className="rv-risk-link">Explore the approach<ArrowUpRight size={16}/></a></div>
 </div></div></section>
}
function Solutions({isAuthenticated}:{isAuthenticated:boolean}){
 const[active,setActive]=useState(0);const reduce=useReducedMotion();
 return <section className="rv-solutions" id="solutions" aria-labelledby="rv-solutions-title"><div className="rv-solutions-intro"><span className="rv-mini-pill">A clearer way forward</span><h2 id="rv-solutions-title">Trust grows when<br/><em>evidence is visible.</em></h2></div>
 <motion.div className="rv-solutions-panel" initial={reduce?false:{clipPath:'inset(0 0 13% 0)',opacity:.7}} whileInView={{clipPath:'inset(0 0 0% 0)',opacity:1}} viewport={{once:true,amount:.13}} transition={{duration:1.05,ease}}>
   <div className="rv-solutions-illustration" aria-hidden="true"><span>VERIFIABLE.</span><div className="rv-orbit-dots"><i/><i/><i/><i/><i/></div></div>
   <div className="rv-solution-list">{solutions.map((s,i)=>{const Icon=s.icon;return <Button variant="ghost" type="button" key={s.title} className={'rv-solution-button'+(active===i?' active':'')} onClick={()=>setActive(i)} aria-pressed={active===i}><span className="rv-solution-number"><Icon size={19} strokeWidth={1.5}/></span><span className="rv-solution-text"><strong>{s.title}</strong><AnimatePresence mode="wait">{active===i&&<motion.small key={s.detail} initial={reduce?false:{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={reduce?undefined:{opacity:0,height:0}} transition={{duration:.28}}>{s.detail}</motion.small>}</AnimatePresence></span><ChevronDown className="rv-solution-chevron" size={17}/></Button>})}<EnterLink isAuthenticated={isAuthenticated}>Explore the workspace</EnterLink></div>
 </motion.div></section>
}
function Footer({isAuthenticated}:{isAuthenticated:boolean}){return <footer className="rv-footer"><div className="rv-footer-main"><div className="rv-footer-logo">VERIF<span>AI.</span><p>AI hallucinates. We investigate.</p></div><div className="rv-footer-links"><a href={isAuthenticated?'/dashboard':'/login'}>Launch app<ArrowUpRight size={14}/></a><a href="https://github.com/Arunprasath-2717/VerifAI" target="_blank" rel="noopener noreferrer">GitHub<ArrowUpRight size={14}/></a><a href="/privacy">Privacy<ArrowUpRight size={14}/></a><a href="/terms">Terms<ArrowUpRight size={14}/></a></div></div><div className="rv-footer-bottom"><span>© {new Date().getFullYear()} VerifAI. All rights reserved.</span><a href="#top">Back to the beginning ↑</a></div></footer>}
export function LandingPage({isAuthenticated}:Props){return <div className="rv-site"><a href="#top" className="rv-skip">Skip to content</a><Header isAuthenticated={isAuthenticated}/><main><Hero isAuthenticated={isAuthenticated}/><Technology/><Challenge/><Solutions isAuthenticated={isAuthenticated}/></main><Footer isAuthenticated={isAuthenticated}/></div>}
