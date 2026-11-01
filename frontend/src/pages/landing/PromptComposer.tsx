import { useState,useRef,useEffect } from 'react';
import { ArrowUpRight, ArrowRight, Check, ShieldCheck, Layers2, AlignLeft, X } from 'lucide-react';
import { type Mode,modeRoutes } from './landing-data';
import {useDialogFocus} from './Visuals';
type Props={isAuthenticated:boolean};
export function PromptComposer({isAuthenticated}:Props){
 const [prompt,setPrompt]=useState('');
 const [mode,setMode]=useState<Mode>('Compare');
 const [error,setError]=useState('');
 const [preview,setPreview]=useState<{mode:Mode,text:string}|null>(null);
 const field=useRef<HTMLTextAreaElement>(null);
 const choose=(next:Mode)=>{setMode(next);setError('');field.current?.focus()};
 const submit=(e?:React.FormEvent)=>{e?.preventDefault();let text=prompt.trim();if(text.length<5){setError('Add a little more detail (at least 5 characters).');field.current?.focus();return}if(text.length>1800){setError('Please keep your draft under 1,800 characters.');return}setError('');setPreview({mode,text});try{sessionStorage.setItem('verifai.landingDraft',JSON.stringify({mode,text}))}catch{/* storage can be disabled */}};
 useDialogFocus(Boolean(preview));
 const target=isAuthenticated?modeRoutes[preview?.mode||mode]:'/login';
 useEffect(()=>{if(!preview)return;const close=(e:KeyboardEvent)=>{if(e.key==='Escape')setPreview(null)};document.addEventListener('keydown',close);return()=>document.removeEventListener('keydown',close)},[preview]);
 return <>
 <form className="v2-composer" onSubmit={submit} aria-label="Try a VerifAI draft">
   <label className="v2-sr-only" htmlFor="v2-question">Enter a question or claim</label>
   <textarea id="v2-question" ref={field} placeholder="Ask a question worth looking into..." value={prompt} maxLength={1800} rows={2}
     onChange={e=>{setPrompt(e.target.value);if(error)setError('')}} onKeyDown={e=>{if(e.key==='Enter'&&(e.metaKey||e.ctrlKey)){e.preventDefault();submit()}}}/>
   <div className="v2-composer-bottom">
     <div className="v2-modes" aria-label="Select draft purpose">
       <button type="button" aria-pressed={mode==='Compare'} className={mode==='Compare'?'selected':''} onClick={()=>choose('Compare')}><Layers2 size={15}/> Compare</button>
       <button type="button" aria-pressed={mode==='Verify'} className={mode==='Verify'?'selected':''} onClick={()=>choose('Verify')}><ShieldCheck size={15}/> Verify</button>
       <button type="button" aria-pressed={mode==='Summarize'} className={mode==='Summarize'?'selected':''} onClick={()=>choose('Summarize')}><AlignLeft size={15}/> Summarize</button>
     </div>
     <button className="v2-submit" type="submit" aria-label="Preview your draft"><ArrowRight size={20}/></button>
   </div>
   {error&&<p role="alert" className="v2-composer-error">{error}</p>}
 </form>
 <p className="v2-composer-note">DRAFT ONLY — no AI call is made on this page. <kbd>⌘</kbd> + <kbd>↵</kbd> to preview.</p>
 {preview&&<div className="v2-modal-overlay" onMouseDown={e=>{if(e.target===e.currentTarget)setPreview(null)}} role="presentation">
  <section className="v2-modal" role="dialog" aria-modal="true" aria-labelledby="v2-modal-title">
   <div className="v2-modal-head"><span>YOUR WORKSPACE DRAFT / {preview.mode.toUpperCase()}</span><button type="button" onClick={()=>setPreview(null)} aria-label="Close preview"><X size={19}/></button></div>
   <div className="v2-modal-confirm"><Check size={20}/> Draft prepared</div>
   <h2 id="v2-modal-title">A good place to begin.</h2>
   <blockquote>{preview.text}</blockquote>
   <p>Your draft is saved in this browser session. This is a preview, not an AI-generated answer or claim verification. Open the workspace to continue (you may need to paste the draft there).</p>
   <a className="v2-dark-button" href={target}>{isAuthenticated?'Go to workspace':'Sign in to continue'} <ArrowUpRight size={18}/></a>
  </section>
 </div>}
 </>;
}
