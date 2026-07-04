import { useState } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';

const ABC_COLORS: Record<string, string> = {
  A: 'bg-success/20 text-success',
  B: 'bg-warning/20 text-warning',
  C: 'bg-error/20 text-error',
};

const XYZ_COLORS: Record<string, string> = {
  X: 'bg-success/20 text-success',
  Y: 'bg-warning/20 text-warning',
  Z: 'bg-error/20 text-error',
};

export default function AbcXyzPage() {
  const [groupBy, setGroupBy] = useState('nomenclature');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRun = async () => {
    setIsLoading(true);
    setResult(null);
    try {
      const { data } = await api.get('/api/analysis/abc-xyz', {
        params: {
          date_from: new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10),
          date_to: new Date().toISOString().slice(0, 10),
          group_by: groupBy,
        },
      });
      setResult(data);
    } catch (err: any) {
      setResult({ error: err?.response?.data?.detail || 'Ошибка анализа' });
    } finally {
      setIsLoading(false);
    }
  };

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
              <select
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value)}
                className="w-full bg-[#1a1d23] border border-[#2d3139] rounded-lg p-2.5 text-white outline-none focus:border-brand-500"
              >
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
          {isLoading && (
            <Card><CardContent className="py-8 text-center text-[#6b7280] animate-pulse">Выполняется анализ...</CardContent></Card>
          )}

          {!result && !isLoading && (
            <Card><CardContent className="py-8 text-center text-[#6b7280]">
              <div className="text-3xl mb-2">📊</div>
              <p>Настройте параметры и запустите анализ</p>
            </CardContent></Card>
          )}

          {result?.error && (
            <Card><CardContent className="text-sm text-error">{result.error}</CardContent></Card>
          )}

          {result?.abc && !result.error && (
            <div className="space-y-4">
              {/* ABC матрица */}
              <Card>
                <CardHeader><CardTitle>ABC классификация</CardTitle></CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-[#6b7280] border-b border-[#2d3139]">
                          <th className="text-left py-2 px-2">Категория</th>
                          <th className="text-left py-2 px-2">Название</th>
                          <th className="text-right py-2 px-2">Выручка</th>
                          <th className="text-right py-2 px-2">Доля</th>
                          <th className="text-center py-2 px-2">ABC</th>
                          <th className="text-center py-2 px-2">XYZ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(result.abc || []).map((item: any, i: number) => (
                          <tr key={i} className="border-b border-[#2d3139] hover:bg-[#22262e]">
                            <td className="py-2 px-2 text-[#6b7280] text-xs">{i + 1}</td>
                            <td className="py-2 px-2 text-white">{item.name || item.nomenclature || '-'}</td>
                            <td className="py-2 px-2 text-right text-white">{item.revenue || item.sum || 0}</td>
                            <td className="py-2 px-2 text-right text-[#9ca3af]">{item.share ? `${(item.share * 100).toFixed(1)}%` : '-'}</td>
                            <td className="py-2 px-2 text-center">
                              <span className={`text-xs px-2 py-0.5 rounded ${ABC_COLORS[item.abc] || 'bg-[#2d3139]'}`}>{item.abc || '-'}</span>
                            </td>
                            <td className="py-2 px-2 text-center">
                              <span className={`text-xs px-2 py-0.5 rounded ${XYZ_COLORS[item.xyz] || 'bg-[#2d3139]'}`}>{item.xyz || '-'}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Легенда */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader><CardTitle>ABC</CardTitle></CardHeader>
                  <CardContent className="flex gap-3">
                    <Badge variant="success">A — 80% выручки</Badge>
                    <Badge variant="warning">B — 15% выручки</Badge>
                    <Badge variant="error">C — 5% выручки</Badge>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle>XYZ</CardTitle></CardHeader>
                  <CardContent className="flex gap-3">
                    <Badge variant="success">X — Стабильный спрос</Badge>
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
