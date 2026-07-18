import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './router';
import { ThemeProvider } from '@/shared/lib/theme';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
});

export function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
