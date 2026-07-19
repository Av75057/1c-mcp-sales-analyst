import { useState, useRef } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Dialog } from '@/shared/components/ui/Dialog';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';

interface Doc {
  id: string; number: string; date: string; counterparty: string; sum: number; posted: boolean;
}

interface DocLine {
  nomenclature: string; quantity: number; sum: number; price?: number;
}

export default function OCRPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [selectedDoc, setSelectedDoc] = useState<Doc | null>(null);
  const [lines, setLines] = useState<DocLine[]>([]);
  const [linesLoading, setLinesLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'list'>('upload');
  const fileRef = useRef<HTMLInputElement>(null);

  const loadDocs = () => {
    setLoading(true);
    const to = new Date().toISOString().slice(0, 10);
    const from = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
    api.get('/api/documents/sales', { params: { date_from: from, date_to: to, page_size: 50 } })
      .then(r => setDocs(Array.isArray(r.data?.documents || r.data) ? (r.data?.documents || r.data) : []))
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  };

  const handleFile = async (file: File) => {
    setUploading(true);
    setUploadResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('match_nomenclature', 'true');
      const r = await api.post('/api/documents/upload', form);
      setUploadResult(r.data);
    } catch (e: any) {
      setUploadResult({ status: 'failed', error: e.message });
    } finally {
      setUploading(false);
    }
  };

  const openDoc = async (doc: Doc) => {
    setSelectedDoc(doc);
    setLines([]);
    setLinesLoading(true);
    try {
      const r = await api.get(`/api/documents/sales/${doc.id}/lines`);
      setLines(r.data?.lines || []);
    } catch { setLines([]); }
    finally { setLinesLoading(false); }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📄 Распознавание документов</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Загрузите скан или фото документа для распознавания</p>
      </div>

      <div className="flex gap-2 mb-4">
        <button onClick={() => setActiveTab('upload')}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{ backgroundColor: activeTab === 'upload' ? 'var(--brand)' : 'var(--bg-card)', color: activeTab === 'upload' ? '#fff' : 'var(--text-secondary)' }}>
          <Upload className="w-4 h-4 inline mr-1" /> Загрузить
        </button>
        <button onClick={() => { setActiveTab('list'); loadDocs(); }}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{ backgroundColor: activeTab === 'list' ? 'var(--brand)' : 'var(--bg-card)', color: activeTab === 'list' ? '#fff' : 'var(--text-secondary)' }}>
          <FileText className="w-4 h-4 inline mr-1" /> Документы
        </button>
      </div>

      {activeTab === 'upload' && (
        <Card>
          <CardContent className="py-8">
            <div onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors"
              style={{ borderColor: 'var(--border)' }}>
              <input ref={fileRef} type="file" accept="image/*,.pdf" className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
              <Upload className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
              <p className="font-medium" style={{ color: 'var(--text-primary)' }}>Нажмите для загрузки</p>
              <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>PDF, JPEG, PNG — до 10 МБ</p>
            </div>

            {uploading && (
              <div className="flex items-center justify-center gap-2 mt-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <div className="animate-spin w-4 h-4 border-2 rounded-full" style={{ borderColor: 'var(--brand)', borderTopColor: 'transparent' }} />
                Распознавание...
              </div>
            )}

            {uploadResult && (
              <div className="mt-4 p-4 rounded-lg" style={{ backgroundColor: uploadResult.status === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)' }}>
                {uploadResult.status === 'success' ? (
                  <div className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>Документ распознан</p>
                      {uploadResult.fields && Object.entries(uploadResult.fields).map(([k, v]) => (
                        <p key={k} className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{k}: {String(v)}</p>
                      ))}
                      {uploadResult.items && (
                        <div className="mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                          Товаров: {uploadResult.items.length}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-sm text-red-600">Ошибка распознавания</p>
                      <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{uploadResult.error || 'Неизвестная ошибка'}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'list' && (
        <>
          {loading && (
            <div className="space-y-2">
              {[1,2,3].map(i => <div key={i} className="h-12 border rounded-lg animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }} />)}
            </div>
          )}
          {!loading && docs.length === 0 && (
            <Card><CardContent className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
              <FileText className="w-8 h-8 mx-auto mb-2" />
              <p>Нет документов за последние 30 дней</p>
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
                        <tr key={d.id} className="border-b cursor-pointer transition-colors" style={{ borderColor: 'var(--border)' }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = ''}
                          onClick={() => openDoc(d)}>
                          <td className="py-2 px-2 font-mono text-xs" style={{ color: 'var(--text-primary)' }}>{d.number || '-'}</td>
                          <td className="py-2 px-2 whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>{d.date?.slice(0, 10) || '-'}</td>
                          <td className="py-2 px-2" style={{ color: 'var(--text-primary)' }}>{d.counterparty || '-'}</td>
                          <td className="py-2 px-2 text-right" style={{ color: 'var(--text-primary)' }}>{(d.sum || 0).toLocaleString()} ₽</td>
                          <td className="py-2 px-2"><Badge variant={d.posted ? 'success' : 'secondary'}>{d.posted ? 'Проведён' : 'Черновик'}</Badge></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      <Dialog open={!!selectedDoc} onClose={() => setSelectedDoc(null)} title={`Документ №${selectedDoc?.number || ''}`} className="max-w-2xl">
        {selectedDoc && (
          <div className="space-y-4 max-h-[70vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-3 pb-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <div>
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Номер</label>
                <div className="font-mono text-sm" style={{ color: 'var(--text-primary)' }}>{selectedDoc.number || '-'}</div>
              </div>
              <div>
                <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Дата</label>
                <div className="text-sm" style={{ color: 'var(--text-primary)' }}>{selectedDoc.date?.slice(0, 10) || '-'}</div>
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
                <div><Badge variant={selectedDoc.posted ? 'success' : 'secondary'}>{selectedDoc.posted ? 'Проведён' : 'Черновик'}</Badge></div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Товары ({lines.length})</h4>
              {linesLoading && <div className="space-y-1">{[1,2,3].map(i => <div key={i} className="h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--skeleton)' }} />)}</div>}
              {!linesLoading && lines.length === 0 && <p className="text-sm py-4 text-center" style={{ color: 'var(--text-secondary)' }}>Нет данных</p>}
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
                            <td className="py-1.5 px-1 text-right" style={{ color: 'var(--text-secondary)' }}>{price ? price.toLocaleString() + ' ₽' : '-'}</td>
                            <td className="py-1.5 px-1 text-right" style={{ color: 'var(--text-primary)' }}>{total.toLocaleString()} ₽</td>
                          </tr>
                        );
                      })}
                    </tbody>
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
