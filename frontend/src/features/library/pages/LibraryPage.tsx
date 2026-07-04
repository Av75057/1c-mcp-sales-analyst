import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useDashboards } from '../hooks/useDashboards';
import type { ListFilters } from '@/shared/types/dashboard';
import { formatDate, formatNumber } from '@/shared/lib/utils';

export default function LibraryPage() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [chartType, setChartType] = useState('');

  const filters: ListFilters = useMemo(() => ({
    search,
    page,
    per_page: 20,
    is_favorite: favoriteOnly || undefined,
  }), [search, page, favoriteOnly]);

  const { data, isLoading, error } = useDashboards(filters);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">📚 Библиотека дашбордов</h1>
          <p className="text-[#6b7280] text-sm mt-1">Сохранённые дашборды и аналитика</p>
        </div>
        <a
          href="/dashboards"
          className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm transition-colors inline-block"
        >
          + Создать
        </a>
      </div>

      {/* Фильтры */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="🔍 Поиск по названию, описанию, тегам..."
          className="flex-1 bg-[#1a1d23] border border-[#2d3139] rounded-lg px-4 py-2 text-sm text-white outline-none focus:border-brand-500"
        />
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
          className="bg-[#1a1d23] border border-[#2d3139] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-brand-500"
        >
          <option value="">Все типы</option>
          <option value="bar">Bar</option>
          <option value="line">Line</option>
          <option value="pie">Pie</option>
          <option value="heatmap">Heatmap</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-[#9ca3af] cursor-pointer">
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
        <div className="bg-[#1a1d23] border border-[#2d3139] rounded-lg p-3 text-center">
          <div className="text-[#6b7280] text-xs">Дашбордов</div>
          <div className="text-white font-bold text-lg">{data?.total || 0}</div>
        </div>
        <div className="bg-[#1a1d23] border border-[#2d3139] rounded-lg p-3 text-center">
          <div className="text-[#6b7280] text-xs">Просмотров</div>
          <div className="text-white font-bold text-lg">
            {formatNumber(data?.dashboards?.reduce((s, d) => s + (d.view_count || 0), 0) || 0)}
          </div>
        </div>
      </div>

      {/* Список */}
      {isLoading && (
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-[#1a1d23] border border-[#2d3139] rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-[#2d3139] rounded w-3/4 mb-3" />
              <div className="h-3 bg-[#2d3139] rounded w-1/2 mb-2" />
              <div className="h-3 bg-[#2d3139] rounded w-2/3" />
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
          <h2 className="text-xl text-white mb-2">Библиотека пуста</h2>
          <p className="text-[#6b7280] mb-4">Сохраните дашборд из AI Чата или создайте вручную</p>
          <Link to="/chat" className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Перейти в AI Чат
          </Link>
        </div>
      )}

      {data?.dashboards && data.dashboards.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.dashboards.map((dashboard) => (
              <Link
                key={dashboard.id}
                to={`/library/${dashboard.id}`}
                className="bg-[#1a1d23] border border-[#2d3139] rounded-lg p-4 hover:border-brand-500 transition-colors group block"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-white font-medium truncate flex-1">{dashboard.title || 'Без названия'}</h3>
                  <div className="flex gap-1 ml-2">
                    {dashboard.is_favorite && <span className="text-warning">⭐</span>}
                    <span className={`text-xs px-1.5 py-0.5 rounded ${dashboard.is_public ? 'bg-success/20 text-success' : 'bg-[#2d3139] text-[#6b7280]'}`}>
                      {dashboard.is_public ? '🌐' : '🔒'}
                    </span>
                  </div>
                </div>

                <div className="flex gap-1 mb-2 flex-wrap">
                  {dashboard.charts?.map((c) => (
                    <span key={c.id} className="text-xs bg-[#2d3139] text-[#9ca3af] px-1.5 py-0.5 rounded">
                      {c.chart_config?.chart_type || '?'}
                    </span>
                  ))}
                </div>

                <div className="text-sm text-[#6b7280]">
                  {dashboard.charts?.length || 0} графиков · 👁 {dashboard.view_count || 0}
                </div>

                {dashboard.tags && dashboard.tags.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {dashboard.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="text-xs bg-brand-500/20 text-brand-500 px-1.5 py-0.5 rounded">{tag}</span>
                    ))}
                    {dashboard.tags.length > 3 && (
                      <span className="text-xs text-[#6b7280]">+{dashboard.tags.length - 3}</span>
                    )}
                  </div>
                )}

                <div className="text-xs text-[#4b5563] mt-2">
                  {formatDate(dashboard.updated_at)}
                </div>
              </Link>
            ))}
          </div>

          {/* Пагинация */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <span className="text-sm text-[#6b7280]">
                Страница {page} из {data.total_pages} (всего: {data.total})
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 bg-[#1a1d23] border border-[#2d3139] rounded-lg text-sm text-white disabled:opacity-50 hover:border-brand-500 transition-colors"
                >
                  ← Назад
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page >= data.total_pages}
                  className="px-3 py-1.5 bg-[#1a1d23] border border-[#2d3139] rounded-lg text-sm text-white disabled:opacity-50 hover:border-brand-500 transition-colors"
                >
                  Вперёд →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
