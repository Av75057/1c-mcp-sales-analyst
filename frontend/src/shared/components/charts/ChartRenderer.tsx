import { useMemo } from 'react';
import { EChartsWrapper } from './EChartsWrapper';
import type { ChartConfig } from '@/shared/types/dashboard';
import { buildBarOption } from './options/barChart';
import { buildLineOption } from './options/lineChart';
import { buildPieOption } from './options/pieChart';
import { buildGaugeOption } from './options/gaugeChart';

const COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'];

interface ChartRendererProps {
  config: ChartConfig;
  data: Record<string, unknown>[];
  height?: number;
}

export function ChartRenderer({ config, data, height }: ChartRendererProps) {
  const option = useMemo(() => {
    if (!data?.length) return {};

    const fields = Object.keys(data[0]);
    const labels = data.map((r) => String(r[config.x_axis?.field || fields[0]] ?? ''));
    const valField = config.series?.[0]?.field || fields[1];
    const values = data.map((r) => Number(r[valField]) || 0);
    const color = config.series?.[0]?.color || COLORS[0];
    const chartType = config.chart_type;

    const builders: Record<string, (l: string[], v: number[], c: string) => any> = {
      bar: buildBarOption,
      line: buildLineOption,
      pie: buildPieOption,
      area: (l, v, c) => ({ ...buildLineOption(l, v, c), series: [{ ...buildLineOption(l, v, c).series?.[0], areaStyle: {} }] }),
      horizontal_bar: (l, v, c) => buildBarOption(l, v, c, true),
      gauge: buildGaugeOption,
    };

    const builder = builders[chartType];
    if (builder) {
      return builder(labels, values, color);
    }

    return buildBarOption(labels, values, color);
  }, [config, data]);

  return (
    <EChartsWrapper
      option={option}
      height={height || 400}
    />
  );
}
