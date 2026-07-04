import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../../src/features/chat/stores/chatStore';

describe('ChatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      sessions: [],
      currentSessionId: null,
      messages: [],
      isTyping: false,
      streamingContent: '',
      currentToolCalls: [],
      error: null,
    });
  });

  it('initial state is empty', () => {
    const s = useChatStore.getState();
    expect(s.sessions).toEqual([]);
    expect(s.messages).toEqual([]);
    expect(s.isTyping).toBe(false);
  });

  it('adds a message', () => {
    const msg = { id: '1', role: 'user' as const, content: 'Hello', timestamp: new Date().toISOString() };
    useChatStore.getState().addMessage(msg);
    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(useChatStore.getState().messages[0].content).toBe('Hello');
  });

  it('sets typing state', () => {
    useChatStore.getState().setTyping(true);
    expect(useChatStore.getState().isTyping).toBe(true);
  });

  it('appends stream token', () => {
    useChatStore.getState().appendStreamToken('Hello');
    useChatStore.getState().appendStreamToken(' World');
    expect(useChatStore.getState().streamingContent).toBe('Hello World');
  });

  it('clears stream', () => {
    useChatStore.getState().setStreamingContent('test');
    useChatStore.getState().clearStream();
    expect(useChatStore.getState().streamingContent).toBe('');
  });

  it('adds tool call', () => {
    const tc = { name: 'create_chart', args: { chart_type: 'bar' } };
    useChatStore.getState().addToolCall(tc);
    expect(useChatStore.getState().currentToolCalls).toHaveLength(1);
  });

  it('sets sessions', () => {
    const sessions = [{ id: 's1', title: 'Chat 1', created_at: '', updated_at: '', message_count: 0 }];
    useChatStore.getState().setSessions(sessions);
    expect(useChatStore.getState().sessions).toHaveLength(1);
  });

  it('sets error', () => {
    useChatStore.getState().setError('Something went wrong');
    expect(useChatStore.getState().error).toBe('Something went wrong');
  });
});
