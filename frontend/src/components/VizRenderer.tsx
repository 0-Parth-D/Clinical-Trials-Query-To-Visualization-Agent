import { useMemo } from 'react'
import ReactEcharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type {
  CallbackDataParams,
  TopLevelFormatterParams,
} from 'echarts/types/dist/shared'
import type { Citation, DataRow, VisualizationSpec } from '../types/api'

/** ECharts does not inherit page CSS; keep in sync with `index.css` (--font-sans). */
const CHART_FONT =
  "'Montserrat', 'Segoe UI', system-ui, -apple-system, sans-serif"

const AXIS_LABEL_COLOR = '#2f4f5c'

function chartTitle(text: string): NonNullable<EChartsOption['title']> {
  return {
    text,
    left: 0,
    top: 6,
    textStyle: {
      fontSize: 16,
      fontWeight: 600,
      fontFamily: CHART_FONT,
      color: '#1b2f36',
    },
  }
}

const defaultAxisName = {
  fontFamily: CHART_FONT,
  fontSize: 12,
  color: AXIS_LABEL_COLOR,
}

function asStr(v: unknown): string {
  if (v == null) return ''
  return String(v)
}

function rowCitations(row: DataRow): Citation[] {
  const c = row.citations
  if (!Array.isArray(c)) return []
  return c.filter(
    (x): x is Citation =>
      x != null &&
      typeof x === 'object' &&
      'nct_id' in x &&
      typeof (x as Citation).nct_id === 'string',
  ) as Citation[]
}

/** Short HTML line; full text and citations stay in Properties after click. */
function tooltipPropertiesHint(): string {
  return `<div style="font-size:11px;opacity:.72;margin-top:6px;max-width:14rem;line-height:1.35">Click the chart for full details in Properties.</div>`
}

type FocusPayload = { citations: Citation[]; label: string }

function buildBarLike(
  spec: VisualizationSpec,
  xKey: string,
  yKey: string,
  lineMode: boolean,
): EChartsOption {
  const { data } = spec
  const xs = data.map((d) => asStr(d[xKey]))
  const ys = data.map((d) => Number(d[yKey]) || 0)
  const bottomPad = xs.some((x) => x.length > 12) ? 88 : 56
  return {
    textStyle: { fontFamily: CHART_FONT },
    title: chartTitle(spec.title),
    grid: {
      left: 56,
      right: 28,
      top: 64,
      bottom: bottomPad,
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      formatter: (items: CallbackDataParams | CallbackDataParams[]) => {
        const arr = Array.isArray(items) ? items : [items]
        const p = arr[0]
        if (!p) return ''
        const i = p.dataIndex ?? 0
        const row = data[i]
        if (!row) return ''
        return `<div><strong>${asStr(row[xKey])}</strong>: ${ys[i]}</div>${tooltipPropertiesHint()}`
      },
    },
    xAxis: {
      type: 'category',
      data: xs,
      axisLabel: {
        rotate: xs.some((x) => x.length > 14) ? 30 : 0,
        fontFamily: CHART_FONT,
        color: AXIS_LABEL_COLOR,
      },
    },
    yAxis: {
      type: 'value',
      name: 'trials',
      nameTextStyle: defaultAxisName,
      axisLabel: { fontFamily: CHART_FONT, color: AXIS_LABEL_COLOR },
    },
    series: [
      {
        type: lineMode ? 'line' : 'bar',
        data: ys,
        smooth: lineMode,
        itemStyle: lineMode ? undefined : { borderRadius: [4, 4, 0, 0] },
      },
    ],
  }
}

function buildGroupedBar(spec: VisualizationSpec, enc: Record<string, unknown>): EChartsOption {
  const xKey = asStr(enc.x)
  const yKey = asStr(enc.y)
  const seriesKey = asStr(enc.series)
  const { data } = spec
  const categories = [...new Set(data.map((d) => asStr(d[xKey])))]
  const seriesNames = [...new Set(data.map((d) => asStr(d[seriesKey])))]
  const series = seriesNames.map((sName) => ({
    name: sName,
    type: 'bar' as const,
    emphasis: { focus: 'series' as const },
    data: categories.map((cat) => {
      const row = data.find(
        (d) => asStr(d[xKey]) === cat && asStr(d[seriesKey]) === sName,
      )
      return row ? Number(row[yKey]) || 0 : 0
    }),
  }))
  return {
    textStyle: { fontFamily: CHART_FONT },
    title: chartTitle(spec.title),
    legend: {
      bottom: 4,
      type: 'scroll',
      textStyle: { fontFamily: CHART_FONT, color: AXIS_LABEL_COLOR },
    },
    grid: { left: 56, right: 28, top: 64, bottom: 92, containLabel: true },
    tooltip: {
      trigger: 'item',
      axisPointer: { type: 'shadow' },
      confine: true,
      formatter: (item: TopLevelFormatterParams) => {
        if (Array.isArray(item)) return ''
        const cat = asStr(item.name)
        const sName = asStr(item.seriesName)
        const v = item.value
        const val = Array.isArray(v) ? v[1] : v
        return `<div><strong>${cat}</strong> · ${sName}: <strong>${val}</strong></div>${tooltipPropertiesHint()}`
      },
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { fontFamily: CHART_FONT, color: AXIS_LABEL_COLOR },
    },
    yAxis: {
      type: 'value',
      name: 'trials',
      nameTextStyle: defaultAxisName,
      axisLabel: { fontFamily: CHART_FONT, color: AXIS_LABEL_COLOR },
    },
    series,
  }
}

function buildScatter(spec: VisualizationSpec, enc: Record<string, unknown>): EChartsOption {
  const xKey = asStr(enc.x)
  const yKey = asStr(enc.y)
  const { data } = spec
  const pts = data.map((d, i) => [Number(d[xKey]) || 0, Number(d[yKey]) || 0, i])
  return {
    textStyle: { fontFamily: CHART_FONT },
    title: chartTitle(spec.title),
    grid: { left: 60, right: 28, top: 64, bottom: 52, containLabel: true },
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (item: TopLevelFormatterParams) => {
        if (Array.isArray(item)) return ''
        const raw = item.value
        if (!Array.isArray(raw) || raw.length < 3) return ''
        return `<div>${xKey}: ${raw[0]}, ${yKey}: ${raw[1]}</div>${tooltipPropertiesHint()}`
      },
    },
    xAxis: {
      type: 'value',
      name: xKey,
      scale: true,
      nameTextStyle: defaultAxisName,
      axisLabel: { fontFamily: CHART_FONT, color: AXIS_LABEL_COLOR },
    },
    yAxis: {
      type: 'value',
      name: yKey,
      scale: true,
      nameTextStyle: defaultAxisName,
      axisLabel: { fontFamily: CHART_FONT, color: AXIS_LABEL_COLOR },
    },
    series: [{ type: 'scatter', symbolSize: 10, data: pts }],
  }
}

function buildGraph(spec: VisualizationSpec): EChartsOption {
  const row0 = spec.data[0]
  if (!row0) {
    return { textStyle: { fontFamily: CHART_FONT }, title: chartTitle(spec.title) }
  }
  const nodes = row0.nodes
  const edges = row0.edges
  if (!Array.isArray(nodes) || !Array.isArray(edges)) {
    return { textStyle: { fontFamily: CHART_FONT }, title: chartTitle(spec.title) }
  }
  const nodeList = nodes as Array<Record<string, unknown>>
  const edgeList = edges as Array<Record<string, unknown>>
  return {
    textStyle: { fontFamily: CHART_FONT },
    title: chartTitle(spec.title),
    tooltip: {
      confine: true,
      formatter: (p: TopLevelFormatterParams) => {
        if (Array.isArray(p)) return ''
        if (p.dataType === 'edge') {
          const s = asStr((p.data as { source?: unknown }).source)
          const t = asStr((p.data as { target?: unknown }).target)
          const w = (p.data as { value?: unknown }).value
          return `<div>${s} → ${t}: ${w}</div>${tooltipPropertiesHint()}`
        }
        const n = p.data as { name?: unknown }
        return `<div>${asStr(n.name)}</div>${tooltipPropertiesHint()}`
      },
    },
    legend: { bottom: 0, data: ['Sponsor', 'Drug'] },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        force: { repulsion: 120, edgeLength: [40, 140] },
        categories: [{ name: 'Sponsor' }, { name: 'Drug' }],
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          fontFamily: CHART_FONT,
          color: AXIS_LABEL_COLOR,
        },
        lineStyle: { color: 'source', curveness: 0.15 },
        emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
        data: nodeList.map((n) => ({
          id: asStr(n.id),
          name: asStr(n.label),
          category: asStr(n.kind) === 'sponsor' ? 0 : 1,
          symbolSize: asStr(n.kind) === 'sponsor' ? 26 : 20,
        })),
        links: edgeList.map((e) => ({
          source: asStr(e.source),
          target: asStr(e.target),
          value: Number(e.weight) || 0,
        })),
        edgeSymbol: ['none', 'arrow'],
      },
    ],
  }
}

function graphClickHandler(
  params: CallbackDataParams,
  spec: VisualizationSpec,
  onFocus: (p: FocusPayload) => void,
) {
  const row0 = spec.data[0]
  if (!row0 || !Array.isArray(row0.edges)) return
  const edgeList = row0.edges as Array<Record<string, unknown>>
  if (params.dataType === 'edge') {
    const d = params.data as { source?: unknown; target?: unknown }
    const src = asStr(d.source)
    const tgt = asStr(d.target)
    const edge = edgeList.find(
      (e) => asStr(e.source) === src && asStr(e.target) === tgt,
    )
    const cites = (edge?.citations as Citation[] | undefined) ?? []
    onFocus({ citations: cites, label: `${src} → ${tgt}` })
    return
  }
  if (params.dataType === 'node') {
    const id = asStr((params.data as { id?: unknown }).id)
    const cites: Citation[] = []
    for (const e of edgeList) {
      if (asStr(e.source) === id || asStr(e.target) === id) {
        const c = e.citations
        if (Array.isArray(c)) cites.push(...(c as Citation[]))
      }
    }
    const uniq = new Map(cites.map((c) => [c.nct_id, c]))
    onFocus({ citations: [...uniq.values()], label: id })
  }
}

export type VizRendererProps = {
  spec: VisualizationSpec
  onDataFocus: (payload: FocusPayload) => void
}

export function VizRenderer({ spec, onDataFocus }: VizRendererProps) {
  const enc = spec.encoding as Record<string, unknown>

  const option = useMemo((): EChartsOption => {
    switch (spec.type) {
      case 'grouped_bar_chart':
        return buildGroupedBar(spec, enc)
      case 'time_series': {
        const xKey = asStr(enc.x)
        const yKey = asStr(enc.y)
        return buildBarLike(spec, xKey, yKey, true)
      }
      case 'histogram': {
        const xKey = asStr(enc.x)
        const yKey = asStr(enc.y)
        return buildBarLike(spec, xKey, yKey, false)
      }
      case 'scatter_plot':
        return buildScatter(spec, enc)
      case 'network_graph':
        return buildGraph(spec)
      default: {
        const xKey = asStr(enc.x)
        const yKey = asStr(enc.y)
        return buildBarLike(spec, xKey, yKey, false)
      }
    }
  }, [spec, enc])

  const onEvents = useMemo(() => {
    const click = (params: CallbackDataParams) => {
      if (spec.type === 'network_graph') {
        graphClickHandler(params, spec, onDataFocus)
        return
      }
      if (spec.type === 'grouped_bar_chart') {
        const xKey = asStr(enc.x)
        const seriesKey = asStr(enc.series)
        const cat = asStr(params.name)
        const sName = asStr(params.seriesName)
        const row = spec.data.find(
          (d) => asStr(d[xKey]) === cat && asStr(d[seriesKey]) === sName,
        )
        if (row) {
          onDataFocus({ citations: rowCitations(row), label: `${cat} · ${sName}` })
        }
        return
      }
      if (
        spec.type === 'bar_chart' ||
        spec.type === 'time_series' ||
        spec.type === 'histogram'
      ) {
        const i = params.dataIndex
        if (typeof i === 'number' && spec.data[i]) {
          const row = spec.data[i]
          const xKey = asStr(enc.x)
          onDataFocus({ citations: rowCitations(row), label: asStr(row[xKey]) })
        }
        return
      }
      if (spec.type === 'scatter_plot') {
        const raw = params.value
        if (Array.isArray(raw) && raw.length >= 3) {
          const i = Number(raw[2])
          const row = spec.data[i]
          if (row) {
            onDataFocus({
              citations: rowCitations(row),
              label: asStr(row.nct_id),
            })
          }
        }
      }
    }
    return { click }
  }, [spec, enc, onDataFocus])

  const chartHeight = 'clamp(20rem, calc(100dvh - 12.5rem), 56rem)'

  return (
    <figure
      className="viz-chart"
      style={{ width: '100%', minHeight: '20rem', flex: 1 }}
      aria-label={`${spec.title}. Interactive chart; select a data element to view citations below or in the properties panel.`}
    >
      <ReactEcharts
        className="viz-echarts"
        option={option}
        style={{ height: chartHeight, width: '100%', minHeight: '20rem' }}
        onEvents={onEvents}
        notMerge
        lazyUpdate
      />
    </figure>
  )
}
