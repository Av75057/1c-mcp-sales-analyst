import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api/adminApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';

export default function AuditPage() {
  const { data: entries, isLoading } = useQuery({
    queryKey: ['admin-audit'],
    queryFn: () => adminApi.getAuditLog(50),
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📋 Аудит</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Журнал действий пользователей</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Последние действия</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <div style={{ color: 'var(--text-secondary)' }}>Загрузка...</div>}
          {entries && entries.length === 0 && (
            <div style={{ color: 'var(--text-secondary)' }}>Нет записей</div>
          )}
          {entries && entries.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                    <th className="text-left py-2 px-2">Время</th>
                    <th className="text-left py-2 px-2">Пользователь</th>
                    <th className="text-left py-2 px-2">Действие</th>
                    <th className="text-left py-2 px-2">Ресурс</th>
                    <th className="text-left py-2 px-2">Детали</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((e: any) => (
                    <tr key={e.id} className="border-b" style={{ borderColor: 'var(--border)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = ''; }}>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-secondary)' }}>{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                      <td className="py-2 px-2" style={{ color: 'var(--text-primary)' }}>{e.user_id?.slice(0, 12) || '-'}</td>
                      <td className="py-2 px-2">
                        <Badge variant={e.action?.includes('delete') ? 'error' : 'default'}>{e.action || '-'}</Badge>
                      </td>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-secondary)' }}>{e.resource_id?.slice(0, 16) || '-'}</td>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-secondary)' }}>{typeof e.details === 'string' ? e.details.slice(0, 60) : JSON.stringify(e.details).slice(0, 60)}</td>
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
