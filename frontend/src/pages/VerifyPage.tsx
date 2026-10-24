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
  const [maxClaims, setMaxClaims] = useState(20);
  const [strictConsensus, setStrictConsensus] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [currentStage, setCurrentStage] = useState('');

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleStartVerification = async () => {
    if (!inputText.trim()) return;

    setIsVerifying(true);
    setErrorMessage(null);
    // The synchronous verification endpoint provides no intermediate stage events.
    // Do not invent step transitions based on elapsed time.
    setCurrentStage('Verification request submitted. Waiting for the backend result...');

    try {
      const resp = await verificationApi.createVerification({
        input_text: inputText,
        options: {
          use_web_evidence: verificationMode === 'PRIVATE_KB_PLUS_WEB' && useWebEvidence,
          use_knowledge_base: true,
          strict_consensus: strictConsensus,
          max_claims: maxClaims,
        },
      });

      const newRecord: VerificationRecord = adaptBackendVerificationToRecord(resp);
      newRecord.verificationMode = verificationMode;

      onAddVerification(newRecord);
      setIsVerifying(false);
      if (newRecord.id && newRecord.id !== 'undefined') {
        navigate(`/verification/${newRecord.id}`);
      } else {
        navigate('/history');
      }
    } catch (err: any) {
      setIsVerifying(false);
      setErrorMessage(err?.message || 'Verification pipeline failed. Please check inputs and try again.');
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full space-y-6 pb-16"
    >
      {/* Page Header */}
      <div className="flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border-[#333742] dark:shadow-[0_0_15px_rgba(182,255,46,0.15)] shadow-xs transition-colors">
          <ShieldCheck size={24} strokeWidth={2.4} />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#1B4332] dark:text-white transition-colors">
            Paste & Verify
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#356B52] dark:text-slate-300 transition-colors">
            Analyze an AI-generated answer with claim-level evidence and multi-model consensus.
          </p>
        </div>
      </div>

      {/* Main Workspace Card */}
      <div className="w-full rounded-2xl p-6 sm:p-8 border shadow-xs space-y-6 transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
        
        {/* Large Input Area */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <label className="font-bold text-[#1B4332] dark:text-slate-200">
              AI Answer or Claims to Verify
            </label>
            <span className="font-mono text-xs font-semibold text-[#356B52] dark:text-slate-400">
              {inputText.length} / 20,000
            </span>
          </div>

          <textarea
            rows={6}
            maxLength={20000}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste the AI answer here to deconstruct and audit against ground truth..."
            className="w-full rounded-2xl p-5 text-sm md:text-base transition-all font-sans leading-relaxed outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] placeholder-[#356B52] focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-100 dark:placeholder-slate-500 dark:focus:ring-[#B6FF2E]/30 dark:focus:border-[#B6FF2E]"
          />
        </div>

        {/* Verification Mode Selection - Radio Options */}
        <div className="space-y-3">
          <label className="text-sm font-bold uppercase tracking-wider block text-[#1B4332] dark:text-slate-300">
            Verification Mode
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label
              onClick={() => setVerificationMode('PRIVATE_KB_ONLY')}
              className={`p-4 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                verificationMode === 'PRIVATE_KB_ONLY'
                  ? 'bg-[#74C69D]/25 border-[#1B4332] text-[#1B4332] dark:bg-[#B6FF2E]/10 dark:border-[#B6FF2E] dark:text-white shadow-xs'
                  : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-300 hover:bg-[#D8F3DC]'
              }`}
            >
              <input
                type="radio"
                name="verificationMode"
                checked={verificationMode === 'PRIVATE_KB_ONLY'}
                onChange={() => setVerificationMode('PRIVATE_KB_ONLY')}
                className="accent-[#1B4332] dark:accent-[#B6FF2E]"
              />
              <div className="flex items-center gap-2">
                <Lock size={16} className={verificationMode === 'PRIVATE_KB_ONLY' ? 'text-[#1B4332] dark:text-[#B6FF2E]' : 'text-[#356B52]'} />
                <span className="text-sm font-bold">Private Knowledge Base Only</span>
              </div>
            </label>

            <label
              onClick={() => setVerificationMode('PRIVATE_KB_PLUS_WEB')}
              className={`p-4 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                verificationMode === 'PRIVATE_KB_PLUS_WEB'
                  ? 'bg-[#74C69D]/25 border-[#1B4332] text-[#1B4332] dark:bg-[#B6FF2E]/10 dark:border-[#B6FF2E] dark:text-white shadow-xs'
                  : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-300 hover:bg-[#D8F3DC]'
              }`}
            >
              <input
                type="radio"
                name="verificationMode"
                checked={verificationMode === 'PRIVATE_KB_PLUS_WEB'}
                onChange={() => setVerificationMode('PRIVATE_KB_PLUS_WEB')}
                className="accent-[#1B4332] dark:accent-[#B6FF2E]"
              />
              <div className="flex items-center gap-2">
                <Globe size={16} className={verificationMode === 'PRIVATE_KB_PLUS_WEB' ? 'text-[#1B4332] dark:text-[#B6FF2E]' : 'text-[#356B52]'} />
                <span className="text-sm font-bold">Private Knowledge Base + Web</span>
              </div>
            </label>
          </div>
        </div>

        {/* Toggle Switch: Use Web Evidence */}
        <div className="flex items-center justify-between p-4 rounded-2xl border transition-colors bg-[#D8F3DC] border-[#74C69D] dark:bg-[#181A20] dark:border-[#333742]">
          <div>
            <p className="text-sm font-bold text-[#1B4332] dark:text-slate-200">Use Web Evidence</p>
            <p className="text-xs font-medium text-[#356B52] dark:text-slate-400 mt-0.5">Include web sources in evidence retrieval</p>
          </div>
          <button
            type="button"
            onClick={() => setUseWebEvidence(!useWebEvidence)}
            className={`w-12 h-6 rounded-full transition-colors relative cursor-pointer ${
              useWebEvidence 
                ? 'bg-[#1B4332] dark:bg-[#B6FF2E]' 
                : 'bg-[#74C69D] dark:bg-slate-700'
            }`}
          >
            <span
              className={`block w-5 h-5 rounded-full shadow-xs transition-transform transform ${
                useWebEvidence 
                  ? 'translate-x-6 bg-[#FFFFFF] dark:bg-[#181A20]' 
                  : 'translate-x-0.5 bg-[#FFFFFF]'
              }`}
            />
          </button>
        </div>

        {/* Advanced Options Accordion */}
        <div className="pt-2 border-t border-[#74C69D] dark:border-[#333742]">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full text-sm font-bold text-[#356B52] dark:text-slate-300 hover:text-[#1B4332] dark:hover:text-white py-2 cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <span>Advanced Verification Options</span>
              <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-[#74C69D]/50 dark:bg-[#333742] text-[#1B4332] dark:text-[#B6FF2E]">
                Up to {maxClaims} Claims · {strictConsensus ? 'Strict Consensus' : 'Standard Consensus'}
              </span>
            </div>
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showAdvanced && (
            <div className="p-4 mt-2 rounded-2xl border space-y-5 animate-in fade-in bg-[#D8F3DC] border-[#74C69D] dark:bg-[#181A20] dark:border-[#333742]">
              {/* Only expose options actually supported by the verification API. */}
              <div className="space-y-3">
                <label htmlFor="verify-max-claims" className="flex justify-between text-xs font-bold uppercase tracking-wider text-[#1B4332] dark:text-slate-200">
                  <span>Maximum claims to extract</span>
                  <span className="font-mono text-[#1B4332] dark:text-[#B6FF2E]">{maxClaims}</span>
                </label>
                <input
                  id="verify-max-claims"
                  type="range"
                  min="1"
                  max="50"
                  value={maxClaims}
                  onChange={e => setMaxClaims(Number(e.target.value))}
                  className="w-full accent-[#1B4332] dark:accent-[#B6FF2E]"
                />
                <p className="text-[11px] text-[#356B52] dark:text-slate-400">
                  Passed to the backend as max_claims (1–50).
                </p>
              </div>

              <label className="flex items-start gap-3 pt-3 border-t border-[#74C69D] dark:border-[#2E3340]">
                <input
                  type="checkbox"
                  checked={strictConsensus}
                  onChange={e => setStrictConsensus(e.target.checked)}
                  className="mt-0.5 accent-[#1B4332] dark:accent-[#B6FF2E]"
                />
                <span className="space-y-1">
                  <span className="block text-xs font-bold text-[#1B4332] dark:text-slate-200">Strict contradiction handling</span>
                  <span className="block text-[11px] text-[#356B52] dark:text-slate-400">
                    Pass strict_consensus to the backend. Exact judge-model routing and a percentage threshold are not configurable on this endpoint.
                  </span>
                </span>
              </label>
            </div>
          )}
        </div>

        {/* The verification API is synchronous; show truthful pending state. */}
        {isVerifying && (
          <div className="p-5 rounded-2xl border space-y-3.5 animate-in fade-in bg-[#74C69D]/20 border-[#74C69D] dark:bg-[#181A20] dark:border-[#B6FF2E]/40">
            <div className="flex items-center gap-3">
              <RotateCw size={18} className="animate-spin text-[#1B4332] dark:text-[#B6FF2E]" />
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-[#1B4332] dark:text-[#B6FF2E]">
                  Verification Lifecycle in Progress
                </p>
                <p className="text-sm font-semibold text-[#1B4332] dark:text-white">
                  {currentStage}
                </p>
              </div>
            </div>
            <HaloProgress value={null} translucent />
          </div>
        )}

        {errorMessage && (
          <div role="alert" className="p-4 rounded-2xl border bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs font-semibold">
            {errorMessage}
          </div>
        )}

        {/* Primary CTA with BorderGlow & HaloButton */}
        <div className="pt-2 flex justify-center">
          <BorderGlow
            borderRadius={20}
            glowRadius={26}
            edgeSensitivity={45}
            glowColor={isDark ? '80 100 60' : '152 42 49'}
            backgroundColor={isDark ? '#14161C' : '#FFFFFF'}
            colors={isDark ? ['#B6FF2E', '#A3E823', '#23262F'] : ['#1B4332', '#74C69D', '#D8F3DC']}
            className="w-full"
          >
            <HaloButton
              type="button"
              isLoading={isVerifying}
              loadingText={currentStage || "Analyzing Claim Grounding..."}
              disabled={!inputText.trim() || inputText.length > 20000 || isVerifying}
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
        <h3 className="font-extrabold text-base tracking-tight text-[#1B4332] dark:text-white">
          How it works?
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
                className="p-5 rounded-2xl border shadow-xs space-y-3 transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]"
              >
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-xl font-bold text-xs flex items-center justify-center bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border dark:border-[#B6FF2E]/30">
                    {s.step}
                  </div>
                  <Icon size={16} className="text-[#356B52] dark:text-slate-400" />
                </div>
                <h4 className="text-sm font-bold text-[#1B4332] dark:text-white">{s.title}</h4>
                <p className="text-xs leading-relaxed text-[#356B52] dark:text-slate-300">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

    </motion.div>
  );
};
export default VerifyPage;
