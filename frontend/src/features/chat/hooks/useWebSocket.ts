import { useEffect, useRef, useCallback } from 'react';
import { useChatStore } from '../stores/chatStore';

export function useChatWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const pingTimer = useRef<ReturnType<typeof setInterval>>();
  const { appendStreamToken, clearStream, addToolCall, clearToolCalls, addMessage, setSessions, setMessages, setError, setCurrentSession, setCurrentChart, setTyping, setStreamingContent } = useChatStore();

  const connect = useCallback((sessionId?: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    const saved = localStorage.getItem('chat_session_id');
    const sid = sessionId || saved || 'new';
    const url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/${sid}`;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log('[Chat] Connected:', sid);
      setTyping(false); clearStream(); clearToolCalls(); setCurrentChart(null); setError(null);
      ws.current?.send(JSON.stringify({ type: 'get_sessions' }));
      const cur = useChatStore.getState().currentSessionId;
      if (!cur) return; // don't auto-load on new session
      clearInterval(pingTimer.current);
      pingTimer.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) ws.current?.send(JSON.stringify({ type: 'ping' }));
      }, 15000);
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'sessions':
            setSessions(data.sessions || []);
            if (!useChatStore.getState().currentSessionId && data.sessions?.length > 0) {
              const s = localStorage.getItem('chat_session_id');
              const hit = s && data.sessions.some((x: any) => x.id === s);
              if (hit) {
                const id = s!;
                localStorage.setItem('chat_session_id', id);
                ws.current?.send(JSON.stringify({ type: 'get_messages', session_id: id }));
              }
            }
            break;

          case 'messages':
            setMessages(data.messages || []);
            if (data.id) { localStorage.setItem('chat_session_id', data.id); setCurrentSession(data.id); }
            break;

          case 'token':
            appendStreamToken(data.content || '');
            break;

          case 'tool_call':
            addToolCall({ name: data.name || '', args: data.args || {} });
            break;

          case 'chart':
            addToolCall({ name: 'create_chart', args: data.config || {}, result: { image_base64: data.image_base64, chart_id: '' } });
            break;

          case 'chart_data':
            setCurrentChart({ 
              config: data.config || {}, 
              data: data.data || [], 
              image_base64: data.image_base64 || '', 
              status: 'ready',
              domain_id: data.domain_id || '',
              drilldown: data.drilldown || null,
            });
            break;

          case 'session_created':
            if (data.id) { localStorage.setItem('chat_session_id', data.id); setCurrentSession(data.id); }
            ws.current?.send(JSON.stringify({ type: 'get_sessions' }));
            break;

          case 'done': {
            const st = useChatStore.getState();
            if (st.streamingContent || st.currentToolCalls.length > 0 || st.currentChart) {
              addMessage({
                id: Date.now().toString(), role: 'assistant', content: st.streamingContent,
                tool_calls: [...st.currentToolCalls], chart: st.currentChart || undefined,
                chart_image: st.currentChart?.image_base64 || st.currentToolCalls.find(t => t.name === 'create_chart')?.result?.image_base64 || undefined,
                timestamp: new Date().toISOString(),
              });
            }
            clearStream(); clearToolCalls(); setCurrentChart(null); setTyping(false);
            break;
          }

          case 'error':
            setError(data.content || 'Ошибка');
            setTyping(false);
            break;
        }
      } catch (e) { console.warn('[Chat] parse error:', e); }
    };

    ws.current.onclose = () => {
      console.log('[Chat] Disconnected');
      clearInterval(pingTimer.current);
      reconnectTimer.current = setTimeout(() => connect(undefined), 3000);
    };

    ws.current.onerror = () => { setError('WebSocket connection error'); };
  }, []);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    clearInterval(pingTimer.current);
    ws.current?.close(); ws.current = null;
  }, []);

  const sendMessage = useCallback((text: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) { setError('Нет соединения'); return; }
    clearStream(); clearToolCalls(); setStreamingContent(''); setCurrentChart(null);
    addMessage({ id: Date.now().toString(), role: 'user', content: text, timestamp: new Date().toISOString() });
    setTyping(true);
    ws.current.send(JSON.stringify({ type: 'message', content: text }));
  }, []);

  const loadSessions = useCallback(() => { ws.current?.send(JSON.stringify({ type: 'get_sessions' })); }, []);
  const loadMessages = useCallback((id: string) => { setCurrentSession(id); ws.current?.send(JSON.stringify({ type: 'get_messages', session_id: id })); }, []);
  const deleteSession = useCallback((id: string) => { ws.current?.send(JSON.stringify({ type: 'delete_session', session_id: id })); }, []);
  const newSession = useCallback(() => { localStorage.removeItem('chat_session_id'); setCurrentSession(null); setMessages([]); clearStream(); clearToolCalls(); disconnect(); setTimeout(() => connect('new'), 100); }, []);

  useEffect(() => { connect(); return () => { disconnect(); clearInterval(pingTimer.current); }; }, []);

  return { sendMessage, loadSessions, loadMessages, deleteSession, newSession, connect, disconnect };
}
