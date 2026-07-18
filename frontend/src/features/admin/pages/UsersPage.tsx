import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api/adminApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';

export default function UsersPage() {
  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.getUsers(),
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>👥 Пользователи</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Управление пользователями системы</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Список пользователей</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <div style={{ color: 'var(--text-secondary)' }}>Загрузка...</div>}
          {users && users.length === 0 && (
            <div style={{ color: 'var(--text-secondary)' }}>Нет пользователей</div>
          )}
          {users && users.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                    <th className="text-left py-2 px-2">Имя</th>
                    <th className="text-left py-2 px-2">Email</th>
                    <th className="text-left py-2 px-2">Роль</th>
                    <th className="text-left py-2 px-2">Статус</th>
                    <th className="text-left py-2 px-2">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u: any) => (
                    <tr key={u.id} className="border-b" style={{ borderColor: 'var(--border)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = ''; }}>
                      <td className="py-2 px-2" style={{ color: 'var(--text-primary)' }}>{u.username}</td>
                      <td className="py-2 px-2" style={{ color: 'var(--text-secondary)' }}>{u.email || '-'}</td>
                      <td className="py-2 px-2">
                        <Badge variant={u.role === 'admin' ? 'success' : 'secondary'}>{u.role}</Badge>
                      </td>
                      <td className="py-2 px-2">
                        <span className={`text-xs px-2 py-0.5 rounded ${u.is_active ? 'bg-success/20 text-success' : 'bg-error/20 text-error'}`}>
                          {u.is_active ? 'Активен' : 'Заблокирован'}
                        </span>
                      </td>
                      <td className="py-2 px-2" style={{ color: 'var(--text-secondary)' }}>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
