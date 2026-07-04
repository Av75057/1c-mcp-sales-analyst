import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../../src/features/auth/stores/authStore';

describe('AuthStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  });

  it('initial state has no user', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });

  it('logout clears everything', () => {
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('sets loading on login attempt', async () => {
    const loginPromise = useAuthStore.getState().login({ username: 'test', password: 'test' });
    expect(useAuthStore.getState().isLoading).toBe(true);
    await loginPromise.catch(() => {});
  });

  it('logout clears localStorage', () => {
    localStorage.setItem('access_token', 'test-token');
    useAuthStore.getState().logout();
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
