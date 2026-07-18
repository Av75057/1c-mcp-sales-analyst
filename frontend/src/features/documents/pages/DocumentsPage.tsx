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

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState<Doc | null>(null);
  const [lines, setLines] = useState<DocLine[]>([]);
  const [linesLoading, setLinesLoading] = useState(false);

  useEffect(() => {
    const to = new Date().toISOString().slice(0, 10);
    const from = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
    api.get('/api/documents/sales', { params: { date_from: from, date_to: to, page_size: 50 } })
      .then((r) => {
        const data = r.data?.documents || r.data || [];
        setDocs(Array.isArray(data) ? data : []);
      })
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, []);

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
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📋 Реализации</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Документы реализации товаров и услуг</p>
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
