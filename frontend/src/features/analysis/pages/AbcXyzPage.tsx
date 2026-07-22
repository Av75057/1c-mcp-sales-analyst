import { useState, useEffect } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { formatNumber } from '@/shared/lib/utils';

const _ABC_VARIANTS: Record<string, 'success' | 'warning' | 'error'> = { A: 'success', B: 'warning', C: 'error' };
const _XYZ_VARIANTS: Record<string, 'success' | 'warning' | 'error'> = { X: 'success', Y: 'warning', Z: 'error' };

const PERIOD_PRESETS = [
  { label: '30 дней', days: 30 }, { label: '90 дней', days: 90 },
  { label: 'Этот год', days: 0 }, { label: 'Всё время', days: 9999 },
];

export default function AbcXyzPage() {
  const [groupBy, setGroupBy] = useState('nomenclature');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [periodDays, setPeriodDays] = useState(30);
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  const run = (days: number, from?: string, to?: string) => {
    setIsLoading(true);
    setResult(null);
    const now = new Date();
    const toDate = to || now.toISOString().slice(0, 10);
    const fromDate = from || (
      days === 0 ? `${now.getFullYear()}-01-01` :
      days > 0 && days < 9000 ? new Date(now.getTime() - days * 86400000).toISOString().slice(0, 10) :
      '2020-01-01'
    );
    api.get('/api/analysis/abc-xyz', { params: { date_from: fromDate, date_to: toDate, group_by: groupBy } })
      .then(r => setResult(r.data))
      .catch(err => setResult({ error: err?.response?.data?.detail || 'Ошибка анализа' }))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => { if (!customFrom || !customTo) run(periodDays); }, [periodDays, groupBy]);

  const matrixKeys = result?.matrix ? Object.keys(result.matrix) : [];
  const recommendations = result?.recommendations || [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📊 ABC/XYZ анализ</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Классификация товаров/клиентов по выручке и стабильности</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <CardHeader><CardTitle>Параметры</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Период</label>
              <div className="flex flex-wrap gap-1 mb-2">
                {PERIOD_PRESETS.map(p => (
                  <button key={p.days} onClick={() => { setPeriodDays(p.days); setCustomFrom(''); setCustomTo(''); }}
                    className="px-2.5 py-1 text-xs font-medium rounded-md transition-colors"
                    style={periodDays === p.days && !customFrom ? { backgroundColor: 'var(--bg-active)', color: 'var(--text-primary)' } : { backgroundColor: 'var(--bg-card-hover)', color: 'var(--text-secondary)' }}>
                    {p.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1 text-xs">
                <input type="date" value={customFrom} onChange={e => { setCustomFrom(e.target.value); setPeriodDays(0); }}
                  className="flex-1 px-2 py-1.5 rounded border" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
                <span style={{ color: 'var(--text-muted)' }}>—</span>
                <input type="date" value={customTo} onChange={e => { setCustomTo(e.target.value); setPeriodDays(0); }}
                  className="flex-1 px-2 py-1.5 rounded border" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
                {customFrom && customTo && (
                  <button onClick={() => run(0, customFrom, customTo)}
                    className="px-2 py-1.5 rounded text-xs font-medium text-white"
                    style={{ backgroundColor: 'var(--brand)' }}>OK</button>
                )}
              </div>
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Группировка</label>
              <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}
                className="w-full rounded-lg p-2.5 outline-none focus:border-brand-500"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}>
                <option value="nomenclature">Товары</option>
                <option value="client">Клиенты</option>
                <option value="manager">Менеджеры</option>
              </select>
            </div>
            <Button onClick={() => run(periodDays)} disabled={isLoading} className="w-full">
              {isLoading ? 'Анализ...' : '🚀 Запустить анализ'}
            </Button>
          </CardContent>
        </Card>

        <div className="col-span-2">
          {isLoading && <Card><CardContent className="py-8 text-center animate-pulse" style={{ color: 'var(--text-secondary)' }}>Выполняется анализ...</CardContent></Card>}

          {!result && !isLoading && (
            <Card><CardContent className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
              <div className="text-3xl mb-2">📊</div>
              <p>Настройте параметры и запустите анализ</p>
            </CardContent></Card>
          )}

          {result?.error && <Card><CardContent className="text-sm text-error">{result.error}</CardContent></Card>}

          {result && !result.error && (
            <div className="space-y-4">
              {/* Summary */}
              {result.summary && (
                <Card>
                  <CardHeader><CardTitle>Сводка</CardTitle></CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-3">
                      <div className="rounded-lg p-2 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Всего</div>
                        <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(result.summary.total_items || 0)}</div>
                      </div>
                      <div className="rounded-lg p-2 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Выручка</div>
                        <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{formatNumber(result.summary.total_revenue || 0)} ₽</div>
                      </div>
                      <div className="rounded-lg p-2 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Период</div>
                        <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{result.summary.period_from?.slice(0, 10)} — {result.summary.period_to?.slice(0, 10)}</div>
                      </div>
                      <div className="rounded-lg p-2 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Тип</div>
                        <Badge variant="default">{result.summary.analysis_type === 'nomenclature' ? 'Товары' : result.summary.analysis_type === 'client' ? 'Клиенты' : 'Менеджеры'}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* ABC/XYZ Matrix */}
              {matrixKeys.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>Матрица ABC/XYZ</CardTitle></CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-2">
                      {matrixKeys.map((key) => {
                        const cell = result.matrix[key] || {};
                        return (
                          <div key={key} className={`rounded-lg p-3 text-center border ${(cell.count || 0) > 0 ? '' : 'border-transparent opacity-30'}`}
                            style={(cell.count || 0) > 0 ? { backgroundColor: 'var(--bg-page)', borderColor: 'var(--border)' } : { backgroundColor: 'var(--bg-page)' }}>
                            <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{key}</div>
                            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{cell.count || 0} шт.</div>
                            <div className="text-xs" style={{ color: 'var(--text-primary)' }}>{formatNumber(cell.revenue || 0)} ₽</div>
                            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{(cell.share || 0).toFixed(1)}%</div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Recommendations */}
              {recommendations.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>💡 Рекомендации</CardTitle></CardHeader>
                  <CardContent>
                    <ul className="space-y-1">
                      {recommendations.map((r: any, i: number) => (
                        <li key={i} className="text-sm rounded p-2" style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-page)' }}>
                          • {typeof r === 'string' ? r : r.description || r.action || r.recommendation || JSON.stringify(r)}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Legend */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader><CardTitle>ABC — выручка</CardTitle></CardHeader>
                  <CardContent className="flex gap-2 flex-wrap">
                    <Badge variant="success">A — 80%</Badge>
                    <Badge variant="warning">B — 15%</Badge>
                    <Badge variant="error">C — 5%</Badge>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle>XYZ — стабильность</CardTitle></CardHeader>
                  <CardContent className="flex gap-2 flex-wrap">
                    <Badge variant="success">X — Стабильный</Badge>
                    <Badge variant="warning">Y — Колебания</Badge>
                    <Badge variant="error">Z — Неравномерный</Badge>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
