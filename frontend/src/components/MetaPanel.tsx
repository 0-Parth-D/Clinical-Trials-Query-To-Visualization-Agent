import type { Citation, MetaBlock } from '../types/api'

const CT_STUDY = 'https://clinicaltrials.gov/study/'

export type MetaPanelProps = {
  meta: MetaBlock | null
  selection: { citations: Citation[]; label: string } | null
  onClearSelection: () => void
}

export function MetaPanel({ meta, selection, onClearSelection }: MetaPanelProps) {
  if (!meta) {
    return (
      <aside
        className="meta-panel"
        aria-labelledby="meta-heading-empty"
      >
        <h2 id="meta-heading-empty" className="pane-heading">
          Properties
        </h2>
        <p className="muted">Run a query to see filters, data source, and assumptions.</p>
      </aside>
    )
  }

  const warnId = 'meta-warnings-title'

  return (
    <aside
      className="meta-panel"
      aria-labelledby="meta-heading"
    >
      <h2 id="meta-heading" className="pane-heading">
        Properties
      </h2>

      {meta.warnings != null && meta.warnings.length > 0 ? (
        <section
          className="warnings-banner"
          role="region"
          aria-labelledby={warnId}
        >
          <strong id={warnId}>Warnings</strong>
          <ul>
            {meta.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <h3>Source</h3>
      <dl className="meta-dl">
        <dt>Name</dt>
        <dd>{meta.source.name}</dd>
        <dt>API</dt>
        <dd className="mono wrap">{meta.source.api}</dd>
        <dt>Retrieved</dt>
        <dd>
          <time dateTime={meta.source.retrieved_at}>{meta.source.retrieved_at}</time>
        </dd>
        <dt>Trials in aggregation</dt>
        <dd>{meta.source.result_count}</dd>
        {meta.units != null ? (
          <>
            <dt>Units</dt>
            <dd>{meta.units}</dd>
          </>
        ) : null}
        {meta.group_by != null ? (
          <>
            <dt>Group by</dt>
            <dd>{meta.group_by}</dd>
          </>
        ) : null}
      </dl>

      <h3>Filters</h3>
      {Object.keys(meta.filters).length === 0 ? (
        <p className="muted">None</p>
      ) : (
        <pre className="json-block" tabIndex={0}>
          {JSON.stringify(meta.filters, null, 2)}
        </pre>
      )}

      <h3>Assumptions</h3>
      {meta.assumptions.length === 0 ? (
        <p className="muted">None</p>
      ) : (
        <ul className="assumptions">
          {meta.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}

      <h3>Selected data</h3>
      <p className="muted">
        Select a bar, point, or graph edge on the chart to inspect trial excerpts.
      </p>
      {selection == null || selection.citations.length === 0 ? null : (
        <div
          className="selection-block"
          role="region"
          aria-label="Citation details for chart selection"
        >
          <div className="selection-header">
            <span className="mono">{selection.label}</span>
            <button type="button" className="linkish" onClick={onClearSelection}>
              Clear selection
            </button>
          </div>
          <ul className="citations">
            {selection.citations.map((c) => (
              <li key={`${c.nct_id}-${c.excerpt.slice(0, 24)}`}>
                <a
                  href={`${CT_STUDY}${c.nct_id}`}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {c.nct_id}
                  <span className="visually-hidden"> (opens in new tab)</span>
                </a>
                <p className="excerpt">{c.excerpt}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  )
}
