import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login({ username, password });
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Ошибка входа');
    }
  };

  return (
    <div className="w-full max-w-md p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white">📊 1C Аналитик</h1>
        <p className="text-[#6b7280] mt-2">Войдите в систему</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-[#ef444422] border border-[#ef4444] text-[#ef4444] p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm text-[#9ca3af] mb-1">Имя пользователя</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full bg-[#1a1d23] border border-[#2d3139] rounded-lg p-2.5 text-white outline-none focus:border-brand-500 transition-colors"
            placeholder="admin"
            required
          />
        </div>

        <div>
          <label className="block text-sm text-[#9ca3af] mb-1">Пароль</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-[#1a1d23] border border-[#2d3139] rounded-lg p-2.5 text-white outline-none focus:border-brand-500 transition-colors"
            placeholder="••••••"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {isLoading ? 'Вход...' : 'Войти'}
        </button>
      </form>
    </div>
  );
}
