import { useCallback } from 'react';
import type { Message } from '../stores/chatStore';
import { Badge } from '@/shared/components/ui/Badge';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
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
      <div className={`rounded-lg p-3 max-w-[80%] ${isUser ? 'bg-brand-600 text-white' : 'bg-[#1a1d23] border border-[#2d3139]'}`}>
        {message.content && (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        )}

        {message.tool_calls?.map((tc, i) => (
          <div key={i} className="mt-2">
            {tc.name === 'create_chart' && (
              <div>
                {tc.result?.image_base64 && (
                  <img
                    src={`data:image/png;base64,${tc.result.image_base64}`}
                    alt="Chart"
                    className="rounded-lg max-w-full cursor-pointer hover:opacity-90 transition-opacity"
                    style={{ maxHeight: 300 }}
                    onClick={() => window.open(`data:image/png;base64,${tc.result.image_base64}`, '_blank')}
                  />
                )}
                <div className="flex gap-1 mt-1">
                  <Badge variant="secondary">{tc.args?.chart_type as string || 'chart'}</Badge>
                  <button
                    onClick={handleSave}
                    className="text-xs text-brand-500 hover:text-brand-400 transition-colors"
                  >
                    💾 Сохранить
                  </button>
                </div>
              </div>
            )}
            {tc.name !== 'create_chart' && (
              <div className="text-xs text-[#6b7280] mt-1">
                🔧 {tc.name}
              </div>
            )}
          </div>
        ))}

        <div className={`text-xs mt-1 ${isUser ? 'text-white/60' : 'text-[#4b5563]'}`}>
          {new Date(message.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
