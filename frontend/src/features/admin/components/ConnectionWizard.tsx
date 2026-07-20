import { useState, useEffect } from 'react';
import { api } from '@/shared/lib/api';
import { Card } from '@/shared/components/ui/Card';

interface WizardProps {
  tenantId: string;
  onComplete: () => void;
  onCancel: () => void;
}

const STEPS = ['Тип', 'Параметры', 'Проверка', 'Готово'];

export default function ConnectionWizard({ tenantId, onComplete, onCancel }: WizardProps) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({ name: '', base_url: '', username: '', password: '', tenant_id: tenantId });
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleTest = async () => {
    if (!form.name || !form.base_url) return;
    setTesting(true);
    setTestResult(null);
    try {
      const r = await api.post('/api/v1/admin/connections', form);
      const connId = r.data?.connection?.id;
      if (connId) {
        const t = await api.post(`/api/v1/admin/connections/${connId}/test`);
        setTestResult(t.data);
        if (t.data?.status === 'ok') setStep(3);
        else setTestResult(t.data);
      }
    } catch (e: any) {
      setTestResult({ status: 'error', error: e?.response?.data?.detail || 'Ошибка' });
    } finally { setTesting(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (!form.id) {
        await api.post('/api/v1/admin/connections', form);
      }
      onComplete();
    } catch (e: any) { alert(e?.response?.data?.detail || 'Ошибка'); }
    finally { setSaving(false); }
  };

  return (
    <div className="max-w-xl mx-auto">
      {/* Stepper */}
      <div className="flex items-center justify-center gap-1 mb-8">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors
              ${i < step ? 'bg-emerald-500 text-white' : i === step ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
              {i < step ? '✓' : i + 1}
            </div>
            <span className={`text-xs ml-1.5 ${i === step ? 'font-medium' : ''}`} style={{ color: i === step ? 'var(--text-primary)' : 'var(--text-muted)' }}>{s}</span>
            {i < 3 && <div className="w-8 h-px mx-1.5" style={{ backgroundColor: i < step ? 'var(--success)' : 'var(--border)' }} />}
          </div>
        ))}
      </div>

      {/* Step 0: Type */}
      {step === 0 && (
        <Card className="p-6 space-y-4">
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Тип подключения</h3>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Выберите способ подключения к базе 1С</p>
          <div className="grid gap-3">
            {[
              { id: 'http', label: 'HTTP-сервисы', desc: 'Через опубликованные HTTP-сервисы 1С (рекомендуется)' },
              { id: 'odata', label: 'OData', desc: 'Стандартный OData-интерфейс 1С' },
              { id: 'com', label: 'COM-соединение', desc: 'Прямое соединение с базой 1С (только Windows)' },
            ].map(t => (
              <button key={t.id} onClick={() => { setForm({ ...form, config_type: t.id }); setStep(1); }}
                className="text-left p-4 rounded-xl border transition-all hover:brightness-110"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
                <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>{t.label}</div>
                <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{t.desc}</div>
              </button>
            ))}
          </div>
          <button onClick={onCancel} className="text-sm" style={{ color: 'var(--text-muted)' }}>← Отмена</button>
        </Card>
      )}

      {/* Step 1: Credentials */}
      {step === 1 && (
        <Card className="p-6 space-y-4">
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Параметры доступа</h3>
          {['name', 'base_url', 'username', 'password'].map(field => (
            <div key={field}>
              <label className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {field === 'name' ? 'Название' : field === 'base_url' ? 'Base URL' : field === 'username' ? 'Логин' : 'Пароль'}
              </label>
              <input type={field === 'password' ? 'password' : 'text'}
                value={(form as any)[field] || ''}
                onChange={e => setForm({ ...form, [field]: e.target.value })}
                className="w-full p-2.5 rounded-lg border text-sm mt-0.5"
                style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <button onClick={() => setStep(0)} className="px-4 py-2 rounded-lg border text-sm" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>← Назад</button>
            <button onClick={() => setStep(2)} disabled={!form.name || !form.base_url}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50" style={{ backgroundColor: 'var(--brand)' }}>
              Далее →
            </button>
          </div>
        </Card>
      )}

      {/* Step 2: Test */}
      {step === 2 && (
        <Card className="p-6 space-y-4">
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Проверка подключения</h3>
          <div className="p-4 rounded-lg text-sm" style={{ backgroundColor: 'var(--bg-page)' }}>
            <p><strong>URL:</strong> {form.base_url}</p>
            <p><strong>Логин:</strong> {form.username}</p>
          </div>
          <button onClick={handleTest} disabled={testing}
            className="w-full py-3 rounded-lg text-sm font-medium text-white transition-colors"
            style={{ backgroundColor: testing ? 'var(--text-muted)' : 'var(--brand)' }}>
            {testing ? 'Тестирование...' : '🔍 Протестировать подключение'}
          </button>
          {testResult && (
            <div className={`p-4 rounded-lg text-sm ${testResult.status === 'ok' ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-800'}`}>
              {testResult.status === 'ok' ? (
                <div>✅ Подключение успешно ({testResult.latency_ms}ms)</div>
              ) : (
                <div>❌ {testResult.error || 'Ошибка подключения'}</div>
              )}
            </div>
          )}
          <div className="flex gap-2 pt-2">
            <button onClick={() => setStep(1)} className="px-4 py-2 rounded-lg border text-sm" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>← Назад</button>
          </div>
        </Card>
      )}

      {/* Step 3: Done */}
      {step === 3 && (
        <Card className="p-6 space-y-4 text-center">
          <div className="text-5xl mb-2">🎉</div>
          <h3 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>Подключение работает!</h3>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>База «{form.name}» успешно подключена. Можете её выбрать в сайдбаре.</p>
          <button onClick={handleSave} disabled={saving}
            className="px-6 py-2.5 rounded-lg text-sm font-medium text-white"
            style={{ backgroundColor: 'var(--brand)' }}>
            {saving ? 'Сохранение...' : '✅ Завершить'}
          </button>
        </Card>
      )}
    </div>
  );
}
