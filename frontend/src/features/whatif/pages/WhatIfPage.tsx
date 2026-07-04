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
      const payload: any = { scenario_type: scenarioType, entity_name: entityName };
      if (scenarioType === 'price_change') payload.change_percent = changePercent;
      if (scenarioType === 'promotion') payload.discount_percent = changePercent;
      const { data } = await api.post('/api/simulate', payload);
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
        <h1 className="text-2xl font-bold text-white">🔮 What-If анализ</h1>
        <p className="text-sm text-[#6b7280] mt-1">Симуляция бизнес-сценариев «Что если?»</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Параметры сценария</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm text-[#9ca3af] mb-1">Тип сценария</label>
              <select
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value)}
                className="w-full bg-[#1a1d23] border border-[#2d3139] rounded-lg p-2.5 text-white outline-none focus:border-brand-500"
              >
                {SCENARIO_TYPES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-[#9ca3af] mb-1">
                {scenarioType === 'price_change' ? 'Товар' :
                 scenarioType === 'promotion' ? 'Товар/категория' :
                 scenarioType === 'purchase_change' ? 'Поставщик' : 'Сотрудник'}
              </label>
              <input
                type="text"
                value={entityName}
                onChange={(e) => setEntityName(e.target.value)}
                placeholder="Название..."
                className="w-full bg-[#1a1d23] border border-[#2d3139] rounded-lg p-2.5 text-white outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-sm text-[#9ca3af] mb-1">
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
              <div className="flex justify-between text-xs text-[#6b7280]">
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
            {isLoading && <div className="text-[#6b7280] animate-pulse">Симуляция выполняется...</div>}
            {!result && !isLoading && (
              <div className="text-center py-8 text-[#6b7280]">
                <div className="text-3xl mb-2">🔮</div>
                <p className="text-sm">Настройте параметры и запустите симуляцию</p>
              </div>
            )}
            {result?.error && (
              <div className="text-sm text-error">{result.error}</div>
            )}
            {result && !result.error && (
              <div className="space-y-3">
                {result.summary && (
                  <div className="text-sm text-white whitespace-pre-wrap">{result.summary}</div>
                )}
                {result.impact && (
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    {Object.entries(result.impact).map(([k, v]: [string, any]) => (
                      <div key={k} className="bg-[#0f1117] rounded-lg p-2 text-center">
                        <div className="text-xs text-[#6b7280]">{k}</div>
                        <div className="text-sm font-bold text-white">{String(v)}</div>
                      </div>
                    ))}
                  </div>
                )}
                {result.chart_url && (
                  <img src={result.chart_url} alt="Chart" className="w-full rounded-lg mt-2" />
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
