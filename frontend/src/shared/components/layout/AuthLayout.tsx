import { Outlet } from 'react-router-dom';

export function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-page)' }}>
      <Outlet />
    </div>
  );
}
