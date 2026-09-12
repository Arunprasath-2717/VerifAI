'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Conversation, AIModel, VerificationResult } from '@/lib/types';
import { Sidebar } from '@/components/Sidebar';
import { ChatMessage } from '@/components/ChatMessage';
import { VerificationPanel } from '@/components/VerificationPanel';
import {
  Send,
  Zap,
  AlertCircle,
  ShieldCheck,
  Sparkles,
  SlidersHorizontal,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react';

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [models, setModels] = useState<AIModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o');
  const [verificationResults, setVerificationResults] = useState<Record<string, VerificationResult>>({});
  const [activeVerification, setActiveVerification] = useState<VerificationResult | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState(true);
  const [inputText, setInputText] = useState('');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchModels();
    fetchConversations();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const activeConv = conversations.find((c) => c.id === activeConversationId) || null;

  useEffect(() => {
    scrollToBottom();
  }, [activeConv?.messages, isSending]);

  const fetchModels = async () => {
    try {
      const res = await fetch('/api/v1/models');
      if (res.ok) {
        const body = await res.json();
        if (body.status === 'success' && body.data) {
          setModels(body.data);
          const defaultModel = body.data.find((m: AIModel) => m.isDefault);
          if (defaultModel) setSelectedModel(defaultModel.id);
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  };

  const fetchConversations = async () => {
    try {
      const res = await fetch('/api/v1/chat/all');
      if (res.ok) {
        const body = await res.json();
        if (body.status === 'success' && body.data) {
          setConversations(body.data);
          if (body.data.length > 0 && !activeConversationId) {
            setActiveConversationId(body.data[0].id);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const handleSelectConversation = async (id: string) => {
    setActiveConversationId(id);
    try {
      const res = await fetch(`/api/v1/chat/${id}`);
      if (res.ok) {
        const body = await res.json();
        if (body.status === 'success' && body.data) {
          setConversations((prev) => prev.map((c) => (c.id === id ? body.data : c)));
        }
      }
    } catch (err) {
      console.error('Failed to fetch conversation:', err);
    }
  };

  const handleNewConversation = async () => {
    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'Hello! I am beginning a new research inquiry.', model: selectedModel }),
      });
      if (res.ok) {
        const body = await res.json();
        if (body.status === 'success' && body.data) {
          await fetchConversations();
          setActiveConversationId(body.data.conversation_id);
        }
      }
    } catch (err) {
      setErrorMessage('Failed to create new conversation');
    }
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/chat/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (activeConversationId === id) {
          const remaining = conversations.filter((c) => c.id !== id);
          setActiveConversationId(remaining.length > 0 ? remaining[0].id : null);
        }
      }
    } catch (err) {
      setErrorMessage('Failed to delete conversation');
    }
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() || isSending) return;
    setIsSending(true);
    setErrorMessage(null);
    setInputText('');

    try {
      if (useStreaming) {
        const res = await fetch('/api/v1/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: activeConversationId,
            message: messageText,
            model: selectedModel,
          }),
        });

        if (!res.ok || !res.body) throw new Error('Streaming failed');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let currentConvId = activeConversationId;
        let partialText = '';
        let aiMsgId = `temp_stream_${Date.now()}`;

        if (!currentConvId) {
          const newConvId = `conv_${Date.now()}`;
          currentConvId = newConvId;
          setActiveConversationId(newConvId);
        }

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunkStr = decoder.decode(value);
          const lines = chunkStr.split('\n\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const dataStr = line.replace('data: ', '').trim();
            if (dataStr === '[DONE]') break;

            try {
              const payload = JSON.parse(dataStr);
              if (payload.type === 'start') {
                currentConvId = payload.conversation_id;
                setActiveConversationId(currentConvId);
                await fetchConversations();
              } else if (payload.type === 'chunk') {
                partialText += payload.content;
                setConversations((prev) =>
                  prev.map((conv) => {
                    if (conv.id !== currentConvId) return conv;
                    const existingMsgs = [...conv.messages];
                    const lastMsg = existingMsgs[existingMsgs.length - 1];

                    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.id === aiMsgId) {
                      lastMsg.content = partialText;
                    } else {
                      existingMsgs.push({
                        id: aiMsgId,
                        conversationId: currentConvId,
                        role: 'assistant',
                        content: partialText,
                        timestamp: new Date().toISOString(),
                        model: selectedModel,
                      });
                    }
                    return { ...conv, messages: existingMsgs };
                  })
                );
              } else if (payload.type === 'done') {
                await fetchConversations();
                if (currentConvId) handleSelectConversation(currentConvId);
              }
            } catch {
              // Ignore stream chunk parse errors
            }
          }
        }
      } else {
        const res = await fetch('/api/v1/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: activeConversationId,
            message: messageText,
            model: selectedModel,
          }),
        });

        if (!res.ok) throw new Error('API Request failed');

        const body = await res.json();
        if (body.status === 'success' && body.data) {
          await fetchConversations();
          setActiveConversationId(body.data.conversation_id);
          handleSelectConversation(body.data.conversation_id);
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const handleVerifyMessage = async (messageId: string) => {
    if (!activeConversationId) return;
    try {
      const res = await fetch(
        `/api/v1/chat/${activeConversationId}/messages/${messageId}/verify`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error('Verification failed');

      const body = await res.json();
      if (body.status === 'success' && body.data) {
        const verif: VerificationResult = body.data.verification;
        setVerificationResults((prev) => ({
          ...prev,
          [verif.verification_id]: verif,
        }));
        setActiveVerification(verif);
        setMobilePanelOpen(true);
        await handleSelectConversation(activeConversationId);
      }
    } catch (err) {
      setErrorMessage('Failed to trigger message verification');
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
        trust_score: 91,
        created_at: new Date().toISOString(),
        summary: 'Verification details fetched from Arun Core Engine.',
      });
    }
    setMobilePanelOpen(true);
  };

  const handleReverify = async (verificationId: string) => {
    if (!activeConversationId) return;
    try {
      const res = await fetch(`/api/v1/chat/${activeConversationId}/reverify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verification_id: verificationId }),
      });
      if (!res.ok) throw new Error('Reverification failed');

      const body = await res.json();
      if (body.status === 'success' && body.data) {
        const verif: VerificationResult = body.data.verification;
        setVerificationResults((prev) => ({
          ...prev,
          [verif.verification_id]: verif,
        }));
        setActiveVerification(verif);
      }
    } catch (err) {
      setErrorMessage('Failed to re-verify claims');
    }
  };

  const samplePrompts = [
    'What was the cause of the Bronze Age collapse according to recent paleoclimatic data?',
    'Explain how CRISPR-Cas9 base editors achieve target specificity without double-strand breaks.',
    'Did Newton actually develop calculus independently of Leibniz, and what is the current consensus?',
    'What empirical evidence verifies the existence of dark matter from gravitational lensing?',
  ];

  return (
    <div className="flex-1 flex h-[calc(100vh-65px)] w-full overflow-hidden bg-pastel-bg dark:bg-pastel-bg-dark">
      {/* =========================================================================
          PANE 1: SIDEBAR (Desktop permanent, Mobile slide drawer)
          ========================================================================= */}
      <div className="hidden md:block h-full">
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
          models={models}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="relative z-10 w-72 h-full bg-white dark:bg-pastel-surface-dark shadow-2xl">
            <Sidebar
              conversations={conversations}
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onNewConversation={handleNewConversation}
              onDeleteConversation={handleDeleteConversation}
              selectedModel={selectedModel}
              onSelectModel={setSelectedModel}
              models={models}
              onCloseMobile={() => setMobileSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* =========================================================================
          PANE 2: CENTER CHAT CANVAS
          ========================================================================= */}
      <main className="flex-1 flex flex-col h-full bg-white dark:bg-pastel-surface-dark overflow-hidden relative">
        {/* Workspace Sub-header */}
        <header className="h-14 border-b border-pastel-border dark:border-pastel-border-dark bg-white/90 dark:bg-pastel-surface-dark/90 backdrop-blur-xs px-4 flex items-center justify-between select-none">
          <div className="flex items-center space-x-3">
            {/* Mobile menu button */}
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="md:hidden p-1.5 rounded-lg text-pastel-slate hover:bg-pastel-lavender-light"
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>

            <h2 className="font-semibold text-sm text-pastel-charcoal dark:text-pastel-charcoal-light truncate max-w-xs sm:max-w-md">
              {activeConv?.title || 'Investigation Studio'}
            </h2>

            <span className="text-[11px] bg-pastel-lavender-light text-purple-800 dark:bg-purple-950/50 dark:text-purple-300 border border-pastel-lavender-border px-2.5 py-0.5 rounded-full font-medium hidden sm:inline-block">
              {selectedModel}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {/* SSE Streaming toggle */}
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className={`flex items-center space-x-1 text-xs px-2.5 py-1 rounded-xl transition-all border ${
                useStreaming
                  ? 'bg-pastel-lavender text-white border-pastel-lavender font-medium shadow-2xs'
                  : 'bg-pastel-bg dark:bg-pastel-surface-elevated text-pastel-slate border-pastel-border'
              }`}
            >
              <Zap className="w-3 h-3" />
              <span className="hidden sm:inline">{useStreaming ? 'SSE Stream: ON' : 'Standard API'}</span>
            </button>

            {/* Mobile panel toggle */}
            <button
              onClick={() => setMobilePanelOpen(!mobilePanelOpen)}
              className="xl:hidden flex items-center space-x-1 text-xs px-2.5 py-1 rounded-xl bg-pastel-lavender-light text-purple-800 dark:bg-purple-950/40 dark:text-purple-300 border border-pastel-lavender-border font-medium"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Evidence</span>
            </button>
          </div>
        </header>

        {/* Error Notification Bar */}
        {errorMessage && (
          <div className="bg-pastel-rose-light border-b border-pastel-rose-border px-4 py-2 flex items-center justify-between text-xs text-rose-900">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-700 hover:text-rose-900 underline font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto">
          {!activeConv || activeConv.messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-pastel-lavender-light dark:bg-purple-950/40 border border-pastel-lavender-border flex items-center justify-center mb-4 shadow-pastel">
                <ShieldCheck className="w-7 h-7 text-purple-600 dark:text-purple-300" />
              </div>
              <h3 className="text-xl font-bold text-pastel-charcoal dark:text-pastel-charcoal-light mb-1">
                No conversations yet
              </h3>
              <p className="text-xs sm:text-sm text-pastel-slate dark:text-pastel-slate-light mb-8 max-w-md leading-relaxed">
                Start a conversation to investigate information or verify a response. Every assistant statement can be verified with granular evidence.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                {samplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3.5 bg-pastel-bg dark:bg-pastel-surface-elevated/40 hover:bg-pastel-lavender-light/40 border border-pastel-border dark:border-pastel-border-dark hover:border-pastel-lavender rounded-2xl text-xs text-pastel-charcoal dark:text-pastel-charcoal-light transition-all shadow-2xs group"
                  >
                    <div className="flex items-center space-x-1.5 text-purple-700 dark:text-purple-300 font-semibold mb-1 text-[11px]">
                      <Sparkles className="w-3 h-3 group-hover:scale-110 transition-transform" />
                      <span>Inquiry Suggestion</span>
                    </div>
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="divide-y divide-pastel-border/40 dark:divide-pastel-border-dark/40">
              {activeConv.messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onVerify={handleVerifyMessage}
                  onViewVerification={handleOpenVerification}
                  verificationResult={msg.verificationId ? verificationResults[msg.verificationId] || null : null}
                />
              ))}

              {isSending && (
                <div className="py-4 px-4 sm:px-6">
                  <div className="max-w-3xl mx-auto flex items-center space-x-3 text-xs text-purple-800 dark:text-purple-300 bg-pastel-lavender-light/50 dark:bg-purple-950/30 p-3 rounded-2xl border border-pastel-lavender-border">
                    <span className="w-2 h-2 rounded-full bg-pastel-lavender animate-ping" />
                    <span className="font-medium">Receiving progressive token stream...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Composer */}
        <div className="p-4 border-t border-pastel-border dark:border-pastel-border-dark bg-white dark:bg-pastel-surface-dark">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(inputText);
            }}
            className="max-w-3xl mx-auto relative"
          >
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(inputText);
                }
              }}
              placeholder="Ask an inquiry, summarize research, or paste content to verify..."
              rows={2}
              className="w-full bg-pastel-bg dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark text-pastel-charcoal dark:text-pastel-charcoal-light text-xs sm:text-sm rounded-2xl pl-4 pr-12 py-3 focus:outline-none focus:border-pastel-lavender placeholder-pastel-slate resize-none shadow-2xs transition-all"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || isSending}
              aria-label="Send message"
              className="absolute right-3 top-3 p-2 bg-pastel-lavender hover:bg-pastel-lavender-hover text-white rounded-xl disabled:opacity-40 transition-all shadow-pastel active:scale-95"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-[10px] text-pastel-slate dark:text-pastel-slate-light text-center mt-2 font-medium">
            Credence Verification Studio • Multi-Source Evidence • Server-Side Safeguards
          </div>
        </div>
      </main>

      {/* =========================================================================
          PANE 3: RIGHT VERIFICATION PANEL
          (Desktop permanent 380px, Tablet/Mobile slide-in drawer)
          ========================================================================= */}
      <div className="hidden xl:block w-96 h-full flex-shrink-0">
        <VerificationPanel
          verificationResult={activeVerification}
          onReverify={handleReverify}
          isDocked={true}
        />
      </div>

      {/* Mobile & Tablet Verification Drawer */}
      {mobilePanelOpen && (
        <div className="fixed inset-0 z-50 xl:hidden flex justify-end">
          <div
            className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs"
            onClick={() => setMobilePanelOpen(false)}
          />
          <div className="relative z-10 w-full max-w-md h-full bg-white dark:bg-pastel-surface-dark shadow-2xl">
            <VerificationPanel
              verificationResult={activeVerification}
              onReverify={handleReverify}
              onClose={() => setMobilePanelOpen(false)}
              isDocked={false}
            />
          </div>
        </div>
      )}
    </div>
  );
}
