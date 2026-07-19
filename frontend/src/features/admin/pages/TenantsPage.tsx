import { useState, useEffect } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Dialog } from '@/shared/components/ui/Dialog';

interface Tenant { id: string; name: string; slug: string; is_active: boolean; created_at: string; }
interface Connection { id: string; tenant_id: string; name: string; base_url: string; username: string; health_status: string; is_default: boolean; }
interface PlatformUser { id: string; email: string; full_name: string; is_superadmin: boolean; is_active: boolean; tenants: { tenant_id: string; tenant_name: string; role: string; }[]; }

function Tab({ active, setActive, label }: { active: boolean; setActive: () => void; label: string }) {
  return (
    <button onClick={setActive} className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
      style={{ backgroundColor: active ? 'var(--brand)' : 'var(--bg-card)', color: active ? '#fff' : 'var(--text-secondary)' }}>
      {label}
    </button>
  );
}

export default function TenantsPage() {
  const [tab, setTab] = useState<'tenants' | 'connections' | 'users'>('tenants');
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<any>({});
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const load = async () => {
    if (tab === 'tenants') api.get('/api/v1/admin/tenants').then(r => setTenants(r.data?.tenants || [])).catch(() => {});
    if (tab === 'connections') api.get('/api/v1/admin/connections?tenant_id=all').then(r => setConnections(r.data?.connections || [])).catch(() => {});
    if (tab === 'users') api.get('/api/v1/admin/users').then(r => setUsers(r.data?.users || [])).catch(() => {});
  };
  useEffect(() => { load(); }, [tab]);

  const save = async () => {
    try {
      if (tab === 'tenants') {
        if (formMode === 'create') await api.post('/api/v1/admin/tenants', form);
        else await api.patch(`/api/v1/admin/tenants/${form.id}`, form);
      }
      if (tab === 'connections') {
        if (formMode === 'create') await api.post('/api/v1/admin/connections', form);
      }
      if (tab === 'users') {
        if (formMode === 'create') await api.post('/api/v1/admin/users', form);
        else await api.patch(`/api/v1/admin/users/${form.id}`, form);
      }
      setShowForm(false); setForm({}); load();
    } catch (e: any) { alert(e?.response?.data?.detail || 'Ошибка'); }
  };

  const testConn = async () => {
    setTesting(true);
    try {
      const r = await api.post(`/api/v1/admin/connections/${form.id}/test`);
      setTestResult(r.data);
    } catch (e: any) { setTestResult({ status: 'error', error: e.message }); }
    finally { setTesting(false); }
  };

  const openCreate = () => { setForm({}); setFormMode('create'); setShowForm(true); setTestResult(null); };
  const openEdit = (item: any) => { setForm(item); setFormMode('edit'); setShowForm(true); setTestResult(null); };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>⚙️ Управление</h1>
        <button onClick={openCreate} className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ backgroundColor: 'var(--brand)' }}>+ Создать</button>
      </div>

      <div className="flex gap-2 mb-6">
        <Tab active={tab === 'tenants'} setActive={() => setTab('tenants')} label="🏢 Организации" />
        <Tab active={tab === 'connections'} setActive={() => setTab('connections')} label="🔌 Подключения 1С" />
        <Tab active={tab === 'users'} setActive={() => setTab('users')} label="👥 Пользователи" />
      </div>

      {/* Tenants */}
      {tab === 'tenants' && (
        <div className="grid gap-3">
          {tenants.map(t => (
            <div key={t.id} className="rounded-xl border p-4 cursor-pointer hover:brightness-110 transition-all"
              style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}
              onClick={() => openEdit(t)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{t.name}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>slug: {t.slug}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                  {t.is_active ? 'Активен' : 'Неактивен'}
                </span>
              </div>
            </div>
          ))}
          {tenants.length === 0 && <p className="text-sm py-8 text-center" style={{ color: 'var(--text-muted)' }}>Нет организаций</p>}
        </div>
      )}

      {/* Connections */}
      {tab === 'connections' && (
        <div className="grid gap-3">
          {connections.map(c => (
            <div key={c.id} className="rounded-xl border p-4 cursor-pointer hover:brightness-110 transition-all"
              style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}
              onClick={() => openEdit(c)}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{c.name}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{c.base_url}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${c.health_status === 'ok' ? 'bg-emerald-100 text-emerald-700' : c.health_status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                  {c.health_status === 'ok' ? '✅' : c.health_status === 'error' ? '❌' : '❓'}
                </span>
              </div>
            </div>
          ))}
          {connections.length === 0 && <p className="text-sm py-8 text-center" style={{ color: 'var(--text-muted)' }}>Нет подключений</p>}
        </div>
      )}

      {/* Users */}
      {tab === 'users' && (
        <div className="grid gap-3">
          {users.map(u => (
            <div key={u.id} className="rounded-xl border p-4 cursor-pointer hover:brightness-110 transition-all"
              style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}
              onClick={() => openEdit(u)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{u.full_name || u.email}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{u.email} · {u.tenants?.map(t => t.tenant_name).join(', ') || 'нет организаций'}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                  {u.is_active ? 'Активен' : 'Заблокирован'}
                </span>
              </div>
            </div>
          ))}
          {users.length === 0 && <p className="text-sm py-8 text-center" style={{ color: 'var(--text-muted)' }}>Нет пользователей</p>}
        </div>
      )}

      {/* Form Dialog */}
      <Dialog open={showForm} onClose={() => setShowForm(false)} title={formMode === 'create' ? 'Создать' : 'Редактировать'} className="max-w-lg">
        <div className="space-y-3">
          {tab === 'tenants' && (
            <>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Название</label>
                <input value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Slug</label>
                <input value={form.slug || ''} onChange={e => setForm({ ...form, slug: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
            </>
          )}

          {tab === 'connections' && (
            <>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Название</label>
                <input value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Base URL</label>
                <input value={form.base_url || ''} onChange={e => setForm({ ...form, base_url: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Логин</label>
                <input value={form.username || ''} onChange={e => setForm({ ...form, username: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Пароль</label>
                <input type="password" value={form.password || ''} onChange={e => setForm({ ...form, password: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Тенант ID</label>
                <input value={form.tenant_id || ''} onChange={e => setForm({ ...form, tenant_id: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              {formMode === 'edit' && (
                <button onClick={testConn} disabled={testing}
                  className="w-full py-2 rounded-lg text-sm font-medium text-white transition-colors"
                  style={{ backgroundColor: testing ? 'var(--text-muted)' : 'var(--brand)' }}>
                  {testing ? 'Тестирование...' : '🔍 Тест подключения'}
                </button>
              )}
              {testResult && (
                <div className={`p-3 rounded-lg text-sm ${testResult.status === 'ok' ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-800'}`}>
                  {testResult.status === 'ok' ? `✅ Подключено (${testResult.latency_ms}ms)` : `❌ ${testResult.error}`}
                </div>
              )}
            </>
          )}

          {tab === 'users' && (
            <>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Email</label>
                <input value={form.email || ''} onChange={e => setForm({ ...form, email: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Имя</label>
                <input value={form.full_name || ''} onChange={e => setForm({ ...form, full_name: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Пароль</label>
                <input type="password" value={form.password || ''} onChange={e => setForm({ ...form, password: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Тенант ID</label>
                <input value={form.tenant_id || ''} onChange={e => setForm({ ...form, tenant_id: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
              <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Роль</label>
                <select value={form.role || 'viewer'} onChange={e => setForm({ ...form, role: e.target.value })}
                  className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}>
                  <option value="admin">Администратор</option>
                  <option value="analyst">Аналитик</option>
                  <option value="viewer">Наблюдатель</option>
                </select></div>
            </>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded-lg border text-sm" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>Отмена</button>
            <button onClick={save}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ backgroundColor: 'var(--brand)' }}>Сохранить</button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
