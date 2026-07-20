import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/shared/lib/utils';
import { useTheme } from '@/shared/lib/theme';
import { useAuthStore } from '@/features/auth/stores/authStore';

const NAV_ITEMS = [
  { path: '/', icon: '📊', label: 'Главная' },
  { path: '/executive', icon: '🎯', label: 'KPI руководителя' },
  { path: '/library', icon: '📚', label: 'Библиотека' },
  { path: '/chat', icon: '💬', label: 'AI Чат' },
  { path: '/search', icon: '🔍', label: 'Поиск' },
  { path: '/analysis/abc-xyz', icon: '📈', label: 'ABC/XYZ' },
  { path: '/whatif', icon: '🔮', label: 'What-If' },
  { path: '/insights', icon: '💡', label: 'Инсайты' },
  { path: '/sales', icon: '📊', label: 'Продажи' },
  { path: '/documents', icon: '📄', label: 'Документы (OCR)' },
  { path: '/documents/sales', icon: '📋', label: 'Реализации' },
  { path: '/status', icon: '🔧', label: 'Статус' },
  { path: '/admin', icon: '⚙️', label: 'Админка' },
];

export function Sidebar() {
  const location = useLocation();
  const { theme, toggle } = useTheme();
  const user = useAuthStore((s) => s.user);
  const displayName = user?.full_name || user?.username || 'Профиль';
  const userEmail = user?.email || '';
  const initial = displayName[0]?.toUpperCase() || 'A';

  return (
    <aside style={{ backgroundColor: 'var(--bg-sidebar)', borderColor: 'var(--border)' }}
      className="fixed left-0 top-0 bottom-0 w-60 border-r flex flex-col z-50">
      <div style={{ borderColor: 'var(--border)' }} className="p-4 border-b">
        <h1 style={{ color: 'var(--text-primary)' }} className="font-bold text-lg">📊 1C Аналитик</h1>
        <p style={{ color: 'var(--text-muted)' }} className="text-xs mt-1">AI-powered analytics</p>
      </div>

      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== '/' && location.pathname.startsWith(item.path + '/'));

          const LinkComponent = (item as any).target ? 'a' : Link;
          const linkProps = (item as any).target
            ? { href: item.path, target: (item as any).target, rel: 'noopener noreferrer' as const }
            : { to: item.path };

          return (
            <LinkComponent
              key={item.path}
              {...(linkProps as any)}
              className={cn(
                'flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                isActive
                  ? 'border-l-2 font-medium'
                  : 'hover:brightness-110'
              )}
              style={{
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'var(--bg-active)' : 'transparent',
                borderLeftColor: isActive ? 'var(--brand)' : 'transparent',
              }}
              onMouseEnter={e => { if (!isActive) e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'; }}
              onMouseLeave={e => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </LinkComponent>
          );
        })}
      </nav>

      <div style={{ borderColor: 'var(--border)' }} className="p-3 border-t space-y-2">
        <button onClick={toggle}
          className="flex items-center gap-3 w-full px-4 py-2 text-sm rounded-lg transition-colors cursor-pointer"
          style={{ color: 'var(--text-secondary)', backgroundColor: 'var(--bg-card)' }}
          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'}
          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'var(--bg-card)'}>
          <span className="text-base">{theme === 'dark' ? '☀️' : '🌙'}</span>
          <span>{theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}</span>
        </button>

        <Link to="/profile"
          className="flex items-center gap-2 text-sm px-2 transition-colors rounded-lg py-1"
          style={{ color: 'var(--text-secondary)' }}>
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
            style={{ backgroundColor: 'var(--brand)' }}>
            {initial}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="truncate font-medium" style={{ color: 'var(--text-primary)' }}>{displayName}</span>
            {userEmail && <span className="text-[10px] truncate" style={{ color: 'var(--text-muted)' }}>{userEmail}</span>}
          </div>
        </Link>
      </div>
    </aside>
  );
}
