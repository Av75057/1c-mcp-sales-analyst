import { useState } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { formatNumber } from '@/shared/lib/utils';

const ABC_VARIANTS: Record<string, 'success' | 'warning' | 'error'> = { A: 'success', B: 'warning', C: 'error' };
const XYZ_VARIANTS: Record<string, 'success' | 'warning' | 'error'> = { X: 'success', Y: 'warning', Z: 'error' };

export default function AbcXyzPage() {
  const [groupBy, setGroupBy] = useState('nomenclature');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRun = async () => {
    setIsLoading(true);
    setResult(null);
    try {
      const to = new Date().toISOString().slice(0, 10);
      const from = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
      const { data } = await api.get('/api/analysis/abc-xyz', {
        params: { date_from: from, date_to: to, group_by: groupBy },
      });
      setResult(data);
    } catch (err: any) {
      setResult({ error: err?.response?.data?.detail || 'Ошибка анализа' });
    } finally {
      setIsLoading(false);
    }
  };

  const matrixKeys = result?.matrix ? Object.keys(result.matrix) : [];
  const recommendations = result?.recommendations || [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">📊 ABC/XYZ анализ</h1>
        <p className="text-sm text-[#6b7280] mt-1">Классификация товаров/клиентов по выручке и стабильности</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <CardHeader><CardTitle>Параметры</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm text-[#9ca3af] mb-1">Группировка</label>
              <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}
                className="w-full bg-[#1a1d23] border border-[#2d3139] rounded-lg p-2.5 text-white outline-none focus:border-brand-500">
                <option value="nomenclature">Товары</option>
                <option value="client">Клиенты</option>
                <option value="manager">Менеджеры</option>
              </select>
            </div>
            <Button onClick={handleRun} disabled={isLoading} className="w-full">
              {isLoading ? 'Анализ...' : '🚀 Запустить анализ'}
            </Button>
          </CardContent>
        </Card>

        <div className="col-span-2">
          {isLoading && <Card><CardContent className="py-8 text-center text-[#6b7280] animate-pulse">Выполняется анализ...</CardContent></Card>}

          {!result && !isLoading && (
            <Card><CardContent className="py-8 text-center text-[#6b7280]">
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
                      <div className="bg-[#0f1117] rounded-lg p-2 text-center">
                        <div className="text-xs text-[#6b7280]">Всего</div>
                        <div className="text-lg font-bold text-white">{formatNumber(result.summary.total_items || 0)}</div>
                      </div>
                      <div className="bg-[#0f1117] rounded-lg p-2 text-center">
                        <div className="text-xs text-[#6b7280]">Выручка</div>
                        <div className="text-lg font-bold text-white">{formatNumber(result.summary.total_revenue || 0)} ₽</div>
                      </div>
                      <div className="bg-[#0f1117] rounded-lg p-2 text-center">
                        <div className="text-xs text-[#6b7280]">Период</div>
                        <div className="text-sm font-bold text-white">{result.summary.period_from?.slice(0, 10)} — {result.summary.period_to?.slice(0, 10)}</div>
                      </div>
                      <div className="bg-[#0f1117] rounded-lg p-2 text-center">
                        <div className="text-xs text-[#6b7280]">Тип</div>
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
                          <div key={key} className={`bg-[#0f1117] rounded-lg p-3 text-center border ${(cell.count || 0) > 0 ? 'border-[#2d3139]' : 'border-transparent opacity-30'}`}>
                            <div className="text-lg font-bold text-white">{key}</div>
                            <div className="text-xs text-[#6b7280]">{cell.count || 0} шт.</div>
                            <div className="text-xs text-white">{formatNumber(cell.revenue || 0)} ₽</div>
                            <div className="text-xs text-[#6b7280]">{((cell.share || 0) * 100).toFixed(1)}%</div>
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
                        <li key={i} className="text-sm text-[#e5e7eb] bg-[#0f1117] rounded p-2">
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
