import {useEffect,useRef,useState} from 'react';
import {motion,useReducedMotion,useScroll,useMotionValueEvent,useTransform,AnimatePresence} from 'motion/react';
import {ArrowUpRight,ArrowRight,ArrowLeft,Check,ChevronDown,Plus,X,MoveUpRight,PanelTop,ScanSearch,Split,MessageSquareQuote,ShieldCheck} from 'lucide-react';
import {examples,faq,methodSteps} from './landing-data';
import {Eyebrow,Reveal,ProductIllustration,RoundArrow,SectionArrow,useDialogFocus} from './Visuals';

type Example=(typeof examples)[number];

export function WorkspaceShowcase({isAuthenticated}:{isAuthenticated:boolean}){
 const [tab,setTab]=useState<'compare'|'verify'|'summarize'>('compare');
 const tabs=[{id:'compare',name:'Compare models',icon:Split},{id:'verify',name:'Check a claim',icon:ScanSearch},{id:'summarize',name:'Synthesize',icon:PanelTop}] as const;
 const texts={compare:['See more than one side.','Compare answers in parallel to understand where they agree and where they differ.'],verify:['Follow the claim.','Investigate individual statements and keep the evidence trail in view.'],summarize:['Make the next step clearer.','Bring different perspectives into one review without hiding uncertainty.']};
 const path=isAuthenticated?(tab==='verify'?'/verify':'/chat'):'/login';
 return <section className="v2-workspace-section" id="product" aria-labelledby="v2-workspace-title">
   <div className="v2-content">
     <Reveal className="v2-workspace-top"><Eyebrow>THE PRODUCT / 01—03</Eyebrow><div className="v2-workspace-heading"><h2 id="v2-workspace-title">Multiple perspectives.<br/><em>One place to think.</em></h2><p>Your models, your questions, your next informed decision. A workspace built to make the thought process visible.</p></div></Reveal>
     <div className="v2-tabs" role="tablist" aria-label="Product workflow">
       {tabs.map(t=><button key={t.id} type="button" role="tab" aria-selected={tab===t.id} onClick={()=>setTab(t.id)} className={tab===t.id?'active':''}><t.icon size={18}/>{t.name}<span>0{tabs.indexOf(t)+1}</span></button>)}
     </div>
     <div className="v2-showcase-layout">
       <AnimatePresence mode="wait"><motion.div key={tab} initial={{opacity:0,y:15}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} transition={{duration:.30}} className="v2-showcase-visual" role="tabpanel">
          <ProductIllustration variant={tab}/>
       </motion.div></AnimatePresence>
       <div className="v2-showcase-side"><Eyebrow>IN THE WORKSPACE</Eyebrow><h3>{texts[tab][0]}</h3><p>{texts[tab][1]}</p><SectionArrow href={path}>Open {tab==='verify'?'verification':'workspace'}</SectionArrow><div className="v2-showcase-index">0{tabs.findIndex(t=>t.id===tab)+1} <span>/ 03</span></div></div>
     </div>
   </div>
 </section>
}

export function StickyMethod(){
 const ref=useRef<HTMLElement>(null);
 const reduce=useReducedMotion();
 const {scrollYProgress}=useScroll({target:ref,offset:['start start','end end']});
 const [stage,setStage]=useState(0);
 useMotionValueEvent(scrollYProgress,'change',v=>setStage(Math.min(3,Math.floor(Math.max(0,v)*4))));
 const current=methodSteps[stage];
 return <section className="v2-method" id="method" ref={ref} aria-labelledby="v2-method-title">
  <div className="v2-method-sticky">
   <div className="v2-content v2-method-grid">
    <div className="v2-method-info">
     <Eyebrow light>HOW IT WORKS / IN FOUR MOVEMENTS</Eyebrow>
     <h2 id="v2-method-title">From <i>answer</i><br/>to understanding.</h2>
     <div className="v2-method-list">
      {methodSteps.map((s,i)=><button type="button" key={s.n} className={'v2-method-step'+(i===stage?' active':'')} onClick={()=>{setStage(i);if(!reduce&&ref.current){const r=ref.current.getBoundingClientRect(),start=window.scrollY+r.top;const range=ref.current.offsetHeight-window.innerHeight;window.scrollTo({top:start+range*((i+.3)/4),behavior:'smooth'})}}} aria-current={i===stage?'step':undefined}><span>{s.n}</span>{s.name}<ArrowUpRight size={16}/></button>)}
     </div>
    </div>
    <div className="v2-method-scene">
     <div className="v2-method-stage-head"><span>VERIFICATION FLOW</span><span>0{stage+1} — 04</span></div>
     <AnimatePresence mode="wait"><motion.div key={current.n} className="v2-method-card" initial={reduce?false:{opacity:0,y:22,scale:.98}} animate={{opacity:1,y:0,scale:1}} exit={reduce?undefined:{opacity:0,y:-16,scale:1.01}} transition={{duration:.38,ease:[.22,1,.36,1]}}>
       <span className="v2-method-counter">{current.n} / WORKFLOW</span><h3>{current.headline}</h3><p>{current.copy}</p>
       <div className="v2-method-diagram"><span>{current.label}</span><div>{current.detail}</div><small>ILLUSTRATIVE WORKFLOW FRAME</small></div>
     </motion.div></AnimatePresence>
     <div className="v2-method-progress" aria-label={'Workflow step '+(stage+1)+' of 4'}><motion.span style={reduce?{width:((stage+1)*25)+'%'}:{scaleX:scrollYProgress}}/></div>
    </div>
   </div>
  </div>
 </section>
}

function EditorialReel(){
 const track=useRef<HTMLDivElement>(null);
 const drag=useRef({active:false,x:0,scroll:0});
 const move=(direction:number)=>track.current?.scrollBy({left:direction*(track.current.clientWidth*.76),behavior:'smooth'});
 const items=[['01','ASK','Start with the right question'],['02','COMPARE','Look across perspectives'],['03','CHECK','Inspect the evidence'],['04','UNDERSTAND','Keep the uncertainty']];
 return <div className="v2-reel">
  <div className="v2-reel-heading"><div><Eyebrow>FOUR WORKING MODES</Eyebrow><h3>A thought in motion.</h3></div><div className="v2-reel-controls"><span>DRAG OR USE ARROWS</span><button type="button" aria-label="Previous reel item" onClick={()=>move(-1)}><ArrowLeft size={18}/></button><button type="button" aria-label="Next reel item" onClick={()=>move(1)}><ArrowRight size={18}/></button></div></div>
  <div className="v2-reel-track" ref={track} role="region" aria-label="Explore workflow reel" tabIndex={0}
   onKeyDown={e=>{if(e.key==='ArrowLeft'){e.preventDefault();move(-1)}if(e.key==='ArrowRight'){e.preventDefault();move(1)}}}
   onPointerDown={e=>{if(e.pointerType==='mouse'||e.pointerType==='pen'){drag.current={active:true,x:e.clientX,scroll:e.currentTarget.scrollLeft};e.currentTarget.setPointerCapture(e.pointerId)}}}
   onPointerMove={e=>{if(drag.current.active)e.currentTarget.scrollLeft=drag.current.scroll+(drag.current.x-e.clientX)}}
   onPointerUp={()=>{drag.current.active=false}}
   onPointerCancel={()=>{drag.current.active=false}}>
   {items.map(([n,title,copy])=><div className="v2-reel-card" key={n}><span>{n} / 04</span><strong>{title}</strong><p>{copy}</p><ArrowUpRight size={21}/></div>)}
  </div>
 </div>;
}

function GalleryArtwork({item}:{item:Example}){
 return <div className={'v2-gallery-art v2-gallery-art-'+item.color} aria-hidden="true">
  <div className="v2-gallery-chip"><span>VERIFAI / {item.id.toUpperCase()}</span><span>↗</span></div>
  <div className="v2-gallery-graphic">
    {item.id==='comparison'||item.id==='models'? <><div className="v2-graphic-col"/><div className="v2-graphic-col"/><div className="v2-graphic-col"/></>
     :item.id==='verification'||item.id==='uncertainty'?<><div className="v2-graphic-circles"><i/><i/><i/></div><div className="v2-graphic-lens"/></>
     :<><div className="v2-graphic-lines"><i/><i/><i/><i/><i/></div></>}
  </div>
  <span className="v2-gallery-big-index">{item.eyebrow.split(' ')[0]}</span>
 </div>
}

export function Gallery(){
 const [filter,setFilter]=useState('All');
 const [selected,setSelected]=useState<Example|null>(null);
 const cats=['All','Models','Evidence','Workflow'];
 const shown=examples.filter(x=>filter==='All'||x.category===filter);
 const reduce=useReducedMotion();
 useDialogFocus(Boolean(selected));
 useEffect(()=>{if(!selected)return;const key=(e:KeyboardEvent)=>{if(e.key==='Escape')setSelected(null)};document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key)},[selected]);
 return <section className="v2-gallery-section" id="explore" aria-labelledby="v2-gallery-title">
  <div className="v2-content">
   <Reveal className="v2-gallery-intro"><Eyebrow>EXPLORE THE SYSTEM</Eyebrow><h2 id="v2-gallery-title">A workspace in<br/><i>many perspectives.</i></h2><p>Explore six ways to approach a question. These are interactive concept frames, not fabricated model output.</p></Reveal>
   <div className="v2-gallery-filter" role="group" aria-label="Filter product concepts">{cats.map(x=><button type="button" key={x} onClick={()=>setFilter(x)} className={filter===x?'active':''} aria-pressed={filter===x}>{x}</button>)}<span>{String(shown.length).padStart(2,'0')} ITEMS</span></div>
   <motion.div layout={!reduce} className="v2-gallery-grid">
    <AnimatePresence mode="popLayout">{shown.map((item,index)=><motion.button type="button" key={item.id} className="v2-gallery-card" onClick={()=>setSelected(item)} aria-label={'Explore '+item.title} layout={!reduce} initial={reduce?false:{opacity:0,scale:.97}} animate={{opacity:1,scale:1}} exit={reduce?undefined:{opacity:0,scale:.96}} transition={{duration:.3}}><GalleryArtwork item={item}/><div className="v2-gallery-card-info"><div><span>{item.eyebrow}</span><h3>{item.title}</h3></div><RoundArrow/></div></motion.button>)}</AnimatePresence>
   </motion.div>
   <EditorialReel/>
  </div>
  {selected&&<div className="v2-modal-overlay" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)setSelected(null)}}><section role="dialog" aria-modal="true" aria-labelledby="v2-gallery-dialog-title" className="v2-modal v2-gallery-dialog"><div className="v2-modal-head"><span>{selected.eyebrow}</span><button type="button" onClick={()=>setSelected(null)} aria-label="Close"><X size={20}/></button></div><GalleryArtwork item={selected}/><h2 id="v2-gallery-dialog-title">{selected.title}</h2><p>{selected.text}</p><span className="v2-demo-label">CONCEPT PREVIEW / NOT A LIVE RESULT</span></section></div>}
 </section>
}

export function Comparison(){
 const [split,setSplit]=useState(49);
 return <section className="v2-compare-section" id="evidence" aria-labelledby="v2-compare-title">
 <div className="v2-content v2-compare-layout">
  <Reveal className="v2-compare-copy"><Eyebrow>THE DIFFERENCE</Eyebrow><h2 id="v2-compare-title">An answer is easy.<br/><i>Context is harder.</i></h2><p>Explore how the same claim changes when evidence and uncertainty are made visible. Move the divider to inspect both perspectives.</p><div className="v2-demo-label">ILLUSTRATIVE EXAMPLE — NO LIVE CLAIM ASSESSED</div></Reveal>
  <div className="v2-compare-frame" aria-label="Before and after evidence illustration">
   <div className="v2-compare-top"><span>CLAIM: “THIS IS ALWAYS TRUE.”</span><span>EXAMPLE / 001</span></div>
   <div className="v2-before"><span>WITHOUT REVIEW</span><strong>“Yes. This is correct.”</strong><p>An unqualified answer with no traceable supporting context.</p></div>
   <div className="v2-after" style={{clipPath:'inset(0 '+(100-split)+'% 0 0)'}}><span>WITH REVIEW</span><strong>“The evidence is incomplete.”</strong><p>Check the claim, inspect sources and preserve what remains uncertain.</p><div className="v2-after-check"><Check size={16}/> REVIEW THE EVIDENCE</div></div>
   <div className="v2-compare-handle" style={{left:split+'%'}} aria-hidden="true"><span>↔</span></div>
   <label className="v2-sr-only" htmlFor="v2-compare-slider">Adjust evidence comparison</label><input id="v2-compare-slider" type="range" min="5" max="95" value={split} onChange={e=>setSplit(Number(e.target.value))} aria-valuetext={split+' percent comparison shown'}/>
  </div>
 </div></section>;
}

export function FAQ(){
 return <section className="v2-faq-section" id="faq" aria-labelledby="v2-faq-title"><div className="v2-content v2-faq-grid">
  <Reveal><Eyebrow>GOOD QUESTIONS</Eyebrow><h2 id="v2-faq-title">A little more<br/><i>clarity.</i></h2><p>No invented statistics, no promises of perfect accuracy. Just a clearer view of what this product is for.</p></Reveal>
  <div className="v2-faq-list">{faq.map(([q,a],i)=><details key={q} open={i===0}><summary><span>{String(i+1).padStart(2,'0')}</span>{q}<Plus className="v2-faq-plus" size={19}/></summary><p>{a}</p></details>)}</div>
 </div></section>;
}
