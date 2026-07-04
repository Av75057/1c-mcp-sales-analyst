import { describe, it, expect } from 'vitest';
import { buildBarOption } from '../../src/shared/components/charts/options/barChart';
import { buildLineOption } from '../../src/shared/components/charts/options/lineChart';
import { buildPieOption } from '../../src/shared/components/charts/options/pieChart';
import { buildGaugeOption } from '../../src/shared/components/charts/options/gaugeChart';

describe('BarChart options', () => {
  it('builds bar chart options', () => {
    const labels = ['A', 'B', 'C'];
    const values = [10, 20, 30];
    const opt = buildBarOption(labels, values, '#ff0000');
    expect(opt.xAxis?.type).toBe('category');
    expect(opt.yAxis?.type).toBe('value');
    expect(opt.series).toHaveLength(1);
    expect(opt.series[0].type).toBe('bar');
    expect(opt.series[0].data).toEqual([10, 20, 30]);
  });

  it('builds horizontal bar options', () => {
    const labels = ['A', 'B'];
    const values = [10, 20];
    const opt = buildBarOption(labels, values, '#000', true);
    expect(opt.xAxis?.type).toBe('value');
    expect(opt.yAxis?.type).toBe('category');
  });

  it('limits data to 20 items', () => {
    const labels = Array.from({ length: 30 }, (_, i) => `Item ${i}`);
    const values = Array.from({ length: 30 }, (_, i) => i);
    const opt = buildBarOption(labels, values, '#000');
    expect(opt.xAxis?.data?.length).toBe(20);
    expect(opt.series[0].data?.length).toBe(20);
  });
});

describe('LineChart options', () => {
  it('builds line chart options', () => {
    const labels = ['2026-01-01', '2026-01-02'];
    const values = [100, 200];
    const opt = buildLineOption(labels, values, '#00ff00');
    expect(opt.xAxis?.type).toBe('category');
    expect(opt.series[0].type).toBe('line');
    expect(opt.series[0].data).toEqual([100, 200]);
    expect(opt.series[0].smooth).toBe(true);
  });
});

describe('PieChart options', () => {
  it('builds pie chart options', () => {
    const labels = ['A', 'B', 'C'];
    const values = [30, 40, 30];
    const opt = buildPieOption(labels, values, '#000');
    expect(opt.series[0].type).toBe('pie');
    expect(opt.series[0].data).toHaveLength(3);
    expect(opt.series[0].data[0].name).toBe('A');
    expect(opt.series[0].data[0].value).toBe(30);
  });

  it('limits pie to 7 segments', () => {
    const labels = Array.from({ length: 10 }, (_, i) => `S${i}`);
    const values = Array.from({ length: 10 }, (_, i) => i * 10);
    const opt = buildPieOption(labels, values, '#000');
    expect(opt.series[0].data?.length).toBe(7);
  });
});

describe('GaugeChart options', () => {
  it('builds gauge chart options', () => {
    const opt = buildGaugeOption(['val'], [75], '#000');
    expect(opt.series[0].type).toBe('gauge');
    expect(opt.series[0].min).toBe(0);
    expect(opt.series[0].max).toBe(100);
    expect(opt.series[0].data[0].value).toBe(75);
  });

  it('handles zero value', () => {
    const opt = buildGaugeOption(['val'], [0], '#000');
    expect(opt.series[0].data[0].value).toBe(0);
  });
});
