import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function RootLayout() {
  return (
    <div className="flex min-h-screen bg-[#0f1117] text-[#e5e7eb]">
      <Sidebar />
      <main className="flex-1 ml-60 p-6">
        <Outlet />
      </main>
    </div>
  );
}
