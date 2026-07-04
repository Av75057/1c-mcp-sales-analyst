import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChatStore } from '../../src/features/chat/stores/chatStore';

// Мокаем WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = WebSocket.OPEN;
  send = vi.fn();
  close = vi.fn();
}
vi.stubGlobal('WebSocket', MockWebSocket);

describe('Chat WebSocket Integration', () => {
  beforeEach(() => {
    useChatStore.setState({
      sessions: [], currentSessionId: null, messages: [],
      isTyping: false, streamingContent: '', currentToolCalls: [], error: null,
    });
  });

  it('processes session list', () => {
    const sessions = [
      { id: 's1', title: 'Chat 1', message_count: 5, created_at: '', updated_at: '' },
      { id: 's2', title: 'Chat 2', message_count: 3, created_at: '', updated_at: '' },
    ];
    useChatStore.getState().setSessions(sessions);
    expect(useChatStore.getState().sessions).toHaveLength(2);
  });

  it('processes streaming tokens', () => {
    useChatStore.getState().appendStreamToken('Hello');
    useChatStore.getState().appendStreamToken(' World');
    expect(useChatStore.getState().streamingContent).toBe('Hello World');
    expect(useChatStore.getState().isTyping).toBe(false);
  });

  it('processes tool calls', () => {
    const tc = { name: 'get_sales', args: { date_from: '2026-01-01' } };
    useChatStore.getState().addToolCall(tc);
    expect(useChatStore.getState().currentToolCalls).toHaveLength(1);
    expect(useChatStore.getState().currentToolCalls[0].name).toBe('get_sales');
  });

  it('clears state for new message', () => {
    useChatStore.getState().setStreamingContent('test');
    useChatStore.getState().addToolCall({ name: 'test', args: {} });
    useChatStore.getState().clearStream();
    useChatStore.getState().clearToolCalls();
    expect(useChatStore.getState().streamingContent).toBe('');
    expect(useChatStore.getState().currentToolCalls).toEqual([]);
  });

  it('adds message on done', () => {
    const msg = { id: 'm1', role: 'assistant' as const, content: 'Answer', timestamp: new Date().toISOString() };
    useChatStore.getState().addMessage(msg);
    expect(useChatStore.getState().messages).toHaveLength(1);
  });

  it('sets error state', () => {
    useChatStore.getState().setError('Connection failed');
    expect(useChatStore.getState().error).toBe('Connection failed');
    useChatStore.getState().setError(null);
    expect(useChatStore.getState().error).toBeNull();
  });
});
