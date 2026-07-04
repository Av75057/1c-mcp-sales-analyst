import { Outlet } from 'react-router-dom';

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
      <Outlet />
    </div>
  );
}
