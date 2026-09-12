import { Conversation, Message, AIModel, ExtensionConfig, CaptureReportPayload, ExtensionCapturePayload } from './types';

// Supported AI Models
export const AVAILABLE_MODELS: AIModel[] = [
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    description: 'High-intelligence flagship model for complex reasoning and factual tasks.',
    isDefault: true,
  },
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    description: 'State-of-the-art reasoning, coding, and nuanced analysis.',
  },
  {
    id: 'gemini-1-5-pro',
    name: 'Gemini 1.5 Pro',
    provider: 'Google',
    description: 'Highly accurate multimodal model with long context window capabilities.',
  },
  {
    id: 'llama-3-70b',
    name: 'Llama 3 70B',
    provider: 'Meta',
    description: 'Open-weights high performance conversational model.',
  },
];

// Default extension configuration
export const DEFAULT_EXTENSION_CONFIG: ExtensionConfig = {
  version: '1.0.0',
  api_endpoint: '/api/v1/extension',
  auto_capture_enabled: true,
  min_selection_length: 10,
};

// Global in-memory storage for development and runtime persistence
class ChatStore {
  private conversations: Map<string, Conversation> = new Map();
  private captureReports: CaptureReportPayload[] = [];
  private capturedItems: Array<ExtensionCapturePayload & { id: string; timestamp: string }> = [];

  constructor() {
    this.seedDefaultConversation();
  }

  private seedDefaultConversation() {
    const defaultId = 'conv_welcome_1';
    const welcomeConv: Conversation = {
      id: defaultId,
      title: 'Getting Started with VerifAI',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      model: 'gpt-4o',
      messages: [
        {
          id: 'msg_welcome_1',
          conversationId: defaultId,
          role: 'assistant',
          content: 'Hello! I am your AI assistant integrated with VerifAI verification engine. You can ask me questions, and click the **Verify** button on any response to check facts against authoritative sources.',
          timestamp: new Date().toISOString(),
          model: 'gpt-4o',
        },
      ],
    };
    this.conversations.set(defaultId, welcomeConv);
  }

  getConversations(): Conversation[] {
    return Array.from(this.conversations.values()).sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  }

  getConversation(id: string): Conversation | null {
    return this.conversations.get(id) || null;
  }

  createConversation(modelId: string = 'gpt-4o', title?: string): Conversation {
    const id = `conv_${Math.random().toString(36).substring(2, 9)}_${Date.now()}`;
    const newConv: Conversation = {
      id,
      title: title || 'New Conversation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      model: modelId,
      messages: [],
    };
    this.conversations.set(id, newConv);
    return newConv;
  }

  deleteConversation(id: string): boolean {
    return this.conversations.delete(id);
  }

  addMessage(conversationId: string, role: 'user' | 'assistant' | 'system', content: string, model?: string): Message {
    let conv = this.conversations.get(conversationId);
    if (!conv) {
      conv = this.createConversation(model || 'gpt-4o');
    }

    const message: Message = {
      id: `msg_${Math.random().toString(36).substring(2, 9)}_${Date.now()}`,
      conversationId,
      role,
      content,
      timestamp: new Date().toISOString(),
      model: model || conv.model,
      verificationStatus: 'unverified',
    };

    conv.messages.push(message);
    conv.updatedAt = message.timestamp;

    // Auto update title if first user message
    if (conv.messages.length === 1 && role === 'user') {
      conv.title = content.slice(0, 30) + (content.length > 30 ? '...' : '');
    }

    this.conversations.set(conversationId, conv);
    return message;
  }

  updateMessageVerification(conversationId: string, messageId: string, verificationId: string, status: 'unverified' | 'pending' | 'completed' | 'failed') {
    const conv = this.conversations.get(conversationId);
    if (!conv) return null;

    const msg = conv.messages.find((m) => m.id === messageId);
    if (!msg) return null;

    msg.verificationId = verificationId;
    msg.verificationStatus = status;
    this.conversations.set(conversationId, conv);
    return msg;
  }

  addCaptureReport(report: CaptureReportPayload) {
    this.captureReports.push(report);
  }

  getCaptureReports() {
    return this.captureReports;
  }

  addExtensionCapture(payload: ExtensionCapturePayload) {
    const item = {
      id: `cap_${Math.random().toString(36).substring(2, 9)}`,
      ...payload,
      timestamp: new Date().toISOString(),
    };
    this.capturedItems.push(item);
    return item;
  }
}

// Global Singleton Instance across Next.js API hot reloads
const globalForStore = globalThis as unknown as { chatStore?: ChatStore };
export const chatStore = globalForStore.chatStore || new ChatStore();
if (process.env.NODE_ENV !== 'production') globalForStore.chatStore = chatStore;
