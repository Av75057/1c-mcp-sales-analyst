import { useState, useEffect } from 'react';
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

export default function SalesPage() {
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const to = new Date().toISOString().slice(0, 10);
    const from = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
    api.get('/api/sales', { params: { date_from: from, date_to: to, limit: 100 } })
      .then((r) => setSales(r.data?.data || r.data || []))
      .catch(() => setSales([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">📊 Продажи</h1>
        <p className="text-sm text-[#6b7280] mt-1">Данные о продажах по товарам</p>
      </div>

      {loading && <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-10 bg-[#1a1d23] border border-[#2d3139] rounded-lg animate-pulse" />)}</div>}

      {!loading && sales.length === 0 && (
        <Card><CardContent className="py-8 text-center text-[#6b7280]"><div className="text-3xl mb-2">📊</div><p>Нет данных о продажах</p></CardContent></Card>
      )}

      {sales.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Продажи ({sales.length})</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#6b7280] border-b border-[#2d3139]">
                    <th className="text-left py-2 px-2">Дата</th>
                    <th className="text-left py-2 px-2">Товар</th>
                    <th className="text-right py-2 px-2">Кол-во</th>
                    <th className="text-right py-2 px-2">Сумма</th>
                    <th className="text-left py-2 px-2">Менеджер</th>
                    <th className="text-left py-2 px-2">Контрагент</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map((s, i) => (
                    <tr key={i} className="border-b border-[#2d3139] hover:bg-[#22262e]">
                      <td className="py-2 px-2 text-[#9ca3af] whitespace-nowrap">{s.date || '-'}</td>
                      <td className="py-2 px-2 text-white max-w-[200px] truncate">{s.nomenclature || '-'}</td>
                      <td className="py-2 px-2 text-right text-white">{s.quantity || 0}</td>
                      <td className="py-2 px-2 text-right text-white whitespace-nowrap">{(s.sum || 0).toLocaleString()} ₽</td>
                      <td className="py-2 px-2 text-[#9ca3af] whitespace-nowrap">{s.manager || '-'}</td>
                      <td className="py-2 px-2 text-white max-w-[150px] truncate">{s.client || '-'}</td>
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
