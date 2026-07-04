export function buildGaugeOption(_labels: string[], values: number[], _color: string) {
  const val = values[0] || 0;
  const maxVal = 100;
  return {
    series: [{
      type: 'gauge',
      startAngle: 220,
      endAngle: -40,
      center: ['50%', '55%'],
      radius: '70%',
      min: 0,
      max: maxVal,
      progress: { show: true, width: 15 },
      axisLine: { lineStyle: { width: 15, color: [[val / maxVal, '#91cc75'], [1, '#2d3139']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: { fontSize: 20, fontWeight: 'bold', color: '#e5e7eb', formatter: `{value} / ${maxVal}` },
      data: [{ value: val }],
    }],
  };
}
