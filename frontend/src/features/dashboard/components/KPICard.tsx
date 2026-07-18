import React, { useMemo } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import type { KPICardProps } from '../types/kpi';

export const KPICard: React.FC<KPICardProps> = React.memo(({
  title,
  metric,
  unit = 'currency',
  isInverseTrend = false,
  className = '',
}) => {
  const formattedValue = useMemo(() => {
    if (unit === 'currency') {
      return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(metric.current);
    }
    if (unit === 'percent') {
      return `${metric.current.toFixed(1)}%`;
    }
    return new Intl.NumberFormat('ru-RU').format(metric.current);
  }, [metric.current, unit]);

  const isPositive = isInverseTrend ? metric.trend_percent < 0 : metric.trend_percent > 0;
  const isNeutral = metric.trend_percent === 0;

  const trendColor = isNeutral ? 'text-gray-500' : (isPositive ? 'text-green-600' : 'text-red-600');
  const TrendIcon = isNeutral ? Minus : (isPositive ? ArrowUpRight : ArrowDownRight);

  return (
    <div className={`rounded-xl border p-4 transition-all duration-200 ${className}`}
      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
      <div className="text-sm font-medium mb-1 truncate" style={{ color: 'var(--text-secondary)' }} title={title}>
        {title}
      </div>

      <div className="text-2xl font-bold mb-3 tracking-tight" style={{ color: 'var(--text-primary)' }}>
        {formattedValue}
      </div>

      <div className="flex items-end justify-between">
        <div className="flex flex-col">
          <div className={`flex items-center text-sm font-semibold ${trendColor}`}>
            <TrendIcon className="w-4 h-4 mr-1" />
            {isNeutral ? '0.0%' : `${Math.abs(metric.trend_percent).toFixed(1)}%`}
          </div>
          <span className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            к пред. периоду
          </span>
        </div>
      </div>
    </div>
  );
});

KPICard.displayName = 'KPICard';
