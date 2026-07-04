const PIE_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4'];

export function buildPieOption(labels: string[], values: number[], _color: string) {
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['0%', '70%'],
      center: ['50%', '50%'],
      data: labels.slice(0, 7).map((name, i) => ({
        name,
        value: values[i] || 0,
        itemStyle: { color: PIE_COLORS[i % PIE_COLORS.length] },
      })),
      label: { color: '#9ca3af', formatter: '{b}\n{d}%' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
    }],
  };
}
