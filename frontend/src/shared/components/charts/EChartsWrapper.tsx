import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

interface EChartsWrapperProps {
  option: EChartsOption;
  height?: number | string;
  loading?: boolean;
  onChartClick?: (name: string) => void;
}

export function EChartsWrapper({ option, height = 400, loading = false, onChartClick }: EChartsWrapperProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts>();
  const onClickRef = useRef(onChartClick);
  onClickRef.current = onChartClick;

  useEffect(() => {
    if (!chartRef.current) return;

    instanceRef.current?.dispose();
    const instance = echarts.init(chartRef.current);
    instanceRef.current = instance;

    const resizeObserver = new ResizeObserver(() => instance.resize());
    resizeObserver.observe(chartRef.current);

    // Use built-in ECharts click event — works for all chart types
    instance.on('click', (params: any) => {
      if (!onClickRef.current) return;
      const name = params.name;
      if (name) onClickRef.current(name);
    });

    return () => {
      resizeObserver.disconnect();
      instance.dispose();
    };
  }, []);

  useEffect(() => {
    if (!instanceRef.current) return;
    if (loading) {
      instanceRef.current.showLoading();
    } else {
      instanceRef.current.hideLoading();
      instanceRef.current.setOption(option, { notMerge: true });
    }
  }, [option, loading]);

  return <div ref={chartRef} style={{ width: '100%', height, cursor: onChartClick ? 'pointer' : undefined }} />;
}
