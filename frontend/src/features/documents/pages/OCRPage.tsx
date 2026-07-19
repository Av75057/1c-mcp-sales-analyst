import { useState, useRef } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';

export default function OCRPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

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

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📄 Распознавание документов</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Загрузите скан или фото документа для распознавания</p>
      </div>

      <div className="mb-4">
        <button onClick={() => fileRef.current?.click()}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-colors inline-flex items-center gap-1.5"
          style={{ backgroundColor: 'var(--brand)', color: '#fff' }}>
          <Upload className="w-4 h-4" /> Загрузить
        </button>
      </div>

      <input ref={fileRef} type="file" accept="image/*,.pdf" className="hidden"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />

      <Card>
        <CardContent className="py-8">
          <div onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors"
            style={{ borderColor: 'var(--border)' }}>
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
            <div className="mt-4 p-4 rounded-lg" style={{ backgroundColor: uploadResult.error ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)' }}>
              {uploadResult.error ? (
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-sm text-red-600">Ошибка распознавания</p>
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{uploadResult.error}</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>✅ Документ распознан</p>
                    <div className="mt-2 space-y-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                      {(() => {
                        const doc = uploadResult.document || {};
                        const h = doc.header || {};
                        return <>
                          <p>Статус: <span style={{ color: 'var(--text-primary)' }}>{uploadResult.status === 'completed' ? 'Готов' : 'Требует проверки'}</span></p>
                          {h.seller && <p>Поставщик: <span style={{ color: 'var(--text-primary)' }}>{String(h.seller)}</span></p>}
                          {h.counterparty && !h.seller && <p>Организация: <span style={{ color: 'var(--text-primary)' }}>{String(h.counterparty)}</span></p>}
                          {h.buyer && <p>Покупатель: <span style={{ color: 'var(--text-primary)' }}>{String(h.buyer)}</span></p>}
                          {h.organization && <p>Организация: <span style={{ color: 'var(--text-primary)' }}>{String(h.organization)}</span></p>}
                          {h.inn && <p>ИНН поставщика: <span style={{ color: 'var(--text-primary)' }}>{String(h.inn)}</span></p>}
                          {h.buyer_inn && <p>ИНН покупателя: <span style={{ color: 'var(--text-primary)' }}>{String(h.buyer_inn)}</span></p>}
                          {h.date && <p>Дата: <span style={{ color: 'var(--text-primary)' }}>{String(h.date)}</span></p>}
                          {h.number && <p>Номер: <span style={{ color: 'var(--text-primary)' }}>{String(h.number)}</span></p>}
                          {doc.totals?.total != null && <p className="font-medium mt-1" style={{ color: 'var(--text-primary)' }}>Сумма: {Number(doc.totals.total).toLocaleString('ru-RU')} ₽</p>}
                          <p className="opacity-60 mt-0.5">Тип: {doc.doc_type || 'документ'} (уверенность: {Math.round((doc.doc_type_confidence || 0) * 100)}%)</p>
                        </>;
                      })()}
                    </div>

                    {(() => {
                      const items = (uploadResult.document || {}).items;
                      if (!items || items.length === 0) return null;
                      const fmt = (n: number) => n.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                      return (
                        <div className="mt-3 overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                                <th className="text-left py-1.5 pr-2">Товар</th>
                                <th className="text-right py-1.5 px-2">Кол-во</th>
                                <th className="text-right py-1.5 px-2">Цена</th>
                                <th className="text-right py-1.5 pl-2">Сумма</th>
                              </tr>
                            </thead>
                            <tbody>
                              {items.map((item: any, i: number) => (
                                <tr key={i} className="border-b" style={{ borderColor: 'var(--border)' }}>
                                  <td className="py-1.5 pr-2" style={{ color: 'var(--text-primary)' }}>{item.name || item.nomenclature || '-'}</td>
                                  <td className="py-1.5 px-2 text-right" style={{ color: 'var(--text-secondary)' }}>{item.quantity != null ? item.quantity : '-'}</td>
                                  <td className="py-1.5 px-2 text-right" style={{ color: 'var(--text-secondary)' }}>{item.price != null ? fmt(item.price) + ' ₽' : '-'}</td>
                                  <td className="py-1.5 pl-2 text-right" style={{ color: 'var(--text-primary)' }}>{item.sum_with_vat != null ? fmt(item.sum_with_vat) + ' ₽' : (item.sum_without_vat != null ? fmt(item.sum_without_vat) + ' ₽' : '-')}</td>
                                </tr>
                              ))}
                            </tbody>
                            <tfoot>
                              <tr className="font-medium" style={{ color: 'var(--text-primary)' }}>
                                <td className="py-1.5 pr-2">Итого</td>
                                <td className="py-1.5 px-2 text-right">{items.reduce((s: number, it: any) => s + (it.quantity || 0), 0)}</td>
                                <td className="py-1.5 px-2" />
                                <td className="py-1.5 pl-2 text-right">{items.reduce((s: number, it: any) => s + (it.sum_with_vat || it.sum_without_vat || 0), 0).toLocaleString('ru-RU')} ₽</td>
                              </tr>
                            </tfoot>
                          </table>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
