/** Mirrors backend `VizType` and response models (see app/schemas/). */

export type VizType =
  | 'bar_chart'
  | 'grouped_bar_chart'
  | 'time_series'
  | 'scatter_plot'
  | 'histogram'
  | 'network_graph'

export interface Citation {
  nct_id: string
  excerpt: string
}

export interface NetworkNode {
  id: string
  label: string
  kind: string
}

export interface NetworkEdge {
  source: string
  target: string
  weight: number
  citations?: Citation[]
}

export type DataRow = Record<string, unknown>

export interface VisualizationSpec {
  type: VizType
  title: string
  encoding: Record<string, unknown>
  data: DataRow[]
}

export interface SourceMeta {
  name: string
  api: string
  retrieved_at: string
  result_count: number
}

export interface MetaBlock {
  units: string | null
  sort: string | null
  time_granularity: string | null
  group_by: string | null
  filters: Record<string, unknown>
  source: SourceMeta
  assumptions: string[]
  warnings: string[] | null
}

export interface VisualizationResponse {
  visualization: VisualizationSpec
  meta: MetaBlock
}

export interface QueryRequest {
  query: string
  drug_name?: string | null
  /** Second drug for grouped A vs B charts; sent as its own field (not only extra_filters). */
  comparison_drug?: string | null
  condition?: string | null
  trial_phase?: string | null
  sponsor?: string | null
  country?: string | null
  start_year?: number | null
  end_year?: number | null
  extra_filters?: Record<string, unknown> | null
}
