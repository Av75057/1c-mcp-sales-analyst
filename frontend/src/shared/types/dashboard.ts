export interface Axis {
  field: string;
  label: string;
  type: string;
}

export interface Series {
  name: string;
  field: string;
  color: string;
}

export interface OnecQuery {
  entity: string;
  fields: string[];
  period: string;
  aggregation?: string;
}

export interface HeatmapConfig {
  x_field: string;
  y_field: string;
  value_field: string;
}

export interface TreemapConfig {
  category_field: string;
  value_field: string;
  max_depth?: number;
}

export interface SankeyConfig {
  source_field: string;
  target_field: string;
  value_field: string;
}

export interface GaugeConfig {
  value_field: string;
  min: number;
  max: number;
  target?: number;
}

export interface RadarConfig {
  dimensions: string[];
  value_field: string;
}

export interface ChartConfig {
  chart_type: string;
  title: string;
  subtitle?: string;
  x_axis: Axis;
  y_axis: Axis;
  series: Series[];
  filters?: Record<string, unknown>[];
  group_by?: string[];
  order_by?: Record<string, string>;
  limit?: number;
  onec_query: OnecQuery;
  heatmap?: HeatmapConfig;
  treemap?: TreemapConfig;
  sankey?: SankeyConfig;
  gauge?: GaugeConfig;
  radar?: RadarConfig;
}

export interface ChartItem {
  id: string;
  title: string;
  chart_config: ChartConfig;
  data: Record<string, unknown>[];
  position: { x: number; y: number; w: number; h: number };
  filter_bindings: string[];
}

export interface Dashboard {
  id: string;
  owner_id: string;
  title: string;
  description?: string;
  charts: ChartItem[];
  tags: string[];
  is_public: boolean;
  is_favorite: boolean;
  refresh_interval_minutes: number;
  view_count: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardListResponse {
  status: string;
  dashboards: Dashboard[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface ListFilters {
  search?: string;
  tags?: string;
  is_favorite?: boolean;
  sort_by?: string;
  page?: number;
  per_page?: number;
}

export interface DashboardCreatePayload {
  title: string;
  description?: string;
  charts: ChartItem[];
  tags?: string[];
  is_public?: boolean;
  is_favorite?: boolean;
  refresh_interval_minutes?: number;
}

export interface DashboardUpdatePayload {
  title?: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
  is_favorite?: boolean;
  charts?: ChartItem[];
}
