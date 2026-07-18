export interface SparklinePoint {
  date: string;
  value: number;
}

export interface MetricData {
  current: number;
  previous: number;
  trend_percent: number;
}

export interface ExecutiveKPIResponse {
  period_label: string;
  revenue: MetricData;
  profit: MetricData;
  orders_count: MetricData;
  margin_percent: MetricData;
  top_manager: { name: string; revenue: number };
  sparklines: Record<string, SparklinePoint[]>;
  cache_status: string;
}

export interface GlobalFilters {
  period: string;
  organization?: string;
}

export interface CrossFilter {
  widgetId: string;
  field: string;
  value: string | number;
  label: string;
}

export interface FilterStep {
  id: string;
  widgetId: string;
  field: string;
  value: string | number;
  label: string;
  timestamp: number;
}

export interface KPICardProps {
  title: string;
  metric: MetricData;
  unit?: 'currency' | 'number' | 'percent';
  isInverseTrend?: boolean;
  className?: string;
  widgetId?: string;
  filterField?: string;
  filterValue?: string | number;
  onDrillDown?: () => void;
}
