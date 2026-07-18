import { useState, useEffect } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';

export default function StatusPage() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/status')
      .then((r) => setStatus(r.data))
      .catch(() => setStatus(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>🔧 Статус системы</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Состояние сервисов и метрики</p>
      </div>

      {loading && <div className="h-32 border rounded-lg animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }} />}

      {!loading && !status && (
        <Card><CardContent className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}>Не удалось загрузить статус</CardContent></Card>
      )}

      {status && (
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle>1С:УНФ</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>Статус</span><Badge variant={status.c1_connected ? 'success' : 'error'}>{status.c1_connected ? 'Доступна' : 'Недоступна'}</Badge></div>
              {(status as any).c1_url && <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>URL</span><span className="text-xs" style={{ color: 'var(--text-primary)' }}>{(status as any).c1_url}</span></div>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Данные</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>Товаров на складе</span><span style={{ color: 'var(--text-primary)' }}>{status.stock_count || 0}</span></div>
              <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>Продаж (30д)</span><span style={{ color: 'var(--text-primary)' }}>{status.sales_count || 0}</span></div>
              <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>Выручка (30д)</span><span style={{ color: 'var(--text-primary)' }}>{(status.sales_sum || 0).toLocaleString()} ₽</span></div>
              <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>Инсайтов</span><span style={{ color: 'var(--text-primary)' }}>{status.insights_count || 0}</span></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Кэш</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm"><span style={{ color: 'var(--text-secondary)' }}>Режим данных</span><Badge variant={status.mock_mode ? 'warning' : 'success'}>{status.mock_mode ? 'Мок' : 'Реальная 1С'}</Badge></div>
            </CardContent>
          </Card>

          {status.modules && (
            <Card>
              <CardHeader><CardTitle>Модули</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {Object.entries(status.modules).map(([k, v]: [string, any]) => (
                    <div key={k} className="flex justify-between text-sm">
                      <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                      <Badge variant={v ? 'success' : 'error'}>{v ? '✓' : '✗'}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
