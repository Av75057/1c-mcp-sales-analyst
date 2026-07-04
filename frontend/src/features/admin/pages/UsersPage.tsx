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
        <h1 className="text-2xl font-bold text-white">👥 Пользователи</h1>
        <p className="text-sm text-[#6b7280] mt-1">Управление пользователями системы</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Список пользователей</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <div className="text-[#6b7280]">Загрузка...</div>}
          {users && users.length === 0 && (
            <div className="text-[#6b7280]">Нет пользователей</div>
          )}
          {users && users.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#6b7280] border-b border-[#2d3139]">
                    <th className="text-left py-2 px-2">Имя</th>
                    <th className="text-left py-2 px-2">Email</th>
                    <th className="text-left py-2 px-2">Роль</th>
                    <th className="text-left py-2 px-2">Статус</th>
                    <th className="text-left py-2 px-2">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u: any) => (
                    <tr key={u.id} className="border-b border-[#2d3139] hover:bg-[#22262e]">
                      <td className="py-2 px-2 text-white">{u.username}</td>
                      <td className="py-2 px-2 text-[#9ca3af]">{u.email || '-'}</td>
                      <td className="py-2 px-2">
                        <Badge variant={u.role === 'admin' ? 'success' : 'secondary'}>{u.role}</Badge>
                      </td>
                      <td className="py-2 px-2">
                        <span className={`text-xs px-2 py-0.5 rounded ${u.is_active ? 'bg-success/20 text-success' : 'bg-error/20 text-error'}`}>
                          {u.is_active ? 'Активен' : 'Заблокирован'}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-[#6b7280]">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
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
