import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/stores/authStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';

export default function ProfilePage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const generateApiKey = () => {
    const key = '1c_' + Array.from({ length: 32 }, () =>
      'abcdefghijklmnopqrstuvwxyz0123456789'.charAt(Math.floor(Math.random() * 36))
    ).join('');
    setApiKey(key);
    navigator.clipboard.writeText(key);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>👤 Профиль</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Настройки пользователя</p>
      </div>

      <div className="space-y-4">
        {/* User info */}
        <Card>
          <CardHeader><CardTitle>Информация</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-brand-600 flex items-center justify-center text-white text-lg font-bold">
                {user?.username?.charAt(0).toUpperCase() || '?'}
              </div>
              <div>
                <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{user?.username || 'Неизвестно'}</div>
                <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{user?.email || 'Нет email'}</div>
              </div>
              <div className="ml-auto">
                <Badge variant={user?.role === 'admin' ? 'success' : 'default'}>{user?.role || 'user'}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Key */}
        <Card>
          <CardHeader><CardTitle>API Ключ</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Ключ для доступа к API 1С Аналитика из внешних систем</p>
            {apiKey ? (
              <div className="border rounded-lg p-3 font-mono text-xs text-brand-500 break-all" style={{ backgroundColor: 'var(--bg-page)', borderColor: 'var(--border)' }}>
                {apiKey}
              </div>
            ) : (
              <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>Нажмите «Сгенерировать» для создания нового ключа</div>
            )}
            <Button onClick={generateApiKey} size="sm">
              🔑 Сгенерировать
            </Button>
          </CardContent>
        </Card>

        {/* Logout */}
        <Card>
          <CardContent className="pt-4">
            <Button variant="destructive" onClick={handleLogout}>
              🚪 Выйти
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
