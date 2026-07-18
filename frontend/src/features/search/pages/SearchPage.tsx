import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { searchApi } from '../api/searchApi';
import { api } from '@/shared/lib/api';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';

const SUGGESTIONS = [
  { query: 'продажи', label: '📈 Продажи' },
  { query: 'остатки', label: '📦 Остатки' },
  { query: 'топ товаров', label: '🏆 Топ товаров' },
  { query: 'шоколад', label: '🍫 Номенклатура' },
  { query: 'клиенты', label: '🏢 Клиенты' },
  { query: 'abc', label: '📊 ABC анализ' },
];

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState<'dashboards' | 'nomenclature'>('dashboards');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const doSearch = useCallback(async () => {
    if (!query.trim()) {
      setResults([]);
      setHasSearched(false);
      return;
    }
    setIsLoading(true);
    try {
      if (tab === 'dashboards') {
        const data = await searchApi.ftsSearch(query);
        setResults(data.results || []);
      } else {
        const { data } = await api.post('/api/search/nomenclature', {
          query, strategy: 'hybrid', page: 1, limit: 20,
        });
        setResults(data?.results || data?.items || []);
      }
      setHasSearched(true);
    } catch (e) {
      console.warn('Search error:', e);
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsLoading(false);
    }
  }, [query, tab]);

  useEffect(() => {
    const timer = setTimeout(doSearch, 300);
    return () => clearTimeout(timer);
  }, [doSearch]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>🔍 Поиск</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Поиск по дашбордам и номенклатуре 1С</p>
        </div>
      </div>

      {/* Search input */}
      <div className="relative mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Поиск..."
          className="w-full rounded-xl px-5 py-3.5 text-base outline-none focus:border-brand-500 transition-colors pl-12"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
          autoFocus
        />
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg" style={{ color: 'var(--text-secondary)' }}>🔍</span>
        {isLoading && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2">
            <span className="animate-spin inline-block w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full" />
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        <button
          onClick={() => setTab('dashboards')}
          className={`px-4 py-1.5 rounded-lg text-sm transition-colors ${tab === 'dashboards' ? 'bg-brand-600 text-white' : ''}`}
          style={tab !== 'dashboards' ? { backgroundColor: 'var(--bg-card)', color: 'var(--text-secondary)' } : undefined}
          onMouseEnter={(e) => { if (tab !== 'dashboards') e.currentTarget.style.color = 'var(--text-primary)'; }}
          onMouseLeave={(e) => { if (tab !== 'dashboards') e.currentTarget.style.color = 'var(--text-secondary)'; }}
        >📚 Дашборды</button>
        <button
          onClick={() => setTab('nomenclature')}
          className={`px-4 py-1.5 rounded-lg text-sm transition-colors ${tab === 'nomenclature' ? 'bg-brand-600 text-white' : ''}`}
          style={tab !== 'nomenclature' ? { backgroundColor: 'var(--bg-card)', color: 'var(--text-secondary)' } : undefined}
          onMouseEnter={(e) => { if (tab !== 'nomenclature') e.currentTarget.style.color = 'var(--text-primary)'; }}
          onMouseLeave={(e) => { if (tab !== 'nomenclature') e.currentTarget.style.color = 'var(--text-secondary)'; }}
        >📦 Номенклатура</button>
      </div>

      {/* Suggestions */}
      {!hasSearched && !query && (
        <div>
          <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>Популярные запросы:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button key={s.query} onClick={() => setQuery(s.query)}
                className="px-4 py-2 border rounded-lg text-sm hover:border-brand-500 transition-colors"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
                onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--text-primary)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}>
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center gap-3 py-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <span className="animate-spin inline-block w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full" />
          Поиск...
        </div>
      )}

      {/* Results */}
      {hasSearched && (
        <div>
          {!isLoading && results.length === 0 && (
            <div className="text-center py-16">
              <div className="text-4xl mb-3">🔍</div>
              <h2 className="text-lg mb-1" style={{ color: 'var(--text-primary)' }}>Ничего не найдено</h2>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Попробуйте изменить поисковый запрос</p>
            </div>
          )}

          {results.length > 0 && (
            <div>
              <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>Найдено: {results.length}</p>
              <div className="space-y-2">
                {results.map((r: any, i: number) => {
                  const id = r.dashboard_id || r.id || r.nomenclature_id || i;
                  const title = r.title || r.name || r.nomenclature || '-';
                  const desc = r.description || '';
                  const tags = r.tags ? String(r.tags) : r.group || '';
                  const link = r.dashboard_id ? `/library/${r.dashboard_id}` : null;
                  const content = (
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 style={{ color: 'var(--text-primary)' }} className="font-medium">{title}</h3>
                        {desc && <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{desc}</p>}
                        {r.article && <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>Арт: {r.article}</p>}
                      </div>
                      <div className="flex gap-1 ml-3 flex-wrap shrink-0">
                        {tags && <Badge variant="secondary">{tags}</Badge>}
                        {r.price && <Badge variant="success">{(r.price || 0).toLocaleString()} ₽</Badge>}
                      </div>
                    </div>
                  );
                  return link ? (
                    <Link key={id} to={link}
                      className="block border rounded-lg p-4 hover:border-brand-500 transition-colors"
                      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
                      {content}
                    </Link>
                  ) : (
                    <div key={id}
                      className="border rounded-lg p-4"
                      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
                      {content}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
