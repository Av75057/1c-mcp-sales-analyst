export function buildBarOption(labels: string[], values: number[], color: string, horizontal = false) {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: horizontal
      ? { type: 'value', axisLabel: { color: '#6b7280' }, splitLine: { lineStyle: { color: '#2d3139' } } }
      : { type: 'category', data: labels.slice(0, 20), axisLabel: { color: '#6b7280', rotate: 30 }, axisLine: { lineStyle: { color: '#2d3139' } } },
    yAxis: horizontal
      ? { type: 'category', data: labels.slice(0, 15).reverse(), axisLabel: { color: '#9ca3af' }, axisLine: { lineStyle: { color: '#2d3139' } } }
      : { type: 'value', axisLabel: { color: '#6b7280' }, splitLine: { lineStyle: { color: '#2d3139' } }, beginAtZero: true },
    series: [{ type: 'bar', data: horizontal ? values.slice(0, 15).reverse() : values.slice(0, 20), itemStyle: { color } }],
  };
}
