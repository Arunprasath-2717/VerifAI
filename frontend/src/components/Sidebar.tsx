'use client';

import React, { useState } from 'react';
import { Conversation, AIModel } from '@/lib/types';
import { Plus, MessageSquare, Trash2, Cpu, Search, CheckCircle2, ShieldCheck, X } from 'lucide-react';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  models: AIModel[];
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  selectedModel,
  onSelectModel,
  models,
  onCloseMobile,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className="w-64 bg-pastel-lavender-light/40 dark:bg-pastel-surface-dark border-r border-pastel-border dark:border-pastel-border-dark flex flex-col h-full select-none transition-colors">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-pastel-border dark:border-pastel-border-dark flex items-center justify-between bg-white dark:bg-pastel-surface-elevated">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-pastel-lavender/20 border border-pastel-lavender flex items-center justify-center text-purple-700 dark:text-purple-300">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-bold text-xs text-pastel-charcoal dark:text-pastel-charcoal-light">
              Research Chats
            </h2>
            <p className="text-[10px] text-pastel-slate dark:text-pastel-slate-light">
              Verified Sessions
            </p>
          </div>
        </div>

        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="md:hidden p-1 text-pastel-slate hover:text-pastel-charcoal"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Action Buttons & Model Selection */}
      <div className="p-3 space-y-2.5">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center space-x-2 bg-pastel-lavender hover:bg-pastel-lavender-hover text-white py-2 px-3 rounded-xl text-xs font-semibold transition-all shadow-pastel hover:shadow-pastel-hover active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          <span>New Investigation</span>
        </button>

        {/* Model Selector */}
        <div>
          <label className="text-[11px] font-semibold text-pastel-slate dark:text-pastel-slate-light mb-1 flex items-center space-x-1">
            <Cpu className="w-3 h-3 text-purple-600 dark:text-purple-300" />
            <span>Active Model</span>
          </label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="w-full bg-white dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark text-pastel-charcoal dark:text-pastel-charcoal-light text-xs rounded-xl p-2 focus:outline-none focus:border-pastel-lavender shadow-2xs"
          >
            {models.length > 0 ? (
              models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.provider})
                </option>
              ))
            ) : (
              <>
                <option value="gpt-4o">GPT-4o (OpenAI)</option>
                <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Anthropic)</option>
                <option value="llama-3-70b">Llama 3 70B (Meta)</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Search Filter */}
      <div className="px-3 pb-2">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-pastel-slate" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white dark:bg-pastel-surface-elevated border border-pastel-border dark:border-pastel-border-dark text-pastel-charcoal dark:text-pastel-charcoal-light text-xs rounded-xl pl-8 pr-2 py-1.5 focus:outline-none focus:border-pastel-lavender placeholder-pastel-slate shadow-2xs"
          />
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {filteredConversations.length === 0 ? (
          <div className="text-center py-8 text-xs text-pastel-slate dark:text-pastel-slate-light">
            No conversations yet
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isActive = conv.id === activeConversationId;
            return (
              <div
                key={conv.id}
                onClick={() => {
                  onSelectConversation(conv.id);
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition-all ${
                  isActive
                    ? 'bg-white dark:bg-pastel-surface-elevated text-purple-900 dark:text-white font-semibold shadow-2xs border border-pastel-lavender/60'
                    : 'text-pastel-slate dark:text-pastel-slate-light hover:bg-white/60 dark:hover:bg-pastel-surface-elevated/50 hover:text-pastel-charcoal'
                }`}
              >
                <div className="flex items-center space-x-2 truncate">
                  <MessageSquare
                    className={`w-3.5 h-3.5 flex-shrink-0 ${
                      isActive ? 'text-purple-600 dark:text-purple-300' : 'text-pastel-slate'
                    }`}
                  />
                  <span className="truncate">{conv.title}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  title="Delete chat"
                  className="opacity-0 group-hover:opacity-100 text-pastel-slate hover:text-rose-500 p-1 transition-opacity"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="p-3 border-t border-pastel-border dark:border-pastel-border-dark bg-white/70 dark:bg-pastel-surface-elevated text-[11px] text-pastel-slate dark:text-pastel-slate-light flex items-center justify-between">
        <span className="font-medium truncate">Credence Engine</span>
        <span className="flex items-center text-emerald-800 dark:text-emerald-300 font-semibold text-[10px] bg-pastel-mint-light dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-pastel-mint-border">
          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
          Ready
        </span>
      </div>
    </aside>
  );
};
