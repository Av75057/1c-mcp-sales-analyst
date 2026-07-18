import React from 'react';
import { Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { summaryApi, type ExecutiveSummary } from '../api/summaryApi';
import { MarkdownRenderer } from '@/shared/components/MarkdownRenderer';

interface AISummaryProps {
  period: string;
  organization?: string;
}

function SummarySkeleton() {
  return (
    <div className="rounded-xl border p-5 animate-pulse"
      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
      <div className="flex items-center mb-4">
        <div className="w-9 h-9 rounded-lg mr-3" style={{ backgroundColor: 'var(--skeleton)' }} />
        <div className="h-5 w-24 rounded" style={{ backgroundColor: 'var(--skeleton)' }} />
      </div>
      <div className="space-y-2">
        <div className="h-4 rounded w-3/4" style={{ backgroundColor: 'var(--skeleton)' }} />
        <div className="h-4 rounded w-1/2" style={{ backgroundColor: 'var(--skeleton)' }} />
        <div className="h-4 rounded w-5/6" style={{ backgroundColor: 'var(--skeleton)' }} />
      </div>
    </div>
  );
}

export const AISummary: React.FC<AISummaryProps> = React.memo(({ period, organization }) => {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['executive_summary', period, organization],
    queryFn: () => summaryApi.generate(period, organization),
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });

  if (isLoading) return <SummarySkeleton />;

  if (isError || !data) {
    return (
      <div className="rounded-xl border p-5" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-primary)' }}>
          <AlertCircle className="w-5 h-5 text-red-500" />
          Не удалось загрузить AI-анализ
        </div>
        <button onClick={() => refetch()} className="mt-2 text-xs underline" style={{ color: 'var(--text-secondary)' }}>
          Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border p-5"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border)',
      }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ backgroundColor: 'var(--brand)' }}>
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>AI-анализ</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {data.cache_status === 'hit' ? '⚡ Из кэша' : data.cache_status === 'fallback' ? '📡 Базовый анализ' : '✨ Сгенерировано'}
              {data.tokens_used > 0 && ` • ${data.tokens_used} токенов`}
            </p>
          </div>
        </div>
        <button onClick={() => refetch()} disabled={isFetching}
          className="p-2 rounded-lg transition-colors hover:brightness-110"
          style={{ color: 'var(--text-muted)' }}>
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <MarkdownRenderer content={data.summary_text} />

      {data.anomalies.length > 0 && (
        <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>
          <h4 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>⚠️ Требует внимания:</h4>
          {data.anomalies.map((a, i) => (
            <p key={i} className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{a}</p>
          ))}
        </div>
      )}

      {data.recommendations.length > 0 && (
        <div className="mt-3 p-3 rounded-lg" style={{ backgroundColor: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)' }}>
          <h4 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>🎯 Рекомендации:</h4>
          {data.recommendations.map((r, i) => (
            <p key={i} className="text-xs mt-0.5">{i + 1}. {r}</p>
          ))}
        </div>
      )}
    </div>
  );
});

AISummary.displayName = 'AISummary';
