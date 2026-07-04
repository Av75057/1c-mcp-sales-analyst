import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../../src/shared/components/layout/Sidebar';

describe('Sidebar', () => {
  it('renders all navigation items', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    expect(screen.getByText('Дашборд')).toBeTruthy();
    expect(screen.getByText('Библиотека')).toBeTruthy();
    expect(screen.getByText('AI Чат')).toBeTruthy();
    expect(screen.getByText('Поиск')).toBeTruthy();
    expect(screen.getByText('ABC/XYZ')).toBeTruthy();
    expect(screen.getByText('What-If')).toBeTruthy();
    expect(screen.getByText('Инсайты')).toBeTruthy();
    expect(screen.getByText('Продажи')).toBeTruthy();
    expect(screen.getByText('Документы (OCR)')).toBeTruthy();
    expect(screen.getByText('Реализации')).toBeTruthy();
    expect(screen.getByText('Статус')).toBeTruthy();
    expect(screen.getByText('Админка')).toBeTruthy();
    expect(screen.getByText('Профиль')).toBeTruthy();
  });

  it('renders app title', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    expect(screen.getByText(/1C Аналитик/)).toBeTruthy();
  });

  it('renders all items as links', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThanOrEqual(13);
  });
});
