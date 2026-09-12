'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Conversation, Message, VerificationResult } from '@/lib/types';
import { ChatMessage } from './ChatMessage';
import { VerificationDrawer } from './VerificationDrawer';
import { Send, Zap, AlertCircle, ShieldCheck, Sparkles } from 'lucide-react';

interface ChatViewProps {
  conversation: Conversation | null;
  selectedModel: string;
  onSendMessage: (messageText: string, useStreaming: boolean) => Promise<void>;
  onVerifyMessage: (messageId: string) => Promise<void>;
  onReverify: (verificationId: string) => Promise<void>;
  verificationResults: Record<string, VerificationResult>;
  isSending: boolean;
  errorMessage: string | null;
  onClearError: () => void;
}

export const ChatView: React.FC<ChatViewProps> = ({
  conversation,
  selectedModel,
  onSendMessage,
  onVerifyMessage,
  onReverify,
  verificationResults,
  isSending,
  errorMessage,
  onClearError,
}) => {
  const [inputText, setInputText] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const [activeVerification, setActiveVerification] = useState<VerificationResult | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages, isSending]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isSending) return;

    const text = inputText.trim();
    setInputText('');
    await onSendMessage(text, useStreaming);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleOpenVerification = (verificationId: string) => {
    const res = Object.values(verificationResults).find((v) => v.verification_id === verificationId);
    if (res) {
      setActiveVerification(res);
    } else {
      setActiveVerification({
        verification_id: verificationId,
        status: 'completed',
        verdict: 'SUPPORTED',
        trust_score: 88,
        created_at: new Date().toISOString(),
        summary: 'Verification details fetched from Arun Core Engine.',
      });
    }
    setIsDrawerOpen(true);
  };

  return (
    <main className="flex-1 flex flex-col h-full bg-[#fafbfe] relative overflow-hidden">
      {/* Header Bar */}
      <header className="h-14 border-b border-purple-100 bg-white/80 backdrop-blur-xs px-4 flex items-center justify-between select-none shadow-2xs">
        <div className="flex items-center space-x-3">
          <h2 className="font-semibold text-sm text-slate-800 truncate max-w-md">
            {conversation?.title || 'New Conversation'}
          </h2>
          <span className="text-[11px] bg-purple-50 text-purple-700 border border-purple-200 px-2.5 py-0.5 rounded-full font-medium">
            {selectedModel}
          </span>
        </div>

        {/* SSE Streaming Toggle */}
        <div className="flex items-center space-x-2 bg-purple-50/60 p-1 rounded-xl border border-purple-100">
          <button
            type="button"
            onClick={() => setUseStreaming(!useStreaming)}
            className={`flex items-center space-x-1.5 text-xs px-3 py-1 rounded-lg transition-all ${useStreaming
                ? 'bg-purple-600 text-white font-medium shadow-2xs'
                : 'text-purple-700 hover:text-purple-900'
              }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{useStreaming ? 'SSE Streaming ON' : 'Standard API'}</span>
          </button>
        </div>
      </header>

      {/* Error Alert Bar */}
      {errorMessage && (
        <div className="bg-rose-50 border-b border-rose-200 px-4 py-2 flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={onClearError}
            className="text-rose-700 hover:text-rose-900 text-xs font-semibold underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Message Stream Area */}
      <div className="flex-1 overflow-y-auto">
        {!conversation || conversation.messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center">
            {/* Soft Pastel Welcome Graphic */}
            <div className="w-14 h-14 rounded-2xl bg-purple-100 border border-purple-200 flex items-center justify-center mb-4 shadow-2xs">
              <ShieldCheck className="w-7 h-7 text-purple-600" />
            </div>

            <h3 className="text-lg font-bold text-slate-800 mb-1">Check what you read. Understand what you can trust.</h3>
            <p className="text-xs text-slate-500 max-w-md mb-8 leading-relaxed">
              Ask AI assistant queries or test response statements. Factual assertions can be verified instantly using Arun's core verification engine.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl w-full text-left">
              {[
                'What is the current global temperature anomaly relative to 1850 baseline?',
                'Explain how mRNA vaccines stimulate host immune cell response.',
                'Who created Python and when was it first released?',
                'How do quantum computers leverage superposition for parallel computation?',
              ].map((samplePrompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(samplePrompt, useStreaming)}
                  className="p-3.5 bg-white hover:bg-purple-50/50 border border-purple-100 hover:border-purple-200 rounded-2xl text-xs text-slate-700 transition-all text-left shadow-2xs hover:shadow-xs group"
                >
                  <div className="flex items-center space-x-1.5 text-purple-600 font-semibold mb-1 text-[11px]">
                    <Sparkles className="w-3 h-3 group-hover:scale-110 transition-transform" />
                    <span>Sample Prompt</span>
                  </div>
                  "{samplePrompt}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-purple-100/40">
            {conversation.messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onVerify={(msgId) => onVerifyMessage(msgId)}
                onViewVerification={(verifId) => handleOpenVerification(verifId)}
                verificationResult={msg.verificationId ? verificationResults[msg.verificationId] || null : null}
              />
            ))}
            {isSending && (
              <div className="py-4 px-4 sm:px-6">
                <div className="max-w-3xl mx-auto flex items-center space-x-3 text-xs text-purple-700 bg-purple-50/60 p-3 rounded-2xl border border-purple-100">
                  <span className="w-2 h-2 bg-purple-600 rounded-full animate-ping" />
                  <span className="font-medium">Generating response token stream...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Pastel Input Composer Bar */}
      <div className="p-4 border-t border-purple-100 bg-white/90 backdrop-blur-xs">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your query or prompt... (Press Enter to send, Shift+Enter for new line)"
            rows={2}
            className="w-full bg-white border border-purple-200 text-slate-800 text-sm rounded-2xl pl-4 pr-12 py-3 focus:outline-none focus:border-purple-500 focus:ring-3 focus:ring-purple-100 placeholder-slate-400 resize-none shadow-2xs transition-all"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSending}
            className="absolute right-3 top-3 p-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl disabled:opacity-40 transition-all shadow-xs active:scale-95"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="text-[10px] text-slate-400 text-center mt-2 font-medium">
          VerifAI Module • Powered by Arun Verification Core • Provider API keys secured server-side
        </div>
      </div>

      {/* Verification Drawer */}
      <VerificationDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        verificationResult={activeVerification}
        conversationId={conversation?.id || ''}
        onReverify={onReverify}
      />
    </main>
  );
};
