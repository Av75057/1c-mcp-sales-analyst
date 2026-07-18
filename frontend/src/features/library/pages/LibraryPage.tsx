import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDashboards, useDeleteDashboard } from '../hooks/useDashboards';
import type { ListFilters } from '@/shared/types/dashboard';
import { formatDate, formatNumber } from '@/shared/lib/utils';
import { Dialog } from '@/shared/components/ui/Dialog';

export default function LibraryPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [chartType, setChartType] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const deleteMutation = useDeleteDashboard();

  const filters: ListFilters = useMemo(() => ({
    search,
    page,
    per_page: 20,
    is_favorite: favoriteOnly || undefined,
  }), [search, page, favoriteOnly]);

  const { data, isLoading, error } = useDashboards(filters);

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📚 Библиотека дашбордов</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Сохранённые дашборды и аналитика</p>
        </div>
        <Link
          to="/dashboards/new"
          className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm transition-colors inline-block"
        >
          + Создать
        </Link>
      </div>

      {/* Фильтры */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="🔍 Поиск по названию, описанию, тегам..."
          className="flex-1 rounded-lg px-4 py-2 text-sm outline-none focus:border-brand-500"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
        />
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
          className="rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
        >
          <option value="">Все типы</option>
          <option value="bar">Bar</option>
          <option value="line">Line</option>
          <option value="pie">Pie</option>
          <option value="heatmap">Heatmap</option>
        </select>
        <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: 'var(--text-secondary)' }}>
          <input
            type="checkbox"
            checked={favoriteOnly}
            onChange={(e) => { setFavoriteOnly(e.target.checked); setPage(1); }}
            className="w-4 h-4 accent-brand-500"
          />
          ⭐ Избранные
        </label>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="border rounded-lg p-3 text-center" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Дашбордов</div>
          <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{data?.total || 0}</div>
        </div>
        <div className="border rounded-lg p-3 text-center" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Просмотров</div>
          <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
            {formatNumber(data?.dashboards?.reduce((s, d) => s + (d.view_count || 0), 0) || 0)}
          </div>
        </div>
      </div>

      {/* Список */}
      {isLoading && (
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="border rounded-lg p-4 animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="h-4 rounded w-3/4 mb-3" style={{ backgroundColor: 'var(--skeleton)' }} />
              <div className="h-3 rounded w-1/2 mb-2" style={{ backgroundColor: 'var(--skeleton)' }} />
              <div className="h-3 rounded w-2/3" style={{ backgroundColor: 'var(--skeleton)' }} />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="bg-[#ef444422] border border-[#ef4444] rounded-lg p-4 text-[#ef4444] text-sm">
          Ошибка загрузки: {(error as any)?.message || 'Неизвестная ошибка'}
        </div>
      )}

      {data?.dashboards && data.dashboards.length === 0 && (
        <div className="text-center py-20">
          <div className="text-4xl mb-4">📚</div>
          <h2 className="text-xl mb-2" style={{ color: 'var(--text-primary)' }}>Библиотека пуста</h2>
          <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>Сохраните дашборд из AI Чата или создайте вручную</p>
          <Link to="/chat" className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Перейти в AI Чат
          </Link>
        </div>
      )}

      {data?.dashboards && data.dashboards.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.dashboards.map((dashboard) => (
              <div key={dashboard.id}
                className="border rounded-lg p-4 transition-colors group relative"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}
              >
                <Link to={`/library/${dashboard.id}`} className="block">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium truncate flex-1" style={{ color: 'var(--text-primary)' }}>{dashboard.title || 'Без названия'}</h3>
                  <div className="flex gap-1 ml-2">
                    {dashboard.is_favorite && <span className="text-warning">⭐</span>}
                    <span className={`text-xs px-1.5 py-0.5 rounded ${dashboard.is_public ? 'bg-success/20 text-success' : ''}`} style={!dashboard.is_public ? { backgroundColor: 'var(--border)', color: 'var(--text-secondary)' } : undefined}>
                      {dashboard.is_public ? '🌐' : '🔒'}
                    </span>
                  </div>
                </div>

                <div className="flex gap-1 mb-2 flex-wrap">
                  {dashboard.charts?.map((c) => (
                    <span key={c.id} className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                      {c.chart_config?.chart_type || '?'}
                    </span>
                  ))}
                </div>

                <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {dashboard.charts?.length || 0} графиков · 👁 {dashboard.view_count || 0}
                </div>

                {dashboard.tags && dashboard.tags.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {dashboard.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="text-xs bg-brand-500/20 text-brand-500 px-1.5 py-0.5 rounded">{tag}</span>
                    ))}
                    {dashboard.tags.length > 3 && (
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>+{dashboard.tags.length - 3}</span>
                    )}
                  </div>
                )}

                <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                  {formatDate(dashboard.updated_at)}
                </div>
                </Link>
                <button onClick={(e) => { e.preventDefault(); setDeleteTarget(dashboard.id); }}
                  className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center rounded opacity-0 group-hover:opacity-100 transition-opacity text-xs hover:bg-red-500/20 hover:text-red-500"
                  style={{ color: 'var(--text-muted)' }}>
                  ✕
                </button>
              </div>
            ))}
          </div>

          {/* Пагинация */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Страница {page} из {data.total_pages} (всего: {data.total})
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 border rounded-lg text-sm disabled:opacity-50 hover:border-brand-500 transition-colors"
                  style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
                >
                  ← Назад
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page >= data.total_pages}
                  className="px-3 py-1.5 border rounded-lg text-sm disabled:opacity-50 hover:border-brand-500 transition-colors"
                  style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
                >
                  Вперёд →
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Удалить дашборд?">
        <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>Дашборд будет безвозвратно удалён.</p>
        <div className="flex justify-end gap-2">
          <button onClick={() => setDeleteTarget(null)}
            className="px-4 py-2 rounded-lg border text-sm"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>Отмена</button>
          <button onClick={() => { if (deleteTarget) { deleteMutation.mutate(deleteTarget); setDeleteTarget(null); } }}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white"
            style={{ backgroundColor: 'var(--color-error, #ef4444)' }}>
            {deleteMutation.isPending ? 'Удаление...' : 'Удалить'}
          </button>
        </div>
      </Dialog>
    </>
  );
}
