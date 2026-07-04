import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { useEffect, type ReactNode } from 'react';
import { useAuthStore } from '@/features/auth/stores/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AuthProvider({ children }: { children: ReactNode }) {
  const checkAuth = useAuthStore((s) => s.checkAuth);
  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    if (token) {
      checkAuth();
    }
  }, [token, checkAuth]);

  return <>{children}</>;
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>{children}</AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
