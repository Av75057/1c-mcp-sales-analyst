import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import NotFoundPage from '../../src/shared/pages/NotFoundPage';
import { RootLayout } from '../../src/shared/components/layout/RootLayout';
import { AuthLayout } from '../../src/shared/components/layout/AuthLayout';

describe('NotFoundPage', () => {
  it('renders 404 message', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>
    );
    expect(screen.getByText('404')).toBeTruthy();
    expect(screen.getByText('Страница не найдена')).toBeTruthy();
    expect(screen.getByText('На главную')).toBeTruthy();
  });

  it('has link to home', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>
    );
    const link = screen.getByText('На главную').closest('a');
    expect(link?.getAttribute('href')).toBe('/');
  });
});

describe('RootLayout', () => {
  it('renders', () => {
    render(
      <MemoryRouter>
        <RootLayout />
      </MemoryRouter>
    );
    expect(screen.getByText(/1C Аналитик/)).toBeTruthy();
  });
});

describe('AuthLayout', () => {
  it('renders children', () => {
    render(
      <MemoryRouter>
        <AuthLayout />
      </MemoryRouter>
    );
    expect(document.querySelector('.min-h-screen')).toBeTruthy();
  });
});
