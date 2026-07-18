import { useState } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';

const SCENARIO_TYPES = [
  { value: 'price_change', label: '💰 Изменение цены' },
  { value: 'promotion', label: '🎉 Промо-акция' },
  { value: 'purchase_change', label: '📦 Изменение закупок' },
  { value: 'employee_departure', label: '👋 Увольнение сотрудника' },
];

export default function WhatIfPage() {
  const [scenarioType, setScenarioType] = useState('price_change');
  const [entityName, setEntityName] = useState('');
  const [changePercent, setChangePercent] = useState(10);
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRun = async () => {
    setIsLoading(true);
    setResult(null);
    try {
      const params = new URLSearchParams();
      params.append('scenario_type', scenarioType);
      params.append('entity_name', entityName);
      if (scenarioType === 'price_change') params.append('change_percent', String(changePercent));
      if (scenarioType === 'promotion') params.append('discount_percent', String(changePercent));
      if (scenarioType === 'purchase_change') params.append('order_size_change_percent', String(changePercent));
      if (scenarioType === 'employee_departure') params.append('employee_name', entityName);
      const { data } = await api.post('/api/simulate', params.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      setResult(data);
    } catch (err: any) {
      setResult({ error: err?.response?.data?.detail || 'Ошибка симуляции' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>🔮 What-If анализ</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Симуляция бизнес-сценариев «Что если?»</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Параметры сценария</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>Тип сценария</label>
              <select
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value)}
                className="w-full rounded-lg p-2.5 outline-none focus:border-brand-500"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
              >
                {SCENARIO_TYPES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
                {scenarioType === 'price_change' ? 'Товар' :
                 scenarioType === 'promotion' ? 'Товар/категория' :
                 scenarioType === 'purchase_change' ? 'Поставщик' : 'Сотрудник'}
              </label>
              <input
                type="text"
                value={entityName}
                onChange={(e) => setEntityName(e.target.value)}
                placeholder="Название..."
                className="w-full rounded-lg p-2.5 outline-none focus:border-brand-500"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
              />
            </div>

            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
                {scenarioType === 'price_change' ? 'Изменение цены (%)' :
                 scenarioType === 'promotion' ? 'Скидка (%)' :
                 scenarioType === 'purchase_change' ? 'Изменение заказа (%)' : ''} {changePercent}%
              </label>
              <input
                type="range"
                min="-50"
                max="50"
                value={changePercent}
                onChange={(e) => setChangePercent(Number(e.target.value))}
                className="w-full accent-brand-500"
              />
              <div className="flex justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
                <span>-50%</span>
                <span>0%</span>
                <span>+50%</span>
              </div>
            </div>

            <Button onClick={handleRun} disabled={isLoading} className="w-full">
              {isLoading ? 'Симуляция...' : '🚀 Запустить симуляцию'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Результат</CardTitle></CardHeader>
          <CardContent>
            {isLoading && <div className="animate-pulse" style={{ color: 'var(--text-secondary)' }}>Симуляция выполняется...</div>}
            {!result && !isLoading && (
              <div className="text-center py-8" style={{ color: 'var(--text-secondary)' }}>
                <div className="text-3xl mb-2">🔮</div>
                <p className="text-sm">Настройте параметры и запустите симуляцию</p>
              </div>
            )}
            {result?.error && (
              <div className="text-sm text-error">{result.error}</div>
            )}
            {result && !result.error && (
              <div className="space-y-3">
                {/* Baseline vs Projected */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="border rounded-lg p-3 text-center" style={{ backgroundColor: 'var(--bg-page)', borderColor: 'var(--border)' }}>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Текущая выручка</div>
                    <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{(result.baseline?.revenue || 0).toLocaleString()} ₽</div>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Маржа: {(result.baseline?.margin || 0).toLocaleString()} ₽</div>
                  </div>
                  <div className="border rounded-lg p-3 text-center" style={{ backgroundColor: 'var(--bg-page)', borderColor: 'var(--border)' }}>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Прогноз</div>
                    <div className="text-lg font-bold text-brand-500">{(result.projected?.revenue || 0).toLocaleString()} ₽</div>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Маржа: {(result.projected?.margin || 0).toLocaleString()} ₽</div>
                  </div>
                </div>

                {/* Delta */}
                {result.delta && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-lg p-2 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Изменение выручки</div>
                      <div className={`text-sm font-bold ${(result.delta.revenue_percent || 0) >= 0 ? 'text-success' : 'text-error'}`}>
                        {result.delta.revenue_percent >= 0 ? '+' : ''}{result.delta.revenue_percent?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="rounded-lg p-2 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
                      <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Изменение маржи</div>
                      <div className={`text-sm font-bold ${(result.delta.margin_percent || 0) >= 0 ? 'text-success' : 'text-error'}`}>
                        {result.delta.margin_percent >= 0 ? '+' : ''}{result.delta.margin_percent?.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {result.recommendations && result.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>💡 Рекомендации</h4>
                    <ul className="space-y-1">
                      {result.recommendations.map((r: string, i: number) => (
                        <li key={i} className="text-sm rounded p-2" style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-page)' }}>• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Chart */}
                {result.chart_html && (
                  <div dangerouslySetInnerHTML={{ __html: result.chart_html }} className="mt-2" />
                )}

                {/* Confidence */}
                {result.confidence !== undefined && (
                  <div className="text-xs text-center" style={{ color: 'var(--text-secondary)' }}>
                    Уверенность прогноза: {Math.round(result.confidence * 100)}%
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
