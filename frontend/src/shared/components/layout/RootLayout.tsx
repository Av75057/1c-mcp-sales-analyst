import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function RootLayout() {
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: 'var(--bg-page)', color: 'var(--text-primary)' }}>
      <Sidebar />
      <main className="flex-1 ml-60 p-6">
        <Outlet />
      </main>
    </div>
  );
}
