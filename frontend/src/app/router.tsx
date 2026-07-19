import { createBrowserRouter } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { RootLayout } from '@/shared/components/layout/RootLayout';
import { AuthLayout } from '@/shared/components/layout/AuthLayout';

const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'));
const LibraryPage = lazy(() => import('@/features/library/pages/LibraryPage'));
const DashboardViewPage = lazy(() => import('@/features/dashboard/pages/DashboardViewPage'));
const ChatPage = lazy(() => import('@/features/chat/pages/ChatPage'));
const SearchPage = lazy(() => import('@/features/search/pages/SearchPage'));
const AdminDashboardPage = lazy(() => import('@/features/admin/pages/AdminDashboardPage'));
const AdminUsersPage = lazy(() => import('@/features/admin/pages/UsersPage'));
const AdminAuditPage = lazy(() => import('@/features/admin/pages/AuditPage'));
const ProfilePage = lazy(() => import('@/features/profile/pages/ProfilePage'));
const WhatIfPage = lazy(() => import('@/features/whatif/pages/WhatIfPage'));
const AbcXyzPage = lazy(() => import('@/features/analysis/pages/AbcXyzPage'));
const OverviewPage = lazy(() => import('@/features/dashboard/pages/OverviewPage'));
const ExecutiveDashboardPage = lazy(() => import('@/features/dashboard/pages/ExecutiveDashboardPage'));
const DashboardConstructorPage = lazy(() => import('@/features/dashboard/pages/DashboardConstructorPage'));
const LegacyDashboardPage = lazy(() => import('@/features/dashboard/pages/LegacyDashboardPage'));
const DocumentsPage = lazy(() => import('@/features/documents/pages/DocumentsPage'));
const OCRPage = lazy(() => import('@/features/documents/pages/OCRPage'));
const SalesPage = lazy(() => import('@/features/documents/pages/SalesPage'));
const InsightsPage = lazy(() => import('@/features/insights/pages/InsightsPage'));
const StatusPage = lazy(() => import('@/features/status/pages/StatusPage'));
const LegacyRedirectPage = lazy(() => import('@/shared/pages/LegacyRedirectPage'));
const SharedDashboardPage = lazy(() => import('@/features/dashboard/pages/SharedDashboardPage'));
const NotFoundPage = lazy(() => import('@/shared/pages/NotFoundPage'));

function Loading() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
    </div>
  );
}

function LazyPage({ Component }: { Component: React.LazyExoticComponent<React.ComponentType<any>> }) {
  return (
    <Suspense fallback={<Loading />}>
      <Component />
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <LazyPage Component={LoginPage} /> },
    ],
  },
  {
    element: <RootLayout />,
    errorElement: <div className="flex flex-col items-center justify-center h-screen p-8 text-center" style={{ backgroundColor: 'var(--bg-page)' }}>
      <div className="text-4xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Ошибка загрузки страницы</h2>
      <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>Попробуйте обновить страницу</p>
      <button onClick={() => window.location.href = '/'}
        className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors">
        🔄 На главную
      </button>
    </div>,
    children: [
      { index: true, element: <LazyPage Component={OverviewPage} /> },
      { path: '/library', element: <LazyPage Component={LibraryPage} /> },
      { path: '/library/:id', element: <LazyPage Component={DashboardViewPage} /> },
      { path: '/executive', element: <LazyPage Component={ExecutiveDashboardPage} /> },
      { path: '/chat', element: <LazyPage Component={ChatPage} /> },
      { path: '/search', element: <LazyPage Component={SearchPage} /> },
      { path: '/whatif', element: <LazyPage Component={WhatIfPage} /> },
      { path: '/analysis/abc-xyz', element: <LazyPage Component={AbcXyzPage} /> },
      { path: '/dashboards', element: <LazyPage Component={DashboardConstructorPage} /> },
      { path: '/dashboards/new', element: <LazyPage Component={DashboardConstructorPage} /> },
      { path: '/insights', element: <LazyPage Component={InsightsPage} /> },
      { path: '/documents', element: <LazyPage Component={OCRPage} /> },
      { path: '/documents/sales', element: <LazyPage Component={DocumentsPage} /> },
      { path: '/documents', element: <LazyPage Component={LegacyRedirectPage} /> },
      { path: '/sales', element: <LazyPage Component={SalesPage} /> },
      { path: '/status', element: <LazyPage Component={StatusPage} /> },
      { path: '/profile', element: <LazyPage Component={ProfilePage} /> },
      { path: '/admin', element: <LazyPage Component={AdminDashboardPage} /> },
      { path: '/admin/users', element: <LazyPage Component={AdminUsersPage} /> },
      { path: '/admin/audit', element: <LazyPage Component={AdminAuditPage} /> },
      { path: '*', element: <LazyPage Component={NotFoundPage} /> },
    ],
  },
  {
    path: '/share/:token',
    element: <LazyPage Component={SharedDashboardPage} />,
  },
]);
