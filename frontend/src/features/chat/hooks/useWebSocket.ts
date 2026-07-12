import { useEffect, useRef, useCallback } from 'react';
import { useChatStore } from '../stores/chatStore';
import type { Message, ToolCall } from '../stores/chatStore';

interface WsMessage {
  type: 'token' | 'chart' | 'done' | 'error' | 'tool_call' | 'full_message' | 'sessions' | 'messages';
  content?: string;
  chart_type?: string;
  data?: any;
  config?: any;
  image_base64?: string;
  name?: string;
  args?: Record<string, unknown>;
  message?: Message;
  sessions?: any[];
  messages?: any[];
  id?: string;
}

export function useChatWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const { setTyping, appendStreamToken, clearStream, addToolCall, clearToolCalls, addMessage, setSessions, setMessages, setError, setCurrentSession, currentSessionId } = useChatStore();

  const connect = useCallback((sessionId?: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    const sid = sessionId || 'new';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/chat/${sid}`;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setError(null);
      // Автоматически загружаем сессии при подключении
      ws.current?.send(JSON.stringify({ type: 'get_sessions' }));
    };

    ws.current.onmessage = (event) => {
      try {
        const data: WsMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'sessions':
            setSessions(data.sessions || []);
            break;

          case 'messages':
            setMessages(data.messages || []);
            if (data.id) setCurrentSession(data.id);
            break;

          case 'token':
            setTyping(true);
            appendStreamToken(data.content || '');
            break;

          case 'chart':
            addToolCall({
              name: 'create_chart',
              args: data.config || {},
              result: { image_base64: data.image_base64, chart_id: '' },
            });
            break;

          case 'tool_call':
            addToolCall({
              name: data.name || '',
              args: data.args || {},
            });
            break;

          case 'full_message':
            clearStream();
            clearToolCalls();
            setTyping(false);
            if (data.message) addMessage(data.message);
            break;

          case 'done':
            if (useChatStore.getState().streamingContent || useChatStore.getState().currentToolCalls.length > 0) {
              const finalContent = useChatStore.getState().streamingContent;
              const finalTools = [...useChatStore.getState().currentToolCalls];
              addMessage({
                id: Date.now().toString(),
                role: 'assistant',
                content: finalContent,
                tool_calls: finalTools,
                chart_image: finalTools.find(t => t.name === 'create_chart')?.result?.image_base64 || undefined,
                timestamp: new Date().toISOString(),
              });
            }
            clearStream();
            clearToolCalls();
            setTyping(false);
            break;

          case 'error':
            setError(data.content || 'Ошибка');
            setTyping(false);
            break;
        }
      } catch (e) {
        console.warn('WS parse error:', e);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 3s
      reconnectTimer.current = setTimeout(() => connect(sessionId), 3000);
    };

    ws.current.onerror = () => {
      setError('WebSocket connection error');
    };
  }, [currentSessionId]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    ws.current?.close();
    ws.current = null;
  }, []);

  const sendMessage = useCallback((text: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      setError('WebSocket не подключён');
      return;
    }
    clearStream();
    clearToolCalls();
    useChatStore.getState().setStreamingContent('');
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    });
    setTyping(true);
    ws.current.send(JSON.stringify({ type: 'message', content: text }));
  }, []);

  const loadSessions = useCallback(() => {
    ws.current?.send(JSON.stringify({ type: 'get_sessions' }));
  }, []);

  const loadMessages = useCallback((sessionId: string) => {
    setCurrentSession(sessionId);
    ws.current?.send(JSON.stringify({ type: 'get_messages', session_id: sessionId }));
  }, []);

  const deleteSession = useCallback((sessionId: string) => {
    ws.current?.send(JSON.stringify({ type: 'delete_session', session_id: sessionId }));
    if (useChatStore.getState().currentSessionId === sessionId) {
      setCurrentSession(null);
      setMessages([]);
    }
  }, []);

  const newSession = useCallback(() => {
    setCurrentSession(null);
    setMessages([]);
    clearStream();
    clearToolCalls();
    disconnect();
    setTimeout(() => connect('new'), 100);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return { sendMessage, loadSessions, loadMessages, deleteSession, newSession, connect, disconnect };
}
