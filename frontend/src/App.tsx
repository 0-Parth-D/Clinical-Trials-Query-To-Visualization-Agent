import { useCallback, useState } from 'react'
import { ApiError, formatValidationMessage, postQuery } from './api/client'
import { MetaPanel } from './components/MetaPanel'
import { QueryForm } from './components/QueryForm'
import { VizRenderer } from './components/VizRenderer'
import type { Citation, MetaBlock, QueryRequest, VisualizationResponse } from './types/api'
import './App.css'

/** Fragment links scroll hash targets into view; with `body`/`#root` overflow hidden that breaks the fixed dashboard. */
function goToWorkspacePanel(id: 'query-panel' | 'main-content' | 'inspector-panel') {
  const el = document.getElementById(id)
  if (!(el instanceof HTMLElement)) return
  const stacked = window.matchMedia('(max-width: 1023px)').matches
  el.focus({ preventScroll: true })
  if (stacked) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

export default function App() {
  const [result, setResult] = useState<VisualizationResponse | null>(null)
  const [meta, setMeta] = useState<MetaBlock | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selection, setSelection] = useState<{
    citations: Citation[]
    label: string
  } | null>(null)

  const handleQuery = useCallback(async (body: QueryRequest) => {
    setLoading(true)
    setError(null)
    setSelection(null)
    try {
      const res = await postQuery(body)
      setResult(res)
      setMeta(res.meta)
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatValidationMessage(e.detail))
      } else {
        setError(e instanceof Error ? e.message : String(e))
      }
      setResult(null)
      setMeta(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const onDataFocus = useCallback(
    (p: { citations: Citation[]; label: string }) => {
      setSelection(p)
    },
    [],
  )

  return (
    <>
      <a
        href="#main-content"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault()
          goToWorkspacePanel('main-content')
        }}
      >
        Skip to main content
      </a>
      <div className="app-shell">
        <header className="app-topbar">
          <div className="app-topbar__brand">
            <span className="app-topbar__logo" aria-hidden="true">
              ◆
            </span>
            <div className="app-topbar__titles">
              <span className="app-topbar__title">CT Viz Studio</span>
              <span className="app-topbar__subtitle">
                ClinicalTrials.gov query → chart
              </span>
            </div>
          </div>
          <p className="app-topbar__hint">
            API <code>POST /v1/query</code>
          </p>
        </header>

        <div className="app-dashboard">
          <aside className="app-sidebar" aria-label="Navigation and query">
            <nav className="app-nav" aria-label="Workspace">
              <span className="app-nav__label">Menu</span>
              <ul className="app-nav__list">
                <li>
                  <button
                    type="button"
                    className="app-nav__link app-nav__link--active"
                    onClick={() => goToWorkspacePanel('query-panel')}
                  >
                    Query
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className="app-nav__link"
                    onClick={() => goToWorkspacePanel('main-content')}
                  >
                    Canvas
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    className="app-nav__link"
                    onClick={() => goToWorkspacePanel('inspector-panel')}
                  >
                    Inspect
                  </button>
                </li>
              </ul>
            </nav>

            <div id="query-panel" className="app-sidebar__query" tabIndex={-1}>
              <div className="app-sidebar__query-head">
                <h2 className="app-sidebar__heading">Query</h2>
              </div>
              <QueryForm loading={loading} onSubmit={handleQuery} />
            </div>
          </aside>

          <main id="main-content" className="app-canvas" tabIndex={-1}>
            <div className="app-canvas__chrome">
              <h2 className="app-canvas__title">Dashboard</h2>
              <div className="app-canvas__tabs" role="tablist" aria-label="Canvas mode">
                <span className="app-canvas__tab app-canvas__tab--on" role="tab" aria-selected="true">
                  Visualization
                </span>
              </div>
            </div>

            <div className="app-canvas__stage">
              {error != null ? (
                <div className="error-banner error-banner--canvas" role="alert" aria-live="polite">
                  {error}
                </div>
              ) : null}

              {result != null ? (
                <>
                  <VizRenderer spec={result.visualization} onDataFocus={onDataFocus} />
                  <p className="hint hint--canvas">
                    Type: <code>{result.visualization.type}</code>
                  </p>
                </>
              ) : (
                !error && (
                  <div className="placeholder placeholder--canvas">
                    Run a query from the left panel to render a chart here. Start the API with{' '}
                    <code>uvicorn app.main:app --reload --host 127.0.0.1 --port 8000</code>
                    and this UI with <code>npm run dev</code>.
                  </div>
                )
              )}
            </div>
          </main>

          <aside
            id="inspector-panel"
            className="app-inspector"
            aria-label="Properties and citations"
            tabIndex={-1}
          >
            <MetaPanel
              meta={meta}
              selection={selection}
              onClearSelection={() => {
                setSelection(null)
              }}
            />
          </aside>
        </div>
      </div>
    </>
  )
}
