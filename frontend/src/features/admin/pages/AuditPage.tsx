import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { adminApi } from '../api/adminApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';

export default function AuditPage() {
  const { data: entries, isLoading } = useQuery({
    queryKey: ['admin-audit'],
    queryFn: () => adminApi.getAuditLog(100),
    refetchInterval: 15000,
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>📋 Аудит</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Журнал действий администраторов</p>
        </div>
        <div className="flex gap-2">
          {[
            { to: '/admin', label: '📊 Статистика' },
            { to: '/admin/tenants', label: '🏢 Организации' },
          ].map(item => (
            <Link key={item.to} to={item.to}
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-secondary)' }}>
              {item.label}
            </Link>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Последние действия</CardTitle></CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-2">
              {[1,2,3].map(i => <div key={i} className="h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--skeleton)' }} />)}
            </div>
          )}
          {entries && entries.length === 0 && (
            <p className="py-8 text-center" style={{ color: 'var(--text-secondary)' }}>Нет записей аудита</p>
          )}
          {entries && entries.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                    <th className="text-left py-2 px-2 whitespace-nowrap">Время</th>
                    <th className="text-left py-2 px-2">Пользователь</th>
                    <th className="text-left py-2 px-2">Действие</th>
                    <th className="text-left py-2 px-2">Тип</th>
                    <th className="text-left py-2 px-2">Детали</th>
                    <th className="text-left py-2 px-2">IP</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((e: any) => (
                    <tr key={e.id} className="border-b" style={{ borderColor: 'var(--border)' }}>
                      <td className="py-2 px-2 text-xs whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>
                        {e.created_at ? new Date(e.created_at).toLocaleString('ru-RU') : '-'}
                      </td>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-primary)' }}>
                        {e.actor_user_id?.slice(0, 12) || '-'}
                      </td>
                      <td className="py-2 px-2">
                        <Badge variant={e.action?.includes('delete') ? 'error' : e.action?.includes('create') ? 'success' : 'default'}>
                          {e.action || '-'}
                        </Badge>
                      </td>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-secondary)' }}>{e.resource_type || '-'}</td>
                      <td className="py-2 px-2 text-xs max-w-[200px] truncate" style={{ color: 'var(--text-secondary)' }}
                        title={typeof e.details === 'string' ? e.details : JSON.stringify(e.details || '')}>
                        {typeof e.details === 'string' ? e.details.slice(0, 80) : JSON.stringify(e.details || '').slice(0, 80)}
                      </td>
                      <td className="py-2 px-2 text-xs" style={{ color: 'var(--text-muted)' }}>{e.ip_address || '-'}</td>
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
