import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/shared/lib/api';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import { formatCurrency } from '@/shared/lib/utils';
import type { EChartsOption } from 'echarts';

const CHART_TYPES = [
  { value: 'bar', label: 'Столбчатая', icon: '📊' },
  { value: 'line', label: 'Линейная', icon: '📈' },
  { value: 'pie', label: 'Круговая', icon: '🥧' },
  { value: 'area', label: 'С областями', icon: '🏔️' },
  { value: 'gauge', label: 'Индикатор', icon: '🎯' },
];

const QUERY_TEMPLATES = [
  { name: 'Продажи по товарам', query: 'ВЫБРАТЬ Продажи.Номенклатура КАК Товар, СУММА(Продажи.Сумма) КАК Продажи ИЗ РегистрНакопления.Продажи КАК Продажи СГРУППИРОВАТЬ ПО Продажи.Номенклатура УПОРЯДОЧИТЬ ПО Продажи УБЫВ' },
  { name: 'Продажи по менеджерам', query: 'ВЫБРАТЬ Продажи.Ответственный КАК Менеджер, СУММА(Продажи.Сумма) КАК Продажи ИЗ РегистрНакопления.Продажи КАК Продажи СГРУППИРОВАТЬ ПО Продажи.Ответственный УПОРЯДОЧИТЬ ПО Продажи УБЫВ' },
  { name: 'Продажи по дням', query: 'ВЫБРАТЬ ВЫРАЗИТЬ(Продажи.Период КАК ДАТА) КАК Дата, СУММА(Продажи.Сумма) КАК Продажи ИЗ РегистрНакопления.Продажи КАК Продажи СГРУППИРОВАТЬ ПО ВЫРАЗИТЬ(Продажи.Период КАК ДАТА) УПОРЯДОЧИТЬ ПО Дата' },
  { name: 'Продажи по клиентам', query: 'ВЫБРАТЬ Продажи.Контрагент КАК Клиент, СУММА(Продажи.Сумма) КАК Продажи ИЗ РегистрНакопления.Продажи КАК Продажи СГРУППИРОВАТЬ ПО Продажи.Контрагент УПОРЯДОЧИТЬ ПО Продажи УБЫВ' },
  { name: 'Остатки на складах', query: 'ВЫБРАТЬ Запасы.Номенклатура КАК Товар, Запасы.КоличествоОстаток КАК Остаток, Запасы.СуммаОстаток КАК Сумма ИЗ РегистрНакопления.ЗапасыНаСкладах.Остатки КАК Запасы ГДЕ Запасы.КоличествоОстаток > 0' },
  { name: 'Задолженность клиентов', query: 'ВЫБРАТЬ Взаиморасчеты.Контрагент КАК Клиент, -Взаиморасчеты.СуммаОстаток КАК Долг ИЗ РегистрНакопления.Взаиморасчеты.Остатки КАК Взаиморасчеты ГДЕ Взаиморасчеты.СуммаОстаток < 0 УПОРЯДОЧИТЬ ПО Долг УБЫВ' },
];

interface ChartDraft {
  id: string;
  title: string;
  chart_type: string;
  query: string;
}

let chartCounter = 0;

function genId() { return `chart_${++chartCounter}_${Date.now()}`; }

function ChartsTab({ charts, setCharts }: { charts: ChartDraft[]; setCharts: (c: ChartDraft[]) => void }) {
  const [active, setActive] = useState<number>(0);
  const cur = charts[active];

  const update = (patch: Partial<ChartDraft>) => {
    const next = [...charts];
    next[active] = { ...next[active], ...patch };
    setCharts(next);
  };

  return (
    <div className="flex gap-6 h-full">
      <div className="w-56 space-y-1 flex-shrink-0">
        <button onClick={() => { setCharts([...charts, { id: genId(), title: `График ${charts.length + 1}`, chart_type: 'bar', query: '' }]); setActive(charts.length); }}
          className="w-full p-2 rounded-lg border text-sm font-medium transition-colors flex items-center gap-2"
          style={{ borderColor: 'var(--brand)', color: 'var(--brand)' }}>
          + Добавить график
        </button>
        <div className="space-y-0.5 mt-2">
          {charts.map((c, i) => (
            <div key={c.id}
              onClick={() => setActive(i)}
              className="flex items-center gap-2 p-2 rounded-lg text-sm cursor-pointer transition-colors"
              style={{ backgroundColor: i === active ? 'var(--bg-active)' : 'transparent', color: 'var(--text-primary)' }}>
              <span>{CHART_TYPES.find(t => t.value === c.chart_type)?.icon || '📊'}</span>
              <span className="flex-1 truncate">{c.title}</span>
              <button onClick={e => { e.stopPropagation(); setCharts(charts.filter((_, j) => j !== i)); setActive(Math.min(i, charts.length - 2)); }}
                className="text-xs opacity-50 hover:opacity-100">✕</button>
            </div>
          ))}
        </div>
      </div>

      {cur && (
        <div className="flex-1 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Название</label>
              <input value={cur.title} onChange={e => update({ title: e.target.value })}
                className="w-full p-2 rounded-lg border text-sm mt-1" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Тип</label>
              <div className="flex gap-1 mt-1">
                {CHART_TYPES.map(t => (
                  <button key={t.value} onClick={() => update({ chart_type: t.value })}
                    className="flex-1 p-2 rounded-lg text-xs border transition-colors"
                    style={{ backgroundColor: cur.chart_type === t.value ? 'var(--bg-active)' : 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}>
                    {t.icon} {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Запрос 1С</label>
            <div className="flex flex-wrap gap-1 mt-1 mb-2">
              {QUERY_TEMPLATES.map(t => (
                <button key={t.name} onClick={() => update({ query: t.query, title: t.name })}
                  className="text-xs px-2 py-1 rounded border transition-colors"
                  style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                  {t.name}
                </button>
              ))}
            </div>
            <textarea value={cur.query} onChange={e => update({ query: e.target.value })}
              rows={3} className="w-full p-2 rounded-lg border text-sm mt-1 font-mono"
              style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}
              placeholder="Введите запрос или выберите шаблон выше" />
          </div>

          <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
            <div className="text-xs font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Предпросмотр</div>
            <div className="h-64">
              <ChartPreview chart_type={cur.chart_type} title={cur.title} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ChartPreview({ chart_type, title }: { chart_type: string; title: string }) {
  const labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'];
  const values = [120, 200, 150, 80, 70, 110];

  if (chart_type === 'pie') {
    const option: EChartsOption = {
      backgroundColor: 'transparent', title: { text: title, left: 'center', textStyle: { fontSize: 13, color: 'var(--text-primary)' as string } },
      series: [{ type: 'pie', radius: '55%', data: labels.map((name, i) => ({ name, value: values[i] })) }],
    };
    return <EChartsWrapper option={option} height={240} />;
  }

  if (chart_type === 'gauge') {
    const option: EChartsOption = {
      backgroundColor: 'transparent',
      series: [{ type: 'gauge', min: 0, max: 100, detail: { fontSize: 20 }, data: [{ value: 68, name: title }] }],
    };
    return <EChartsWrapper option={option} height={240} />;
  }

  const isArea = chart_type === 'area';
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: { text: title, left: 'center', textStyle: { fontSize: 13, color: 'var(--text-primary)' as string } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: labels, axisLabel: { color: 'var(--text-secondary)' as string } },
    yAxis: { type: 'value', axisLabel: { color: 'var(--text-secondary)' as string }, splitLine: { lineStyle: { color: 'var(--border)' as string } } },
    grid: { left: 50, right: 16, top: 36, bottom: 24 },
    series: [{ type: chart_type as any, data: values, smooth: true, areaStyle: isArea ? {} : undefined, itemStyle: { color: '#3b82f6' } }],
  };
  return <EChartsWrapper option={option} height={240} />;
}

export default function DashboardConstructorPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [tags, setTags] = useState('');
  const [charts, setCharts] = useState<ChartDraft[]>([{ id: genId(), title: 'График 1', chart_type: 'bar', query: '' }]);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!title.trim()) return;
    setSaving(true);
    try {
      await api.post('/api/v2/dashboards', {
        title: title.trim(),
        description: desc.trim(),
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        charts: charts.map(c => ({
          id: c.id, title: c.title,
          chart_config: { chart_type: c.chart_type, title: c.title, x_axis: { field: '', label: '', type: '' }, y_axis: { field: '', label: '', type: '' }, series: [], onec_query: { entity: '', fields: [], period: '' } },
          data: [], position: { x: 0, y: 0, w: 6, h: 4 }, filter_bindings: [],
        })),
      });
      navigate('/library');
    } catch (e) {
      alert('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-page)' }} className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Новый дашборд</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Создайте дашборд с графиками</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate('/library')}
            className="px-4 py-2 rounded-lg border text-sm transition-colors"
            style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>Отмена</button>
          <button onClick={handleSave} disabled={saving || !title.trim()}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50"
            style={{ backgroundColor: 'var(--brand)' }}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <div className="rounded-xl border p-5" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Название дашборда</label>
              <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Мой дашборд"
                className="w-full p-2 rounded-lg border text-sm mt-1" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Описание</label>
              <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Описание дашборда"
                className="w-full p-2 rounded-lg border text-sm mt-1" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Теги (через запятую)</label>
              <input value={tags} onChange={e => setTags(e.target.value)} placeholder="продажи, аналитика"
                className="w-full p-2 rounded-lg border text-sm mt-1" style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
          </div>
        </div>

        <div className="rounded-xl border p-5" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', minHeight: 400 }}>
          <ChartsTab charts={charts} setCharts={setCharts} />
        </div>
      </div>
    </div>
  );
}
