import { useEffect, useRef } from 'react';
import { useChatStore } from '../stores/chatStore';
import { MessageBubble } from './MessageBubble';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';

interface ChatWindowProps {
  onSendMessage: (text: string) => void;
}

export function ChatWindow({ onSendMessage }: ChatWindowProps) {
  const { messages, isTyping, streamingContent, currentToolCalls, error } = useChatStore();
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputRef.current?.value.trim();
    if (!text) return;
    onSendMessage(text);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 p-3 border border-[#2d3139] rounded-lg bg-[#0f1117]" style={{ maxHeight: 'calc(100vh - 280px)' }}>
        {messages.length === 0 && !isTyping && (
          <div className="text-center py-10 text-[#6b7280]">
            <div className="text-3xl mb-2">💬</div>
            <p className="text-lg mb-1">AI Аналитик 1С</p>
            <p className="text-sm">Задайте вопрос о продажах, остатках или клиентах</p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {['Покажи продажи за месяц', 'Топ-10 товаров', 'Остатки на складах', 'ABC анализ'].map((q) => (
                <button
                  key={q}
                  onClick={() => { onSendMessage(q); }}
                  className="px-3 py-1.5 bg-[#1a1d23] border border-[#2d3139] rounded-lg text-sm text-[#9ca3af] hover:text-white hover:border-brand-500 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Streaming message */}
        {isTyping && (streamingContent || currentToolCalls.length > 0) && (
          <div className="flex justify-start">
            <div className="bg-[#1a1d23] border border-[#2d3139] rounded-lg p-3 max-w-[80%]">
              {streamingContent && (
                <p className="text-sm text-[#e5e7eb] whitespace-pre-wrap">{streamingContent}</p>
              )}
              {currentToolCalls.map((tc, i) => (
                <div key={i} className="text-xs text-[#6b7280] mt-1">
                  🔧 {tc.name}({JSON.stringify(tc.args, null, 1).slice(0, 100)})
                  {tc.result?.image_base64 && (
                    <img src={`data:image/png;base64,${tc.result.image_base64}`} alt="Chart" className="mt-2 rounded-lg max-w-full" style={{ maxHeight: 300 }} />
                  )}
                </div>
              ))}
              <span className="inline-block w-2 h-4 bg-brand-500 animate-pulse ml-1" />
            </div>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-3 text-error text-sm">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          placeholder="Задайте вопрос о данных..."
          className="flex-1 bg-[#1a1d23] border border-[#2d3139] rounded-lg px-4 py-2.5 text-sm text-white outline-none focus:border-brand-500 transition-colors"
          disabled={isTyping}
        />
        <Button type="submit" disabled={isTyping} size="lg">
          {isTyping ? '...' : '→'}
        </Button>
      </form>
    </div>
  );
}
