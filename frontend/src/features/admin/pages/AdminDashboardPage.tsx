import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api/adminApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { formatNumber } from '@/shared/lib/utils';

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(30),
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>⚙️ Админ-панель</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Статистика использования дашбордов</p>
      </div>

      {isLoading && (
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => (
            <div key={i} className="border rounded-lg p-4 animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="h-3 rounded w-1/2 mb-2" style={{ backgroundColor: 'var(--skeleton)' }} />
              <div className="h-6 rounded w-1/3" style={{ backgroundColor: 'var(--skeleton)' }} />
            </div>
          ))}
        </div>
      )}

      {stats && (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader><CardTitle className="text-sm" style={{ color: 'var(--text-secondary)' }}>Дашбордов</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(stats.total_dashboards || 0)}</div></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-sm" style={{ color: 'var(--text-secondary)' }}>Активных</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold text-success">{formatNumber(stats.active_dashboards || 0)}</div></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-sm" style={{ color: 'var(--text-secondary)' }}>Просмотров</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(stats.total_views || 0)}</div></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-sm" style={{ color: 'var(--text-secondary)' }}>Экспортов</CardTitle></CardHeader>
              <CardContent><div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(stats.total_exports || 0)}</div></CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Top dashboards */}
            <Card>
              <CardHeader><CardTitle>🏆 Топ дашбордов</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(stats.top_dashboards || []).slice(0, 5).map((d, i) => (
                    <div key={d.id} className="flex items-center justify-between text-sm">
                      <span className="truncate flex-1" style={{ color: 'var(--text-primary)' }}>{i+1}. {d.title}</span>
                      <span className="ml-2" style={{ color: 'var(--text-secondary)' }}>👁 {d.views}</span>
                    </div>
                  ))}
                  {(!stats.top_dashboards || stats.top_dashboards.length === 0) && (
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Нет данных</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Top tags */}
            <Card>
              <CardHeader><CardTitle>🏷️ Популярные теги</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(stats.top_tags || []).slice(0, 10).map((t) => (
                    <div key={t.tag} className="flex items-center justify-between text-sm">
                      <Badge>{t.tag}</Badge>
                      <span style={{ color: 'var(--text-secondary)' }}>{t.count}</span>
                    </div>
                  ))}
                  {(!stats.top_tags || stats.top_tags.length === 0) && (
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Нет данных</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Chart types */}
            <Card>
              <CardHeader><CardTitle>📊 Типы графиков</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(stats.chart_types || []).map((ct) => (
                    <div key={ct.type} className="flex items-center justify-between text-sm">
                      <span style={{ color: 'var(--text-primary)' }}>{ct.type}</span>
                      <Badge variant="secondary">{ct.count}</Badge>
                    </div>
                  ))}
                  {(!stats.chart_types || stats.chart_types.length === 0) && (
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Нет данных</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Feedback */}
            <Card>
              <CardHeader><CardTitle>💬 Feedback</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {stats.feedback_summary ? (
                    <>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-success">👍 Положительных</span>
                        <span style={{ color: 'var(--text-primary)' }}>{stats.feedback_summary.positive || 0}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-error">👎 Отрицательных</span>
                        <span style={{ color: 'var(--text-primary)' }}>{stats.feedback_summary.negative || 0}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm font-bold">
                        <span style={{ color: 'var(--text-primary)' }}>Удовлетворённость</span>
                        <span className="text-brand-500">{((stats.feedback_summary.satisfaction_rate || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Нет данных</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Cache stats info */}
          <Card className="mt-4">
            <CardHeader><CardTitle>⚡ Кэш</CardTitle></CardHeader>
            <CardContent>
              <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                <p>Метаданные 1С: TTL 1 час · Результаты запросов: TTL 15 мин</p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
