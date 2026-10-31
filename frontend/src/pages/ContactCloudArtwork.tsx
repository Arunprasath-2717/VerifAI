import { motion, useReducedMotion } from 'motion/react';
import { ShieldCheck, Sparkles, CheckCircle2, FileCheck2, ChartNoAxesColumnIncreasing, TriangleAlert, Layers3 } from 'lucide-react';

/** Original responsive illustration: a verification engine suspended over the clouds. */
export function ContactCloudArtwork() {
  const reduced = useReducedMotion();
  return <div className="vc-art" role="img" aria-label="VerifAI evidence verification engine floating over clouds, connecting multiple AI models and evidence cards">
    <div className="vc-art-aura" aria-hidden="true"/>
    <motion.div className="vc-art-engine" aria-hidden="true"
      animate={reduced?undefined:{y:[0,-9,0],rotate:[-1,0.7,-1]}}
      transition={{duration:8,repeat:Infinity,ease:'easeInOut'}}>
      <div className="vc-art-island"/>
      <div className="vc-art-ring vc-art-ring-one"/>
      <div className="vc-art-ring vc-art-ring-two"/>
      <div className="vc-art-ring vc-art-ring-three"/>
      <div className="vc-art-foundation vc-art-foundation-back"/>
      <div className="vc-art-foundation vc-art-foundation-front"/>
      <div className="vc-art-core"><ShieldCheck size={113} strokeWidth={1.2}/></div>
      <div className="vc-art-glow"/>
      <div className="vc-art-model vc-art-model-a"><Sparkles size={32}/></div>
      <div className="vc-art-model vc-art-model-b"><Layers3 size={33}/></div>
      <div className="vc-art-model vc-art-model-c">AI</div>
      <div className="vc-art-card vc-art-card-left">
        <FileCheck2 size={24}/><div className="vc-art-line"/><div className="vc-art-line short"/><CheckCircle2 size={22} className="vc-art-success"/>
      </div>
      <div className="vc-art-card vc-art-card-right">
        <ChartNoAxesColumnIncreasing size={39}/><div className="vc-art-line"/><div className="vc-art-line short"/>
      </div>
      <div className="vc-art-card vc-art-card-lower">
        <div className="vc-art-mini-image"/><div><div className="vc-art-line"/><div className="vc-art-line short"/></div><CheckCircle2 size={24} className="vc-art-success"/>
      </div>
      <div className="vc-art-card vc-art-card-status"><CheckCircle2 size={21} className="vc-art-success"/><div className="vc-art-line"/><TriangleAlert size={18} color="#e5ac45"/></div>
      <span className="vc-art-node vc-art-node-a"/><span className="vc-art-node vc-art-node-b"/><span className="vc-art-node vc-art-node-c"/>
    </motion.div>
    <div className="vc-cloud vc-cloud-one"/><div className="vc-cloud vc-cloud-two"/><div className="vc-cloud vc-cloud-three"/>
  </div>;
}
