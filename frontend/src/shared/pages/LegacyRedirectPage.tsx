import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function LegacyRedirectPage() {
  const location = useLocation();

  useEffect(() => {
    window.location.href = location.pathname;
  }, [location.pathname]);

  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
      <span className="ml-3 text-[#6b7280]">Загрузка...</span>
    </div>
  );
}
