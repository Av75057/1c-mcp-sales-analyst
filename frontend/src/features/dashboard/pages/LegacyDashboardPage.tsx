import { useEffect } from 'react';

export default function LegacyDashboardPage() {
  useEffect(() => {
    // Перенаправляем на бэкенд для загрузки Jinja2 SPA
    window.location.href = '/dashboards';
  }, []);

  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
    </div>
  );
}
