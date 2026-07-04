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
        <h1 className="text-2xl font-bold text-white">📋 Реализации</h1>
        <p className="text-sm text-[#6b7280] mt-1">Документы реализации товаров и услуг</p>
      </div>

      {loading && (
        <div className="space-y-2">
          {[1,2,3].map(i => <div key={i} className="h-12 bg-[#1a1d23] border border-[#2d3139] rounded-lg animate-pulse" />)}
        </div>
      )}

      {!loading && docs.length === 0 && (
        <Card><CardContent className="py-8 text-center text-[#6b7280]">
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
                  <tr className="text-[#6b7280] border-b border-[#2d3139]">
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
                      className="border-b border-[#2d3139] hover:bg-[#22262e] cursor-pointer transition-colors"
                      onClick={() => openDoc(d)}
                    >
                      <td className="py-2 px-2 text-white font-mono text-xs">{d.number || '-'}</td>
                      <td className="py-2 px-2 text-[#9ca3af] whitespace-nowrap">{d.date ? d.date.slice(0, 10) : '-'}</td>
                      <td className="py-2 px-2 text-white">{d.counterparty || '-'}</td>
                      <td className="py-2 px-2 text-right text-white whitespace-nowrap">{(d.sum || 0).toLocaleString()} ₽</td>
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
            <div className="grid grid-cols-2 gap-3 pb-3 border-b border-[#2d3139]">
              <div>
                <label className="text-xs text-[#6b7280]">Номер</label>
                <div className="text-white font-mono text-sm">{selectedDoc.number || '-'}</div>
              </div>
              <div>
                <label className="text-xs text-[#6b7280]">Дата</label>
                <div className="text-white text-sm">{selectedDoc.date ? selectedDoc.date.slice(0, 10) : '-'}</div>
              </div>
              <div className="col-span-2">
                <label className="text-xs text-[#6b7280]">Контрагент</label>
                <div className="text-white text-sm">{selectedDoc.counterparty || '-'}</div>
              </div>
              <div>
                <label className="text-xs text-[#6b7280]">Сумма</label>
                <div className="text-white font-bold text-lg">{(selectedDoc.sum || 0).toLocaleString()} ₽</div>
              </div>
              <div>
                <label className="text-xs text-[#6b7280]">Статус</label>
                <div><Badge variant={selectedDoc.posted ? 'success' : 'secondary'}>
                  {selectedDoc.posted ? 'Проведён' : 'Черновик'}
                </Badge></div>
              </div>
            </div>

            {/* Таблица товаров */}
            <div>
              <h4 className="text-sm font-medium text-white mb-2">Товары ({lines.length})</h4>
              {linesLoading && (
                <div className="space-y-1">
                  {[1,2,3].map(i => <div key={i} className="h-8 bg-[#2d3139] rounded animate-pulse" />)}
                </div>
              )}
              {!linesLoading && lines.length === 0 && (
                <p className="text-sm text-[#6b7280] py-4 text-center">Нет данных о товарах</p>
              )}
              {!linesLoading && lines.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-[#6b7280] border-b border-[#2d3139]">
                        <th className="text-left py-1.5 px-1">Товар</th>
                        <th className="text-right py-1.5 px-1">Кол-во</th>
                        <th className="text-right py-1.5 px-1">Цена</th>
                        <th className="text-right py-1.5 px-1">Сумма</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lines.map((line, i) => (
                        <tr key={i} className="border-b border-[#2d3139]">
                          <td className="py-1.5 px-1 text-white">{line.nomenclature || '-'}</td>
                          <td className="py-1.5 px-1 text-right text-[#9ca3af]">{line.quantity || 0}</td>
                          <td className="py-1.5 px-1 text-right text-[#9ca3af]">
                            {line.price ? (line.price || 0).toLocaleString() + ' ₽' : '-'}
                          </td>
                          <td className="py-1.5 px-1 text-right text-white">{(line.sum || 0).toLocaleString()} ₽</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="font-bold text-white">
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
