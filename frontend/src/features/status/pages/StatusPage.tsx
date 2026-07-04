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
        <h1 className="text-2xl font-bold text-white">🔧 Статус системы</h1>
        <p className="text-sm text-[#6b7280] mt-1">Состояние сервисов и метрики</p>
      </div>

      {loading && <div className="h-32 bg-[#1a1d23] border border-[#2d3139] rounded-lg animate-pulse" />}

      {!loading && !status && (
        <Card><CardContent className="py-8 text-center text-[#6b7280]">Не удалось загрузить статус</CardContent></Card>
      )}

      {status && (
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle>1С:УНФ</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm"><span className="text-[#6b7280]">Статус</span><Badge variant={status.c1_connected ? 'success' : 'error'}>{status.c1_connected ? 'Доступна' : 'Недоступна'}</Badge></div>
              {(status as any).c1_url && <div className="flex justify-between text-sm"><span className="text-[#6b7280]">URL</span><span className="text-white text-xs">{(status as any).c1_url}</span></div>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Данные</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm"><span className="text-[#6b7280]">Товаров на складе</span><span className="text-white">{status.stock_count || 0}</span></div>
              <div className="flex justify-between text-sm"><span className="text-[#6b7280]">Продаж (30д)</span><span className="text-white">{status.sales_count || 0}</span></div>
              <div className="flex justify-between text-sm"><span className="text-[#6b7280]">Выручка (30д)</span><span className="text-white">{(status.sales_sum || 0).toLocaleString()} ₽</span></div>
              <div className="flex justify-between text-sm"><span className="text-[#6b7280]">Инсайтов</span><span className="text-white">{status.insights_count || 0}</span></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Кэш</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm"><span className="text-[#6b7280]">Режим данных</span><Badge variant={status.mock_mode ? 'warning' : 'success'}>{status.mock_mode ? 'Мок' : 'Реальная 1С'}</Badge></div>
            </CardContent>
          </Card>

          {status.modules && (
            <Card>
              <CardHeader><CardTitle>Модули</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {Object.entries(status.modules).map(([k, v]: [string, any]) => (
                    <div key={k} className="flex justify-between text-sm">
                      <span className="text-[#6b7280]">{k}</span>
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
