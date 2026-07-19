import { useState, useEffect } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Dialog } from '@/shared/components/ui/Dialog';

interface Doc {
  id: string;
  number: string;
  date: string;
  counterparty: string;
  sum: number;
  posted: boolean;
}

interface DocLine {
  nomenclature: string;
  quantity: number;
  sum: number;
  price?: number;
}

const PERIOD_PRESETS = [
  { label: 'Сегодня', days: 0 },
  { label: 'Вчера', days: 1 },
  { label: '7 дней', days: 7 },
  { label: '30 дней', days: 30 },
  { label: '90 дней', days: 90 },
  { label: 'Год', days: 365 },
];

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState<Doc | null>(null);
  const [lines, setLines] = useState<DocLine[]>([]);
  const [linesLoading, setLinesLoading] = useState(false);
  const [periodDays, setPeriodDays] = useState(30);
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  const fetchDocs = (days: number, from?: string, to?: string) => {
    setLoading(true);
    const toDate = to || new Date().toISOString().slice(0, 10);
    const fromDate = from || (days > 0 ? new Date(Date.now() - days * 86400000).toISOString().slice(0, 10) : toDate);
    api.get('/api/documents/sales', { params: { date_from: fromDate, date_to: toDate, page_size: 50 } })
      .then((r) => {
        const data = r.data?.documents || r.data || [];
        setDocs(Array.isArray(data) ? data : []);
      })
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (!customFrom || !customTo) fetchDocs(periodDays); }, [periodDays, customFrom, customTo]);

  const openDoc = async (doc: Doc) => {
    setSelectedDoc(doc);
    setLines([]);
    setLinesLoading(true);
    try {
      const r = await api.get(`/api/documents/sales/${doc.id}/lines`);
      setLines(r.data?.lines || []);
    } catch {
      setLines([]);
    } finally {
      setLinesLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📋 Реализации</h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Документы реализации товаров и услуг</p>
          </div>
          <div className="flex items-center gap-1 flex-wrap">
            <div className="flex rounded-lg p-0.5" style={{ backgroundColor: 'var(--bg-card-hover)' }}>
              {PERIOD_PRESETS.map(p => (
                <button key={p.days} onClick={() => { setPeriodDays(p.days); setCustomFrom(''); setCustomTo(''); }}
                  className="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  style={periodDays === p.days && !customFrom ? { backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' } : { color: 'var(--text-secondary)' }}>
                  {p.label}
                </button>
              ))}
            </div>
            <input type="date" value={customFrom} onChange={e => { setCustomFrom(e.target.value); setPeriodDays(0); }}
              className="px-2 py-1.5 text-xs rounded-lg border"
              style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>—</span>
            <input type="date" value={customTo} onChange={e => { setCustomTo(e.target.value); setPeriodDays(0); }}
              className="px-2 py-1.5 text-xs rounded-lg border"
              style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            {customFrom && customTo && (
              <button onClick={() => fetchDocs(0, customFrom, customTo)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors text-white"
                style={{ backgroundColor: 'var(--brand)' }}>
                Применить
              </button>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <div className="space-y-2">
          {[1,2,3].map(i => <div key={i} className="h-12 border rounded-lg animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }} />)}
        </div>
      )}

      {!loading && docs.length === 0 && (
        <Card><CardContent className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
          <div className="text-3xl mb-2">📋</div>
          <p>Нет документов за выбранный период</p>
        </CardContent></Card>
      )}

      {docs.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Документы ({docs.length})</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                    <th className="text-left py-2 px-2">№</th>
                    <th className="text-left py-2 px-2">Дата</th>
                    <th className="text-left py-2 px-2">Контрагент</th>
                    <th className="text-right py-2 px-2">Сумма</th>
                    <th className="text-left py-2 px-2">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map((d) => (
                    <tr
                      key={d.id}
                      className="border-b cursor-pointer transition-colors"
                      style={{ borderColor: 'var(--border)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = ''; }}
                      onClick={() => openDoc(d)}
                    >
                      <td className="py-2 px-2 font-mono text-xs" style={{ color: 'var(--text-primary)' }}>{d.number || '-'}</td>
                      <td className="py-2 px-2 whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>{d.date ? d.date.slice(0, 10) : '-'}</td>
                      <td className="py-2 px-2" style={{ color: 'var(--text-primary)' }}>{d.counterparty || '-'}</td>
                      <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--text-primary)' }}>{(d.sum || 0).toLocaleString()} ₽</td>
                      <td className="py-2 px-2">
                        <Badge variant={d.posted ? 'success' : 'secondary'}>
                          {d.posted ? 'Проведён' : 'Черновик'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal деталей документа */}
      <Dialog open={!!selectedDoc} onClose={() => setSelectedDoc(null)} title={`Документ №${selectedDoc?.number || ''}`} className="max-w-2xl">
        {selectedDoc && (
          <div className="space-y-4 max-h-[70vh] overflow-y-auto">
            {/* Шапка документа */}
            <div className="grid grid-cols-2 gap-3 pb-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <div>
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Номер</label>
                <div className="font-mono text-sm" style={{ color: 'var(--text-primary)' }}>{selectedDoc.number || '-'}</div>
              </div>
              <div>
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Дата</label>
                <div className="text-sm" style={{ color: 'var(--text-primary)' }}>{selectedDoc.date ? selectedDoc.date.slice(0, 10) : '-'}</div>
              </div>
              <div className="col-span-2">
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Контрагент</label>
                <div className="text-sm" style={{ color: 'var(--text-primary)' }}>{selectedDoc.counterparty || '-'}</div>
              </div>
              <div>
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Сумма</label>
                <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{(selectedDoc.sum || 0).toLocaleString()} ₽</div>
              </div>
              <div>
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Статус</label>
                <div><Badge variant={selectedDoc.posted ? 'success' : 'secondary'}>
                  {selectedDoc.posted ? 'Проведён' : 'Черновик'}
                </Badge></div>
              </div>
            </div>

            {/* Таблица товаров */}
            <div>
              <h4 className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Товары ({lines.length})</h4>
              {linesLoading && (
                <div className="space-y-1">
                  {[1,2,3].map(i => <div key={i} className="h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--skeleton)' }} />)}
                </div>
              )}
              {!linesLoading && lines.length === 0 && (
                <p className="text-sm py-4 text-center" style={{ color: 'var(--text-secondary)' }}>Нет данных о товарах</p>
              )}
              {!linesLoading && lines.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                        <th className="text-left py-1.5 px-1">Товар</th>
                        <th className="text-right py-1.5 px-1">Кол-во</th>
                        <th className="text-right py-1.5 px-1">Цена</th>
                        <th className="text-right py-1.5 px-1">Сумма</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lines.map((line, i) => {
                        const qty = line.quantity || 0;
                        const total = line.sum || 0;
                        const price = qty > 0 ? Math.round(total / qty) : (line.price || 0);
                        return (
                          <tr key={i} className="border-b" style={{ borderColor: 'var(--border)' }}>
                            <td className="py-1.5 px-1" style={{ color: 'var(--text-primary)' }}>{line.nomenclature || '-'}</td>
                            <td className="py-1.5 px-1 text-right" style={{ color: 'var(--text-secondary)' }}>{qty}</td>
                            <td className="py-1.5 px-1 text-right" style={{ color: 'var(--text-secondary)' }}>
                              {price ? price.toLocaleString() + ' ₽' : '-'}
                            </td>
                            <td className="py-1.5 px-1 text-right" style={{ color: 'var(--text-primary)' }}>{total.toLocaleString()} ₽</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr className="font-bold" style={{ color: 'var(--text-primary)' }}>
                        <td className="py-2 px-1">Итого</td>
                        <td className="py-2 px-1 text-right">{lines.reduce((s, l) => s + (l.quantity || 0), 0)}</td>
                        <td className="py-2 px-1" />
                        <td className="py-2 px-1 text-right">{lines.reduce((s, l) => s + (l.sum || 0), 0).toLocaleString()} ₽</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
