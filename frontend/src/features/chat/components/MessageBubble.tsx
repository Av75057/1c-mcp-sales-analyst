import { useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../stores/chatStore';
import { ChatChartWidget } from './ChatChartWidget';
import { SuggestionChips } from './SuggestionChips';
import { Badge } from '@/shared/components/ui/Badge';

interface MessageBubbleProps {
  message: Message;
  onSuggestionClick?: (s: string) => void;
}

export function MessageBubble({ message, onSuggestionClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  const handleSave = useCallback(async () => {
    const chartToolCall = message.tool_calls?.find(t => t.name === 'create_chart' && t.result?.image_base64);
    if (!chartToolCall) return;
    const title = prompt('Название дашборда:', chartToolCall.args?.title || 'График из чата');
    if (!title) return;
    const tags = (prompt('Теги (через запятую):', 'чат') || 'чат').split(',').map(t => t.trim());
    const chartItem = {
      id: 'c' + Date.now(),
      title,
      chart_config: {
        chart_type: chartToolCall.args?.chart_type || 'bar',
        title,
        x_axis: { field: 'x', label: 'X', type: 'category' },
        y_axis: { field: 'y', label: 'Y', type: 'category' },
        series: [{ name: 'Значение', field: 'y', color: '#5470c6' }],
        onec_query: { entity: 'Document.РеализацияТоваровУслуг', fields: ['Сумма'], period: 'last_30_days' },
      },
      data: [],
      position: { x: 0, y: 0, w: 6, h: 4 },
      filter_bindings: [],
    };
    try {
      const resp = await fetch('/api/v2/dashboards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description: 'Сохранён из AI Чата', tags, charts: [chartItem] }),
      });
      if (resp.ok) alert('✅ Дашборд сохранён в библиотеку!');
      else alert('❌ Ошибка сохранения');
    } catch {
      alert('❌ Ошибка сети');
    }
  }, [message]);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`rounded-lg p-3 max-w-[80%] ${isUser ? 'bg-brand-600 text-white' : 'border'}`} style={!isUser ? { backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' } : undefined}>
        {message.content && (
          <div className="text-sm markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}

        {message.chart && (
          <ChatChartWidget chart={message.chart} messageId={message.id} onSuggestionClick={onSuggestionClick} />
        )}

        {message.tool_calls?.map((tc, i) => {
          const imgB64 = tc.result?.image_base64 as string | undefined;
          return (
          <div key={i} className="mt-2">
            {tc.name === 'create_chart' && !message.chart && (
              <div>
                {imgB64 && (
                  <img
                    src={`data:image/png;base64,${imgB64}`}
                    alt="Chart"
                    className="rounded-lg max-w-full cursor-pointer hover:opacity-90 transition-opacity"
                    style={{ maxHeight: 300 }}
                    onClick={() => window.open(`data:image/png;base64,${imgB64}`, '_blank')}
                  />
                )}
                <div className="flex gap-1 mt-1">
                  <Badge variant="secondary">{tc.args?.chart_type as string || 'chart'}</Badge>
                  <button
                    onClick={handleSave}
                    className="text-xs transition-colors"
                    style={{ color: 'var(--brand)' }}
                  >
                    💾 Сохранить
                  </button>
                </div>
              </div>
            )}
            {tc.name !== 'create_chart' && (
              <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                🔧 {tc.name}
              </div>
            )}
          </div>
          );
        })}

        {!isUser && message.suggestions && message.suggestions.length > 0 && (
          <SuggestionChips suggestions={message.suggestions} onClick={onSuggestionClick || (() => {})} />
        )}

        <div className={`text-xs mt-1 ${isUser ? 'text-white/60' : ''}`} style={!isUser ? { color: 'var(--text-muted)' } : undefined}>
          {new Date(message.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
