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
        <h1 className="text-2xl font-bold text-white">📋 Аудит</h1>
        <p className="text-sm text-[#6b7280] mt-1">Журнал действий пользователей</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Последние действия</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <div className="text-[#6b7280]">Загрузка...</div>}
          {entries && entries.length === 0 && (
            <div className="text-[#6b7280]">Нет записей</div>
          )}
          {entries && entries.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#6b7280] border-b border-[#2d3139]">
                    <th className="text-left py-2 px-2">Время</th>
                    <th className="text-left py-2 px-2">Пользователь</th>
                    <th className="text-left py-2 px-2">Действие</th>
                    <th className="text-left py-2 px-2">Ресурс</th>
                    <th className="text-left py-2 px-2">Детали</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((e: any) => (
                    <tr key={e.id} className="border-b border-[#2d3139] hover:bg-[#22262e]">
                      <td className="py-2 px-2 text-[#6b7280] text-xs">{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                      <td className="py-2 px-2 text-white">{e.user_id?.slice(0, 12) || '-'}</td>
                      <td className="py-2 px-2">
                        <Badge variant={e.action?.includes('delete') ? 'error' : 'default'}>{e.action || '-'}</Badge>
                      </td>
                      <td className="py-2 px-2 text-[#9ca3af] text-xs">{e.resource_id?.slice(0, 16) || '-'}</td>
                      <td className="py-2 px-2 text-[#6b7280] text-xs">{typeof e.details === 'string' ? e.details.slice(0, 60) : JSON.stringify(e.details).slice(0, 60)}</td>
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
