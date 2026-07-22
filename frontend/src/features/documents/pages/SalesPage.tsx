import { useState, useEffect, useMemo } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';

interface Sale {
  date: string;
  nomenclature: string;
  quantity: number;
  sum: number;
  manager: string;
  client: string;
}

const PERIODS = [
  { label: '7 дней', days: 7 },
  { label: '30 дней', days: 30 },
  { label: '90 дней', days: 90 },
  { label: 'Год', days: 365 },
  { label: 'Всё', days: 0 },
];

export default function SalesPage() {
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10);
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10));

  const fetchSales = () => {
    setLoading(true);
    api.get('/api/sales', { params: { date_from: dateFrom, date_to: dateTo, limit: 5000 } })
      .then((r) => setSales(r.data?.data || r.data || []))
      .catch(() => setSales([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchSales(); }, [dateFrom, dateTo]);

  const setPreset = (days: number) => {
    if (days === 0) {
      setDateFrom('2020-01-01'); setDateTo(new Date().toISOString().slice(0, 10));
    } else {
      const d = new Date(); d.setDate(d.getDate() - days);
      setDateFrom(d.toISOString().slice(0, 10));
      setDateTo(new Date().toISOString().slice(0, 10));
    }
    setPeriod(days);
  };

  const grouped = useMemo(() => {
    const map = new Map<string, { quantity: number; sum: number; sales: number }>();
    for (const s of sales) {
      const key = s.nomenclature || 'Неизвестно';
      const existing = map.get(key) || { quantity: 0, sum: 0, sales: 0 };
      existing.quantity += s.quantity || 0;
      existing.sum += s.sum || 0;
      existing.sales += 1;
      map.set(key, existing);
    }
    return Array.from(map.entries())
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.sum - a.sum);
  }, [sales]);

  const totalSum = useMemo(() => grouped.reduce((a, b) => a + b.sum, 0), [grouped]);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📊 Продажи</h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Сводка по товарам</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {PERIODS.map(p => (
            <button key={p.days} onClick={() => setPreset(p.days)}
              className="px-3 py-1.5 text-xs rounded-lg border transition-colors"
              style={{
                backgroundColor: period === p.days ? 'var(--brand)' : 'var(--bg-card)',
                borderColor: period === p.days ? 'var(--brand)' : 'var(--border)',
                color: period === p.days ? '#fff' : 'var(--text-secondary)',
              }}>{p.label}</button>
          ))}
          <input type="date" value={dateFrom} onChange={e => { setPeriod(0); setDateFrom(e.target.value); }}
            className="px-2 py-1.5 text-xs rounded-lg border" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>—</span>
          <input type="date" value={dateTo} onChange={e => { setPeriod(0); setDateTo(e.target.value); }}
            className="px-2 py-1.5 text-xs rounded-lg border" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
        </div>
      </div>

      {loading && <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-10 border rounded-lg animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }} />)}</div>}

      {!loading && grouped.length === 0 && (
        <Card><CardContent className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}><div className="text-3xl mb-2">📊</div><p>Нет данных о продажах</p></CardContent></Card>
      )}

      {grouped.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Товары ({grouped.length}) · всего {totalSum.toLocaleString()} ₽</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                    <th className="text-left py-2 px-2">#</th>
                    <th className="text-left py-2 px-2">Товар</th>
                    <th className="text-right py-2 px-2">Продаж</th>
                    <th className="text-right py-2 px-2">Кол-во</th>
                    <th className="text-right py-2 px-2">Сумма</th>
                    <th className="text-right py-2 px-2">Доля</th>
                  </tr>
                </thead>
                <tbody>
                  {grouped.map((item, i) => (
                    <tr key={item.name} className="border-b" style={{ borderColor: 'var(--border)' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = ''}>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                      <td className="py-2 px-2 max-w-[300px] truncate" style={{ color: 'var(--text-primary)' }}>{item.name}</td>
                      <td className="py-2 px-2 text-right" style={{ color: 'var(--text-secondary)' }}>{item.sales}</td>
                      <td className="py-2 px-2 text-right" style={{ color: 'var(--text-primary)' }}>{item.quantity.toFixed(1)}</td>
                      <td className="py-2 px-2 text-right whitespace-nowrap font-medium" style={{ color: 'var(--text-primary)' }}>{item.sum.toLocaleString()} ₽</td>
                      <td className="py-2 px-2 text-right" style={{ color: 'var(--text-secondary)' }}>{totalSum > 0 ? (item.sum / totalSum * 100).toFixed(1) : 0}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
