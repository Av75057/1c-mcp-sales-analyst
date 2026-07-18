import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { formatNumber } from '@/shared/lib/utils';

export default function OverviewPage() {
  const [status, setStatus] = useState<any>(null);
  const [dashboards, setDashboards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/status').catch(() => ({ data: null })),
      api.get('/api/v2/dashboards?per_page=4').catch(() => ({ data: { dashboards: [] } })),
    ]).then(([s, d]) => {
      setStatus(s.data);
      setDashboards(d.data?.dashboards || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 rounded-lg animate-pulse" style={{ backgroundColor: 'var(--skeleton)', border: '1px solid var(--border)' }} />
          ))}
        </div>
        <div className="h-48 rounded-lg animate-pulse" style={{ backgroundColor: 'var(--skeleton)', border: '1px solid var(--border)' }} />
      </div>
    );
  }

  const linkCardStyle = {
    backgroundColor: 'var(--bg-card)',
    borderColor: 'var(--border)',
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📊 Главный дашборд</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Сводка по продажам, остаткам и активности</p>
      </div>

      {/* Метрики */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader><CardTitle className="text-sm uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Позиций на складе</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(status?.stock_count || 0)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Продаж за 30д</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(status?.sales_count || 0)}</div></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Выручка за 30д</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-success">{formatNumber(status?.sales_sum || 0)} ₽</div></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Инсайтов</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(status?.insights_count || 0)}</div></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Последние дашборды */}
        <Card className="col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>📚 Последние дашборды</CardTitle>
            <Link to="/library" className="text-sm" style={{ color: 'var(--brand)' }}>Все →</Link>
          </CardHeader>
          <CardContent>
            {dashboards.length === 0 && (
              <div className="text-center py-6" style={{ color: 'var(--text-muted)' }}>
                <p className="mb-2">Нет сохранённых дашбордов</p>
                <Link to="/library" className="text-sm" style={{ color: 'var(--brand)' }}>Создать первый →</Link>
              </div>
            )}
            {dashboards.length > 0 && (
              <div className="space-y-2">
                {dashboards.map((d: any) => (
                  <Link key={d.id} to={`/library/${d.id}`}
                    className="flex items-center justify-between p-3 rounded-lg transition-colors"
                    style={{ backgroundColor: 'var(--bg-page)' }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'var(--bg-page)'}>
                    <div>
                      <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{d.title}</div>
                      <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                        {d.charts?.length || 0} графиков · 👁 {d.view_count || 0}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {d.charts?.slice(0, 3).map((c: any) => (
                        <Badge key={c.id} variant="secondary">{c.chart_config?.chart_type}</Badge>
                      ))}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Статус системы */}
        <Card>
          <CardHeader><CardTitle>🔧 Статус</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>1С:УНФ</span>
              <Badge variant={status?.c1_connected ? 'success' : 'error'}>
                {status?.c1_connected ? 'Доступна' : 'Недоступна'}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>DeepSeek AI</span>
              <Badge variant={status?.deepseek_key ? 'success' : 'secondary'}>
                {status?.deepseek_key ? 'Ключ есть' : 'Нет ключа'}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Режим</span>
              <Badge variant={status?.mock_mode ? 'warning' : 'success'}>
                {status?.mock_mode ? 'Мок' : 'Реальная 1С'}
              </Badge>
            </div>
            {status?.c1_url && (
              <div className="text-xs truncate mt-2" style={{ color: 'var(--text-muted)' }}>{status.c1_url}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Быстрые ссылки */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <a href="/chat"
          className="flex items-center gap-3 p-4 rounded-lg border transition-colors hover:brightness-110"
          style={linkCardStyle}>
          <span className="text-2xl">💬</span>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>AI Чат</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Задать вопрос о данных</div>
          </div>
        </a>
        <a href="/library"
          className="flex items-center gap-3 p-4 rounded-lg border transition-colors hover:brightness-110"
          style={linkCardStyle}>
          <span className="text-2xl">📚</span>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Библиотека</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Сохранённые дашборды</div>
          </div>
        </a>
        <Link to="/dashboards/new"
          className="flex items-center gap-3 p-4 rounded-lg border transition-colors hover:brightness-110"
          style={linkCardStyle}>
          <span className="text-2xl">📊</span>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Конструктор</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Создать новый дашборд</div>
          </div>
        </Link>
        <a href="/search"
          className="flex items-center gap-3 p-4 rounded-lg border transition-colors hover:brightness-110"
          style={linkCardStyle}>
          <span className="text-2xl">🔍</span>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Поиск</div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Найти дашборды</div>
          </div>
        </a>
      </div>
    </div>
  );
}
