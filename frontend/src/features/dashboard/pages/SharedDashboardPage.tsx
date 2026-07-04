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
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center text-center p-8">
        <div>
          <div className="text-4xl mb-4">🔗</div>
          <h1 className="text-xl text-white mb-2">{error}</h1>
          <p className="text-sm text-[#6b7280]">Свяжитесь с владельцем дашборда для получения новой ссылки</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e5e7eb] p-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8 border-b border-[#2d3139] pb-6">
          <h1 className="text-2xl font-bold">📊 {data?.title || 'Дашборд'}</h1>
          {data?.description && <p className="text-[#6b7280] mt-1">{data.description}</p>}
          <div className="flex justify-center gap-4 mt-2 text-sm text-[#6b7280]">
            <span>👤 {data?.owner || 'Пользователь'}</span>
            {data?.created_at && <span>📅 {new Date(data.created_at).toLocaleDateString()}</span>}
            <Badge variant="secondary">Публичный доступ</Badge>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          {(data?.charts || []).map((chart: any) => (
            <div key={chart.id} className={`col-span-${chart.position?.w || 6} bg-[#1a1d23] border border-[#2d3139] rounded-lg p-4`}>
              <h3 className="text-white font-medium mb-2">{chart.title || 'График'}</h3>
              <div style={{ height: Math.max(200, (chart.position?.h || 4) * 60) }}
                   className="bg-[#0f1117] rounded-lg flex items-center justify-center text-[#6b7280]">
                📊 Данные дашборда
              </div>
            </div>
          ))}
        </div>

        <div className="text-center text-xs text-[#4b5563] mt-8 border-t border-[#2d3139] pt-4">
          Сгенерировано 1С Аналитиком · Данные из 1С:УНФ
        </div>
      </div>
    </div>
  );
}
