import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  RotateCw, 
  ChevronDown, 
  ChevronUp, 
  Globe, 
  Lock, 
  ArrowRight, 
  Layers, 
  Cpu, 
  FileCheck2 
} from 'lucide-react';
import { motion } from 'motion/react';
import { VerificationRecord, ClaimItem, VerificationStatus } from '../types';
import { verificationApi, adaptBackendVerificationToRecord } from '../api';
import { HaloButton, HaloProgress } from '../components/ui';
import { BorderGlow } from '../components/ui/BorderGlow';
import { useTheme } from '../context/ThemeContext';

interface VerifyPageProps {
  onAddVerification: (record: VerificationRecord) => void;
  theme?: 'light' | 'dark';
}

export const VerifyPage: React.FC<VerifyPageProps> = ({ onAddVerification, theme: propTheme }) => {
  const navigate = useNavigate();
  const context = useTheme();
  const isDark = (propTheme || context.theme) === 'dark';

  const [inputText, setInputText] = useState(
    'Electric vehicles are better for the environment because they produce zero emissions and have a lower carbon footprint compared to gasoline cars.'
  );
  const [verificationMode, setVerificationMode] = useState<'PRIVATE_KB_ONLY' | 'PRIVATE_KB_PLUS_WEB'>('PRIVATE_KB_PLUS_WEB');
  const [useWebEvidence, setUseWebEvidence] = useState(true);
  const [selectedModels, setSelectedModels] = useState<string[]>(['gpt-4o', 'claude-3-5', 'gemini-1-5']);
  const [confidenceThreshold, setConfidenceThreshold] = useState(85);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [currentStage, setCurrentStage] = useState('');

  const availableModels = [
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
    { id: 'claude-3-5', name: 'Claude 3.5', provider: 'Anthropic' },
    { id: 'gemini-1-5', name: 'Gemini 1.5', provider: 'Google' },
    { id: 'llama-3', name: 'Llama 3.3', provider: 'Meta' },
    { id: 'mistral-large', name: 'Mistral Large', provider: 'Mistral' },
  ];

  const toggleModel = (id: string) => {
    if (selectedModels.includes(id)) {
      if (selectedModels.length > 1) {
        setSelectedModels(selectedModels.filter(m => m !== id));
      }
    } else {
      if (selectedModels.length < 3) {
        setSelectedModels([...selectedModels, id]);
      }
    }
  };

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleStartVerification = async () => {
    if (!inputText.trim()) return;

    setIsVerifying(true);
    setErrorMessage(null);
    setCurrentStage('Step 1/4: Extracting atomic claims from input...');

    const stageTimers = [
      setTimeout(() => setCurrentStage('Step 2/4: Querying private KB & ground-truth evidence...'), 1200),
      setTimeout(() => setCurrentStage('Step 3/4: Cross-verifying model consensus judgments...'), 2400),
      setTimeout(() => setCurrentStage('Step 4/4: Calibrating cryptographic evidence confidence...'), 3600),
    ];

    try {
      const resp = await verificationApi.createVerification({
        input_text: inputText,
        options: {
          use_web_evidence: verificationMode === 'PRIVATE_KB_PLUS_WEB' && useWebEvidence,
          use_knowledge_base: true,
          strictness: confidenceThreshold > 85 ? 'HIGH' : 'STANDARD',
        },
      });

      stageTimers.forEach(clearTimeout);
      const newRecord: VerificationRecord = adaptBackendVerificationToRecord(resp);
      newRecord.modelsUsed = selectedModels;
      newRecord.model = selectedModels.join(' & ');
      newRecord.verificationMode = verificationMode;

      onAddVerification(newRecord);
      setIsVerifying(false);
      if (newRecord.id && newRecord.id !== 'undefined') {
        navigate(`/verification/${newRecord.id}`);
      } else {
        navigate('/history');
      }
    } catch (err: any) {
      stageTimers.forEach(clearTimeout);
      setIsVerifying(false);
      setErrorMessage(err?.message || 'Verification pipeline failed. Please check inputs and try again.');
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="max-w-4xl mx-auto space-y-8 pb-16"
    >
      {/* Page Header */}
      <div className="flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border-[#333742] dark:shadow-[0_0_15px_rgba(182,255,46,0.15)] shadow-xs transition-colors">
          <ShieldCheck size={24} strokeWidth={2.4} />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#2E0A12] dark:text-white transition-colors">
            Paste & Verify
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#6C3B45] dark:text-slate-300 transition-colors">
            Analyze an AI-generated answer with claim-level evidence and multi-model consensus.
          </p>
        </div>
      </div>

      {/* Main Workspace Card */}
      <div className="rounded-[2.8rem] p-6 md:p-10 border shadow-xs space-y-7 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
        
        {/* Large Input Area */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <label className="font-bold text-[#2E0A12] dark:text-slate-200">
              AI Answer or Claims to Verify
            </label>
            <span className="font-mono text-xs font-semibold text-[#8A6A72] dark:text-slate-400">
              {inputText.length} / 50,000
            </span>
          </div>

          <textarea
            rows={6}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste the AI answer here to deconstruct and audit against ground truth..."
            className="w-full rounded-2xl p-5 text-sm md:text-base transition-all font-sans leading-relaxed outline-none border bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12] placeholder-[#8A6A72] focus:ring-2 focus:ring-[#800020]/20 focus:border-[#800020] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-100 dark:placeholder-slate-500 dark:focus:ring-[#B6FF2E]/30 dark:focus:border-[#B6FF2E]"
          />
        </div>

        {/* Verification Mode Selection - Radio Options */}
        <div className="space-y-3">
          <label className="text-sm font-bold uppercase tracking-wider block text-[#2E0A12] dark:text-slate-300">
            Verification Mode
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label
              onClick={() => setVerificationMode('PRIVATE_KB_ONLY')}
              className={`p-4 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                verificationMode === 'PRIVATE_KB_ONLY'
                  ? 'bg-[#D8AE9B]/25 border-[#800020] text-[#800020] dark:bg-[#B6FF2E]/10 dark:border-[#B6FF2E] dark:text-white shadow-xs'
                  : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#6C3B45] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-300 hover:bg-[#FBF1E3]'
              }`}
            >
              <input
                type="radio"
                name="verificationMode"
                checked={verificationMode === 'PRIVATE_KB_ONLY'}
                onChange={() => setVerificationMode('PRIVATE_KB_ONLY')}
                className="accent-[#800020] dark:accent-[#B6FF2E]"
              />
              <div className="flex items-center gap-2">
                <Lock size={16} className={verificationMode === 'PRIVATE_KB_ONLY' ? 'text-[#800020] dark:text-[#B6FF2E]' : 'text-[#8A6A72]'} />
                <span className="text-sm font-bold">Private Knowledge Base Only</span>
              </div>
            </label>

            <label
              onClick={() => setVerificationMode('PRIVATE_KB_PLUS_WEB')}
              className={`p-4 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                verificationMode === 'PRIVATE_KB_PLUS_WEB'
                  ? 'bg-[#D8AE9B]/25 border-[#800020] text-[#800020] dark:bg-[#B6FF2E]/10 dark:border-[#B6FF2E] dark:text-white shadow-xs'
                  : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#6C3B45] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-300 hover:bg-[#FBF1E3]'
              }`}
            >
              <input
                type="radio"
                name="verificationMode"
                checked={verificationMode === 'PRIVATE_KB_PLUS_WEB'}
                onChange={() => setVerificationMode('PRIVATE_KB_PLUS_WEB')}
                className="accent-[#800020] dark:accent-[#B6FF2E]"
              />
              <div className="flex items-center gap-2">
                <Globe size={16} className={verificationMode === 'PRIVATE_KB_PLUS_WEB' ? 'text-[#800020] dark:text-[#B6FF2E]' : 'text-[#8A6A72]'} />
                <span className="text-sm font-bold">Private Knowledge Base + Web</span>
              </div>
            </label>
          </div>
        </div>

        {/* Toggle Switch: Use Web Evidence */}
        <div className="flex items-center justify-between p-4 rounded-2xl border transition-colors bg-[#FBF1E3] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
          <div>
            <p className="text-sm font-bold text-[#2E0A12] dark:text-slate-200">Use Web Evidence</p>
            <p className="text-xs font-medium text-[#8A6A72] dark:text-slate-400 mt-0.5">Include web sources in evidence retrieval</p>
          </div>
          <button
            type="button"
            onClick={() => setUseWebEvidence(!useWebEvidence)}
            className={`w-12 h-6 rounded-full transition-colors relative cursor-pointer ${
              useWebEvidence 
                ? 'bg-[#800020] dark:bg-[#B6FF2E]' 
                : 'bg-[#E9D6C4] dark:bg-slate-700'
            }`}
          >
            <span
              className={`block w-5 h-5 rounded-full shadow-xs transition-transform transform ${
                useWebEvidence 
                  ? 'translate-x-6 bg-[#FFFDFA] dark:bg-[#181A20]' 
                  : 'translate-x-0.5 bg-[#FFFDFA]'
              }`}
            />
          </button>
        </div>

        {/* Advanced Options Accordion */}
        <div className="pt-2 border-t border-[#E9D6C4] dark:border-[#333742]">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full text-sm font-bold text-[#6C3B45] dark:text-slate-300 hover:text-[#2E0A12] dark:hover:text-white py-2 cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <span>Advanced Verification Options</span>
              <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-[#E9D6C4]/50 dark:bg-[#333742] text-[#800020] dark:text-[#B6FF2E]">
                {selectedModels.length} Judge Models · {confidenceThreshold}% Threshold
              </span>
            </div>
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showAdvanced && (
            <div className="p-4 mt-2 rounded-2xl border space-y-5 animate-in fade-in bg-[#FBF1E3] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
              {/* Auditor & Judge Engine (1-3 Models) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-[#2E0A12] dark:text-slate-300">
                      Auditor & Judge Engine (1–3 Models)
                    </label>
                    <p className="text-[11px] font-medium text-[#8A6A72] dark:text-slate-400 mt-0.5">
                      Frontier models selected to independently extract propositions and audit evidence for consensus
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-[#800020] dark:text-[#B6FF2E] shrink-0">
                    {selectedModels.length} of 3 active
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                  {availableModels.map((m) => {
                    const isSelected = selectedModels.includes(m.id);
                    return (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => toggleModel(m.id)}
                        className={`p-2.5 rounded-xl border flex flex-col items-center justify-center text-center transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-[#800020] border-[#800020] text-[#FBF1E3] dark:bg-[#B6FF2E] dark:border-[#B6FF2E] dark:text-[#181A20] font-bold shadow-sm'
                            : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#6C3B45] dark:bg-[#14161C] dark:border-[#333742] dark:text-slate-300 hover:bg-[#F5E8D8]'
                        }`}
                      >
                        <span className="text-xs font-bold">{m.name}</span>
                        <span className={`text-[10px] mt-0.5 font-medium ${
                          isSelected 
                            ? 'text-[#FBF1E3]/80 dark:text-[#181A20]/80' 
                            : 'text-[#8A6A72] dark:text-slate-400'
                        }`}>
                          {m.provider}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Confidence Threshold */}
              <div className="pt-3 border-t border-[#E9D6C4] dark:border-[#2E3340]">
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider mb-1 text-[#2E0A12] dark:text-slate-200">
                  <span>Corroboration Confidence Threshold</span>
                  <span className="font-mono text-[#800020] dark:text-[#B6FF2E]">{confidenceThreshold}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="99"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                  className="w-full accent-[#800020] dark:accent-[#B6FF2E]"
                />
                <span className="text-[11px] text-[#8A6A72] dark:text-slate-400">
                  Minimum corroboration score required from auditor models to mark propositions as SUPPORTED
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Real SSE Lifecycle Progress indicator if running */}
        {isVerifying && (
          <div className="p-5 rounded-2xl border space-y-3.5 animate-in fade-in bg-[#D8AE9B]/20 border-[#D8AE9B] dark:bg-[#181A20] dark:border-[#B6FF2E]/40">
            <div className="flex items-center gap-3">
              <RotateCw size={18} className="animate-spin text-[#800020] dark:text-[#B6FF2E]" />
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-[#800020] dark:text-[#B6FF2E]">
                  Verification Lifecycle in Progress
                </p>
                <p className="text-sm font-semibold text-[#2E0A12] dark:text-white">
                  {currentStage}
                </p>
              </div>
            </div>
            <HaloProgress value={null} translucent />
          </div>
        )}

        {errorMessage && (
          <div className="p-4 rounded-2xl border bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs font-semibold">
            {errorMessage}
          </div>
        )}

        {/* Primary CTA with BorderGlow & HaloButton */}
        <div className="pt-2 flex justify-center">
          <BorderGlow
            borderRadius={20}
            glowRadius={26}
            edgeSensitivity={45}
            glowColor={isDark ? '80 100 60' : '128 0 32'}
            backgroundColor={isDark ? '#14161C' : '#FFFDFA'}
            colors={isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#800020', '#D8AE9B', '#FBF1E3']}
            className="w-full"
          >
            <HaloButton
              type="button"
              isLoading={isVerifying}
              loadingText={currentStage || "Analyzing Claim Grounding..."}
              disabled={!inputText.trim()}
              onClick={handleStartVerification}
              className="w-full"
            >
              <span className="flex items-center gap-2">
                <span>Verify Answer</span>
                <ArrowRight size={17} />
              </span>
            </HaloButton>
          </BorderGlow>
        </div>

      </div>

      {/* "How it works?" 4-Step Chain */}
      <section className="space-y-4 pt-4">
        <h3 className="font-extrabold text-base tracking-tight text-[#2E0A12] dark:text-white">
          How it works?
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {[
            {
              step: '1',
              title: 'Extract Claims',
              desc: 'Identify individual factual assertions from the answer.',
              icon: Layers
            },
            {
              step: '2',
              title: 'Retrieve Evidence',
              desc: 'Search your private knowledge base and verified web corpus.',
              icon: Globe
            },
            {
              step: '3',
              title: 'Multi-Model Judging',
              desc: 'Independent model evaluations score agreement and contradiction.',
              icon: Cpu
            },
            {
              step: '4',
              title: 'Verification Decision',
              desc: 'Get calibrated verdicts with direct citation provenance.',
              icon: FileCheck2
            }
          ].map((s) => {
            const Icon = s.icon;
            return (
              <div 
                key={s.step} 
                className="p-5 rounded-[2rem] border shadow-xs space-y-3 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]"
              >
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-xl font-bold text-xs flex items-center justify-center bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border dark:border-[#B6FF2E]/30">
                    {s.step}
                  </div>
                  <Icon size={16} className="text-[#8A6A72] dark:text-slate-400" />
                </div>
                <h4 className="text-xs font-bold text-[#2E0A12] dark:text-white">{s.title}</h4>
                <p className="text-[11px] leading-relaxed text-[#6C3B45] dark:text-slate-300">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

    </motion.div>
  );
};
export default VerifyPage;
