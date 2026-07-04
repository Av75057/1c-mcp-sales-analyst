import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDashboard } from '@/features/library/hooks/useDashboards';
import { api } from '@/shared/lib/api';
import { ChartRenderer } from '@/shared/components/charts/ChartRenderer';
import { formatDate } from '@/shared/lib/utils';

export default function DashboardViewPage() {
  const { id } = useParams<{ id: string }>();
  const { data: initialData, isLoading, error } = useDashboard(id!);
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    if (!initialData) return;
    // Проверяем, есть ли данные, если нет — обновляем
    const hasData = initialData.charts?.some((c: any) => c.data?.length > 0);
    if (hasData) {
      setDashboard(initialData);
    } else {
      api.post(`/api/v2/dashboards/${id}/refresh`).then((r) => {
        setDashboard(r.data?.dashboard || initialData);
      }).catch(() => {
        setDashboard(initialData);
      });
    }
  }, [initialData, id]);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-[#2d3139] rounded w-1/3" />
        <div className="grid grid-cols-2 gap-4">
          {[1,2].map(i => <div key={i} className="h-64 bg-[#2d3139] rounded" />)}
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="text-center py-20">
        <div className="text-4xl mb-4">🔗</div>
        <h2 className="text-xl text-white mb-2">Дашборд не найден</h2>
        <p className="text-[#6b7280] mb-4">Дашборд был удалён или у вас нет доступа</p>
        <Link to="/library" className="text-brand-500 hover:text-brand-400">← Вернуться в библиотеку</Link>
      </div>
    );
  }

  return (
    <div>
      <nav className="text-sm text-[#6b7280] mb-4">
        <Link to="/library" className="hover:text-white transition-colors">Библиотека</Link>
        <span className="mx-2">/</span>
        <span className="text-white">{dashboard.title}</span>
      </nav>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{dashboard.title}</h1>
          {dashboard.description && (
            <p className="text-[#6b7280] mt-1">{dashboard.description}</p>
          )}
          <div className="flex gap-4 mt-2 text-sm text-[#6b7280]">
            <span>📅 {formatDate(dashboard.created_at)}</span>
            <span>👁 {dashboard.view_count} просмотров</span>
            {dashboard.is_public && <span className="text-success">🌐 Публичный</span>}
          </div>
        </div>
      </div>

      {dashboard.tags?.length > 0 && (
        <div className="flex gap-1 mb-4">
          {dashboard.tags.map((tag: string) => (
            <span key={tag} className="text-xs bg-brand-500/20 text-brand-500 px-2 py-0.5 rounded">{tag}</span>
          ))}
        </div>
      )}

      {/* Charts — используем inline style вместо col-span */}
      <div className="flex flex-wrap gap-4">
        {(dashboard.charts || []).map((chart: any) => {
          const w = chart.position?.w || 6;
          const widthPct = Math.round((w / 12) * 100);
          return (
            <div
              key={chart.id}
              style={{ width: `calc(${widthPct}% - 12px)`, minWidth: 300 }}
              className="bg-[#1a1d23] border border-[#2d3139] rounded-lg p-4 flex-1"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white font-medium truncate">{chart.title || 'График'}</h3>
                <span className="text-xs bg-[#2d3139] text-[#9ca3af] px-2 py-0.5 rounded ml-2 whitespace-nowrap">
                  {chart.chart_config?.chart_type || '?'}
                </span>
              </div>
              <div style={{ height: Math.max(200, (chart.position?.h || 4) * 60) }}>
                {chart.data?.length > 0 ? (
                  <ChartRenderer
                    config={chart.chart_config}
                    data={chart.data}
                    height={Math.max(200, (chart.position?.h || 4) * 60)}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-[#6b7280] text-sm">
                    Нет данных за выбранный период
                  </div>
                )}
              </div>
              <div className="text-xs text-[#6b7280] mt-2">
                {chart.data?.length || 0} записей
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
