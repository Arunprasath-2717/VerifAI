'use client';

import React from 'react';
import { Message, VerificationResult } from '@/lib/types';
import { ShieldCheck, Shield, Loader2, User, Bot, CheckCircle, AlertTriangle, XCircle, ArrowUpRight } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
  onVerify: (messageId: string) => void;
  onViewVerification?: (verificationId: string) => void;
  verificationResult?: VerificationResult | null;
  isVerifying?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onVerify,
  onViewVerification,
  verificationResult,
  isVerifying = false,
}) => {
  const isUser = message.role === 'user';

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const getVerdictBadge = (verdict?: string) => {
    switch (verdict) {
      case 'SUPPORTED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-mint-light text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300 border border-pastel-mint-border">
            <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600 dark:text-emerald-400" />
            Verified (Trust {verificationResult?.trust_score ?? 88}%)
          </span>
        );
      case 'REFUTED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-rose-light text-rose-900 dark:bg-rose-950/40 dark:text-rose-300 border border-pastel-rose-border">
            <XCircle className="w-3.5 h-3.5 mr-1 text-rose-600 dark:text-rose-400" />
            Refuted (Trust {verificationResult?.trust_score ?? 20}%)
          </span>
        );
      case 'MIXED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-peach-light text-amber-900 dark:bg-amber-950/40 dark:text-amber-300 border border-pastel-peach-border">
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600 dark:text-amber-400" />
            Partially Supported ({verificationResult?.trust_score ?? 65}%)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-pastel-lavender-light text-purple-900 dark:bg-purple-950/40 dark:text-purple-300 border border-pastel-lavender-border">
            <ShieldCheck className="w-3.5 h-3.5 mr-1 text-purple-600 dark:text-purple-400" />
            Inspected (Trust {verificationResult?.trust_score ?? 85}%)
          </span>
        );
    }
  };

  return (
    <div className="py-4 px-4 sm:px-6 animate-fade-in-up">
      <div className="max-w-3xl mx-auto flex items-start space-x-3.5">
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-semibold flex-shrink-0 shadow-2xs ${
            isUser
              ? 'bg-pastel-blue-light text-blue-800 dark:bg-blue-950/50 dark:text-blue-200 border border-pastel-blue-border'
              : 'bg-pastel-lavender text-white shadow-pastel'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        {/* Message Bubble Card */}
        <div
          className={`flex-1 p-4 rounded-2xl border transition-all ${
            isUser
              ? 'bg-pastel-blue-light/50 dark:bg-pastel-surface-elevated border-pastel-blue-border/80 text-pastel-charcoal dark:text-pastel-charcoal-light shadow-2xs'
              : 'bg-white dark:bg-pastel-surface-elevated border-pastel-border dark:border-pastel-border-dark text-pastel-charcoal dark:text-pastel-charcoal-light shadow-pastel-card'
          }`}
        >
          {/* Header row */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-pastel-charcoal dark:text-pastel-charcoal-light">
              {isUser ? 'You' : `AI Assistant (${message.model || 'gpt-4o'})`}
            </span>
            <span className="text-[10px] font-medium text-pastel-slate dark:text-pastel-slate-light">
              {formatTime(message.timestamp)}
            </span>
          </div>

          {/* Text Message Content */}
          <div className="text-sm text-pastel-charcoal dark:text-pastel-charcoal-light leading-relaxed whitespace-pre-wrap break-words font-normal">
            {message.content}
          </div>

          {/* Verification Bar for Assistant Messages */}
          {!isUser && (
            <div className="pt-3 flex flex-wrap items-center justify-between gap-2 border-t border-pastel-border/60 dark:border-pastel-border-dark/60 mt-3">
              {message.verificationStatus === 'pending' || isVerifying ? (
                <div className="flex items-center space-x-2 text-xs font-medium text-purple-800 dark:text-purple-300 bg-pastel-lavender-light dark:bg-purple-950/40 px-3 py-1.5 rounded-xl border border-pastel-lavender-border">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-600 dark:text-purple-400" />
                  <span>Segmenting claims & searching evidence index...</span>
                </div>
              ) : verificationResult || message.verificationId ? (
                <button
                  onClick={() =>
                    onViewVerification &&
                    onViewVerification(message.verificationId || verificationResult?.verification_id || '')
                  }
                  className="flex items-center space-x-2 hover:opacity-90 transition-opacity focus:outline-none"
                  title="Click to view detailed claims and citations in Verification panel"
                >
                  {getVerdictBadge(verificationResult?.verdict)}
                  <span className="text-[11px] text-purple-600 dark:text-purple-300 font-medium inline-flex items-center space-x-0.5 hover:underline">
                    <span>Inspect Evidence</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </span>
                </button>
              ) : (
                <button
                  onClick={() => onVerify(message.id)}
                  className="flex items-center space-x-1.5 text-xs bg-pastel-lavender-light hover:bg-pastel-lavender/30 text-purple-800 dark:text-purple-200 border border-pastel-lavender-border px-3 py-1.5 rounded-xl transition-all font-semibold shadow-2xs active:scale-95"
                >
                  <Shield className="w-3.5 h-3.5 text-purple-600 dark:text-purple-300" />
                  <span>Verify Claims with Evidence</span>
                </button>
              )}

              <span className="text-[10px] text-pastel-slate dark:text-pastel-slate-light font-mono">
                {message.model || 'Arun-Verified'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
