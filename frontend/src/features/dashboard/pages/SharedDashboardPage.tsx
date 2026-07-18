import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '@/shared/lib/api';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';

interface ShareData {
  title: string;
  description?: string;
  charts: any[];
  owner?: string;
  created_at?: string;
}

export default function SharedDashboardPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<ShareData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api.get(`/api/v3/share/${token}`)
      .then((resp) => setData(resp.data))
      .catch((err) => setError(err?.response?.status === 410 ? 'Срок действия ссылки истёк' : 'Дашборд не найден'))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-page)' }}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center text-center p-8" style={{ backgroundColor: 'var(--bg-page)' }}>
        <div>
          <div className="text-4xl mb-4">🔗</div>
          <h1 className="text-xl" style={{ color: 'var(--text-primary)' }}>{error}</h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Свяжитесь с владельцем дашборда для получения новой ссылки</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--bg-page)', color: 'var(--text-primary)' }}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8 border-b pb-6" style={{ borderColor: 'var(--border)' }}>
          <h1 className="text-2xl font-bold">📊 {data?.title || 'Дашборд'}</h1>
          {data?.description && <p className="mt-1" style={{ color: 'var(--text-secondary)' }}>{data.description}</p>}
          <div className="flex justify-center gap-4 mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
            <span>👤 {data?.owner || 'Пользователь'}</span>
            {data?.created_at && <span>📅 {new Date(data.created_at).toLocaleDateString()}</span>}
            <Badge variant="secondary">Публичный доступ</Badge>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          {(data?.charts || []).map((chart: any) => (
            <div key={chart.id} className={`col-span-${chart.position?.w || 6} border rounded-lg p-4`} style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <h3 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>{chart.title || 'График'}</h3>
              <div style={{ height: Math.max(200, (chart.position?.h || 4) * 60), backgroundColor: 'var(--bg-page)', color: 'var(--text-secondary)' }}
                   className="rounded-lg flex items-center justify-center">
                📊 Данные дашборда
              </div>
            </div>
          ))}
        </div>

        <div className="text-center text-xs mt-8 border-t pt-4" style={{ color: 'var(--text-muted)', borderColor: 'var(--border)' }}>
          Сгенерировано 1С Аналитиком · Данные из 1С:УНФ
        </div>
      </div>
    </div>
  );
}
