import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-20">
      <div className="text-6xl mb-4">404</div>
      <h2 className="text-2xl text-white mb-2">Страница не найдена</h2>
      <p className="text-[#6b7280] mb-6">Такой страницы не существует</p>
      <Link to="/" className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg transition-colors">
        На главную
      </Link>
    </div>
  );
}
