import { create } from 'zustand';

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: { image_base64?: string; chart_id?: string };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tool_calls?: ToolCall[];
  chart_image?: string;
  timestamp: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ChatState {
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  isTyping: boolean;
  streamingContent: string;
  currentToolCalls: ToolCall[];
  error: string | null;

  setSessions: (sessions: Session[]) => void;
  setCurrentSession: (id: string) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (msg: Message) => void;
  setTyping: (v: boolean) => void;
  appendStreamToken: (token: string) => void;
  clearStream: () => void;
  setStreamingContent: (content: string) => void;
  addToolCall: (tc: ToolCall) => void;
  clearToolCalls: () => void;
  setError: (err: string | null) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  isTyping: false,
  streamingContent: '',
  currentToolCalls: [],
  error: null,

  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (id) => set({ currentSessionId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setTyping: (v) => set({ isTyping: v }),
  appendStreamToken: (token) => set((s) => ({ streamingContent: s.streamingContent + token })),
  clearStream: () => set({ streamingContent: '' }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  addToolCall: (tc) => set((s) => ({ currentToolCalls: [...s.currentToolCalls, tc] })),
  clearToolCalls: () => set({ currentToolCalls: [] }),
  setError: (err) => set({ error: err }),
}));
