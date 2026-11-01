import { motion, useInView, useReducedMotion } from 'motion/react';
import { useRef, useEffect } from 'react';
import { ArrowUpRight, ArrowRight, Check, CircleDashed, Minus } from 'lucide-react';

export function Eyebrow({children,light=false}:{children:React.ReactNode,light?:boolean}) {
  return <span className={'v2-eyebrow'+(light?' v2-eyebrow-light':'')}><span aria-hidden="true" className="v2-eyebrow-marker"/> {children}</span>;
}
export function Reveal({children,className='',delay=0}:{children:React.ReactNode,className?:string,delay?:number}) {
  const ref=useRef<HTMLDivElement>(null);
  const on=useInView(ref,{once:true,margin:'0px 0px -8% 0px'});
  const reduce=useReducedMotion();
  return <motion.div ref={ref} className={className} initial={reduce?false:{opacity:0,y:32}} animate={on?{opacity:1,y:0}:undefined} transition={{duration:.78,delay,ease:[.22,1,.36,1]}}>{children}</motion.div>;
}
export function ProductIllustration({variant='compare',compact=false}:{variant?:'compare'|'verify'|'summarize',compact?:boolean}) {
  return <div className={'v2-ui-art v2-ui-art-'+variant+(compact?' v2-ui-art-small':'')} aria-label={variant+' workflow interface illustration'}>
    <div className="v2-ui-top"><span className="v2-ui-dots"><i/><i/><i/></span><span>VERIFAI / WORKSPACE</span><span>● LOCAL PREVIEW</span></div>
    <div className="v2-ui-question"><span>QUESTION / 001</span><p>Can we trust the first answer?</p><span className="v2-ui-mini-line"/></div>
    <div className="v2-ui-cards">
      <div className="v2-ui-card"><span>MODEL / 01</span><div className="v2-ui-line long"/><div className="v2-ui-line"/><div className="v2-ui-line mid"/><div className="v2-ui-blocks"><b/><b/><b/></div></div>
      <div className="v2-ui-card"><span>MODEL / 02</span><div className="v2-ui-line"/><div className="v2-ui-line long"/><div className="v2-ui-line mid"/><div className="v2-ui-blocks"><b/><b/><b/></div></div>
      <div className="v2-ui-card v2-ui-card-third"><span>MODEL / 03</span><div className="v2-ui-line mid"/><div className="v2-ui-line"/><div className="v2-ui-line long"/><div className="v2-ui-blocks"><b/><b/><b/></div></div>
    </div>
    <div className="v2-ui-result">
      <span>{variant==='verify'?'EVIDENCE REVIEW':variant==='summarize'?'SYNTHESIS':'CROSS-MODEL REVIEW'}</span>
      <span className="v2-ui-result-icon">{variant==='verify'?<Check size={16}/>:variant==='summarize'?<Minus size={16}/>:<CircleDashed size={16}/>}</span>
      <div className="v2-ui-bar"/><div className="v2-ui-bar half"/>
      <small>Illustrative interface · not a live verification</small>
    </div>
  </div>;
}
export function SectionArrow({href,children}:{href:string,children:React.ReactNode}){return <a className="v2-text-link" href={href}>{children}<ArrowUpRight size={18}/></a>}
export function RoundArrow(){return <span className="v2-round-arrow"><ArrowRight size={19}/></span>}


// Keeps focus within landing-page dialogs and restores it on dismissal.
// No global focus management is left behind when the dialog unmounts.
export function useDialogFocus(open:boolean) {
  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = document.querySelector<HTMLElement>('.v2-modal[role="dialog"]');
    const focusable = () => Array.from(dialog?.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])') ?? []);
    const priorOverflow = document.body.style.overflow;
    document.body.style.overflow='hidden';
    focusable()[0]?.focus({preventScroll:true});
    const onKey = (event:KeyboardEvent) => {
      if (event.key !== 'Tab') return;
      const nodes=focusable();
      if (nodes.length===0) return;
      const first=nodes[0], last=nodes[nodes.length-1];
      if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
    };
    document.addEventListener('keydown',onKey);
    return () => {
      document.removeEventListener('keydown',onKey);
      document.body.style.overflow=priorOverflow;
      previous?.focus({preventScroll:true});
    };
  },[open]);
}
