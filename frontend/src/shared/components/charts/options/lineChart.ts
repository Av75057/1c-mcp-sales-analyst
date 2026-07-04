export function buildLineOption(labels: string[], values: number[], color: string) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: labels, boundaryGap: false, axisLabel: { color: '#6b7280' }, axisLine: { lineStyle: { color: '#2d3139' } } },
    yAxis: { type: 'value', axisLabel: { color: '#6b7280' }, splitLine: { lineStyle: { color: '#2d3139' } }, beginAtZero: true },
    series: [{ type: 'line', data: values, smooth: true, lineStyle: { color, width: 2 }, itemStyle: { color }, symbol: 'circle', symbolSize: 6 }],
  };
}
