import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/shared/lib/utils';

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
  { path: '/documents', icon: '📄', label: 'Документы (OCR)', target: '_blank' },
  { path: '/documents/sales', icon: '📋', label: 'Реализации' },
  { path: '/status', icon: '🔧', label: 'Статус' },
  { path: '/admin', icon: '⚙️', label: 'Админка' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-60 bg-[#1a1d23] border-r border-[#2d3139] flex flex-col z-50">
      <div className="p-4 border-b border-[#2d3139]">
        <h1 className="text-white font-bold text-lg">📊 1C Аналитик</h1>
        <p className="text-[#6b7280] text-xs mt-1">AI-powered analytics</p>
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
                  ? 'text-white bg-[#2563eb22] border-l-2 border-[#2563eb]'
                  : 'text-[#9ca3af] hover:text-white hover:bg-[#22262e]'
              )}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </LinkComponent>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[#2d3139]">
        <Link
          to="/profile"
          className="flex items-center gap-2 text-sm text-[#9ca3af] hover:text-white transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-[#2563eb] flex items-center justify-center text-white text-xs font-bold">
            A
          </div>
          <span>Профиль</span>
        </Link>
      </div>
    </aside>
  );
}
