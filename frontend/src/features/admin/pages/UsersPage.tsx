import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Dialog } from '@/shared/components/ui/Dialog';
import { formatDate } from '@/shared/lib/utils';

interface ConnectionOption { id: string; name: string; base_url: string; }

interface PlatformUser {
  id: string; email: string; full_name: string; is_superadmin: boolean;
  is_active: boolean; last_login_at: string; created_at: string;
  tenants: { tenant_id: string; tenant_name: string; role: string; }[];
}

export default function UsersPage() {
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<any>({});
  const [editId, setEditId] = useState<string | null>(null);

  const [connections, setConnections] = useState<ConnectionOption[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const [u, c] = await Promise.all([
        api.get('/api/v1/admin/users'),
        api.get('/api/v1/admin/connections', { params: { tenant_id: 'all' } }),
      ]);
      setUsers(u.data?.users || []);
      setConnections(c.data?.connections || []);
    } catch { setUsers([]); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => { setForm({ role: 'viewer' }); setEditId(null); setShowForm(true); };
  const openEdit = (u: PlatformUser) => { setForm(u); setEditId(u.id); setShowForm(true); };

  const save = async () => {
    try {
      if (editId) {
        await api.patch(`/api/v1/admin/users/${editId}`, form);
      } else {
        await api.post('/api/v1/admin/users', form);
      }
      setShowForm(false); load();
    } catch (e: any) { alert(e?.response?.data?.detail || 'Ошибка'); }
  };

  const toggleBlock = async (u: PlatformUser) => {
    if (!confirm(u.is_active ? 'Заблокировать пользователя?' : 'Разблокировать пользователя?')) return;
    try { await api.patch(`/api/v1/admin/users/${u.id}`, { is_active: !u.is_active }); load(); }
    catch (e: any) { alert(e?.response?.data?.detail || 'Ошибка'); }
  };

  const filtered = users.filter(u =>
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    (u.full_name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>👥 Пользователи</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Управление учётными записями</p>
        </div>
        <div className="flex gap-2">
          <Link to="/admin" className="px-3 py-2 rounded-lg text-sm transition-colors" style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-secondary)' }}>← Админка</Link>
          <button onClick={openCreate} className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ backgroundColor: 'var(--brand)' }}>+ Создать</button>
        </div>
      </div>

      <input type="text" value={search} onChange={e => setSearch(e.target.value)}
        placeholder="Поиск по email или имени..."
        className="w-full p-2.5 rounded-lg border text-sm mb-4"
        style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />

      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-14 rounded-lg animate-pulse" style={{ backgroundColor: 'var(--skeleton)' }} />)}</div>
      ) : (
        <div className="space-y-2">
          {filtered.map(u => (
            <div key={u.id} className="rounded-xl border p-4 transition-all"
              style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between">
                <div className="flex-1" onClick={() => openEdit(u)}>
                  <div className="flex items-center gap-2">
                    <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{u.full_name || u.email}</span>
                    {u.is_superadmin && <Badge variant="success">Superadmin</Badge>}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                    {u.email}
                    {u.tenants?.length > 0 && ` · ${u.tenants.map(t => `${t.tenant_name} (${t.role})`).join(', ')}`}
                    {u.last_login_at && ` · последний вход: ${formatDate(u.last_login_at)}`}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={u.is_active ? 'success' : 'error'}>{u.is_active ? 'Активен' : 'Заблокирован'}</Badge>
                  <button onClick={() => openEdit(u)} className="text-xs px-2 py-1 rounded transition-colors" style={{ color: 'var(--brand)' }}>✏️</button>
                  <button onClick={() => toggleBlock(u)} className="text-xs px-2 py-1 rounded transition-colors" style={{ color: u.is_active ? 'var(--text-muted)' : 'var(--success)' }}>
                    {u.is_active ? '🔒' : '🔓'}
                  </button>
                </div>
              </div>
            </div>
          ))}
          {filtered.length === 0 && <p className="py-8 text-center text-sm" style={{ color: 'var(--text-muted)' }}>Пользователи не найдены</p>}
        </div>
      )}

      <Dialog open={showForm} onClose={() => setShowForm(false)} title={editId ? 'Редактировать пользователя' : 'Создать пользователя'} className="max-w-lg">
        <div className="space-y-3">
          <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Email</label>
            <input value={form.email || ''} onChange={e => setForm({ ...form, email: e.target.value })}
              className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
          <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Имя</label>
            <input value={form.full_name || ''} onChange={e => setForm({ ...form, full_name: e.target.value })}
              className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
          <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Пароль</label>
            <input type="password" value={form.password || ''} onChange={e => setForm({ ...form, password: e.target.value })}
              className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} /></div>
          <div><label className="text-xs" style={{ color: 'var(--text-secondary)' }}>Роль</label>
            <select value={form.role || 'viewer'} onChange={e => setForm({ ...form, role: e.target.value })}
              className="w-full p-2 rounded-lg border text-sm mt-0.5" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}>
              <option value="viewer">Наблюдатель</option>
              <option value="analyst">Аналитик</option>
              <option value="admin">Администратор</option>
            </select></div>
          <div className="flex gap-2">
            <label className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              <input type="checkbox" checked={form.is_superadmin || false} onChange={e => setForm({ ...form, is_superadmin: e.target.checked })} />
              Superadmin (доступ ко всем тенантам)
            </label>
          </div>
          {connections.length > 0 && (
            <div>
              <label className="text-xs mb-1 block" style={{ color: 'var(--text-secondary)' }}>Доступ к базам 1С</label>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {connections.map(c => {
                  const checked = form.allowed_connection_ids?.includes(c.id);
                  return (
                    <label key={c.id} className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: 'var(--text-primary)' }}>
                      <input type="checkbox" checked={checked || false}
                        onChange={e => {
                          const ids = form.allowed_connection_ids || [];
                          setForm({ ...form, allowed_connection_ids: e.target.checked ? [...ids, c.id] : ids.filter((id: string) => id !== c.id) });
                        }} />
                      {c.name}
                      <span className="opacity-50" style={{ color: 'var(--text-muted)' }}>({c.base_url.slice(0, 30)}…)</span>
                    </label>
                  );
                })}
              </div>
              {(!form.allowed_connection_ids || form.allowed_connection_ids.length === 0) && (
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Не выбрано — доступ ко всем базам</p>
              )}
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded-lg border text-sm" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>Отмена</button>
            <button onClick={save}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ backgroundColor: 'var(--brand)' }}>{editId ? 'Сохранить' : 'Создать'}</button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
