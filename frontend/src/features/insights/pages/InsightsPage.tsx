import { useState, useEffect } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { formatDateTime } from '@/shared/lib/utils';

interface Insight {
  title: string;
  text: string;
  type?: string;
  created_at?: string;
  metric?: string;
  value?: string;
  recommendation?: string;
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const r = await api.post('/api/insights/scan', null, { timeout: 15000 });
      setInsights(r.data?.insights || r.data || []);
    } catch (e: any) {
      console.warn('Insights fetch error:', e?.message || e);
      setInsights([]);
    } finally {
      setLoading(false);
    }
  };

  const typeVariant = (t?: string) => {
    const map: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
      positive: 'success',
      warning: 'warning',
      critical: 'error',
      info: 'default',
    };
    return map[t || ''] || 'default';
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>💡 Инсайты</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Автоматические аналитические заметки</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchInsights}>
          🔄 Обновить
        </Button>
      </div>

      {loading && (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-24 border rounded-lg animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }} />)}
        </div>
      )}

      {!loading && insights.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
            <div className="text-3xl mb-2">💡</div>
            <p>Нет инсайтов. Они появятся после анализа данных.</p>
          </CardContent>
        </Card>
      )}

      {insights.length > 0 && (
        <div className="space-y-3">
          {insights.map((insight, i) => (
            <Card key={i} className={`border-l-4 ${insight.type === 'critical' ? 'border-l-error' : insight.type === 'warning' ? 'border-l-warning' : 'border-l-info'}`}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium" style={{ color: 'var(--text-primary)' }}>{insight.title}</h3>
                  <div className="flex gap-2">
                    {insight.type && <Badge variant={typeVariant(insight.type)}>{insight.type}</Badge>}
                    {insight.created_at && (
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{formatDateTime(insight.created_at)}</span>
                    )}
                  </div>
                </div>
                <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{insight.text}</p>
                {insight.recommendation && (
                  <p className="text-sm text-brand-500 mt-1">💡 {insight.recommendation}</p>
                )}
                {insight.metric && insight.value && (
                  <div className="flex gap-4 mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                    <span>{insight.metric}: <strong style={{ color: 'var(--text-primary)' }}>{insight.value}</strong></span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
