import { type FormEvent, useId, useState } from 'react'
import type { QueryRequest } from '../types/api'

export type QueryFormProps = {
  loading: boolean
  onSubmit: (body: QueryRequest) => void
}

function emptyToUndef(s: string): string | undefined {
  const t = s.trim()
  return t === '' ? undefined : t
}

function parseYear(s: string): number | undefined {
  const t = s.trim()
  if (t === '') return undefined
  const n = Number(t)
  return Number.isFinite(n) ? Math.trunc(n) : undefined
}

export function QueryForm({ loading, onSubmit }: QueryFormProps) {
  const uid = useId()
  const qid = `${uid}-q`
  const drugId = `${uid}-drug`
  const cmpId = `${uid}-cmp`
  const condId = `${uid}-cond`
  const phaseId = `${uid}-phase`
  const sponsorId = `${uid}-sponsor`
  const countryId = `${uid}-country`
  const startYId = `${uid}-sy`
  const endYId = `${uid}-ey`
  const extraId = `${uid}-extra`

  const [query, setQuery] = useState(
    'Breast cancer trials in Canada by phase',
  )
  const [drugName, setDrugName] = useState('')
  const [comparisonDrug, setComparisonDrug] = useState('')
  const [condition, setCondition] = useState('')
  const [trialPhase, setTrialPhase] = useState('')
  const [sponsor, setSponsor] = useState('')
  const [country, setCountry] = useState('')
  const [startYear, setStartYear] = useState('')
  const [endYear, setEndYear] = useState('')
  const [extraFiltersJson, setExtraFiltersJson] = useState('')
  const [jsonError, setJsonError] = useState<string | null>(null)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setJsonError(null)
    let extra: Record<string, unknown> | undefined
    const raw = extraFiltersJson.trim()
    if (raw !== '') {
      try {
        const parsed: unknown = JSON.parse(raw)
        if (parsed == null || typeof parsed !== 'object' || Array.isArray(parsed)) {
          throw new Error('extra_filters must be a JSON object')
        }
        extra = parsed as Record<string, unknown>
      } catch {
        setJsonError('Extra filters must be valid JSON (a single object).')
        return
      }
    }
    const cmp = emptyToUndef(comparisonDrug)
    if (cmp != null) {
      extra = { ...extra, comparison_drug: cmp }
    }
    const body: QueryRequest = {
      query: query.trim(),
      drug_name: emptyToUndef(drugName),
      comparison_drug: cmp,
      condition: emptyToUndef(condition),
      trial_phase: emptyToUndef(trialPhase),
      sponsor: emptyToUndef(sponsor),
      country: emptyToUndef(country),
      start_year: parseYear(startYear),
      end_year: parseYear(endYear),
      extra_filters: extra && Object.keys(extra).length > 0 ? extra : undefined,
    }
    onSubmit(body)
  }

  return (
    <form className="query-form" onSubmit={handleSubmit} noValidate>
      {jsonError != null ? (
        <div className="form-error" role="alert" id={`${uid}-json-err`}>
          {jsonError}
        </div>
      ) : null}

      <div className="field">
        <label className="field-label" htmlFor={qid}>
          Question
        </label>
        <textarea
          id={qid}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          required
          aria-required="true"
          placeholder="Natural-language clinical trials question"
          autoComplete="off"
        />
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor={drugId}>
            Drug or intervention
          </label>
          <input
            id={drugId}
            value={drugName}
            onChange={(e) => setDrugName(e.target.value)}
            placeholder="e.g. pembrolizumab"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={cmpId}>
            Comparison drug
          </label>
          <input
            id={cmpId}
            value={comparisonDrug}
            onChange={(e) => setComparisonDrug(e.target.value)}
            placeholder="Second drug for grouped comparison"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={condId}>
            Condition
          </label>
          <input
            id={condId}
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            placeholder="e.g. lung cancer"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={phaseId}>
            Trial phase
          </label>
          <input
            id={phaseId}
            value={trialPhase}
            onChange={(e) => setTrialPhase(e.target.value)}
            placeholder="e.g. PHASE3"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={sponsorId}>
            Sponsor
          </label>
          <input
            id={sponsorId}
            value={sponsor}
            onChange={(e) => setSponsor(e.target.value)}
            autoComplete="organization"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={countryId}>
            Country
          </label>
          <input
            id={countryId}
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            autoComplete="country-name"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={startYId}>
            Start year
          </label>
          <input
            id={startYId}
            value={startYear}
            onChange={(e) => setStartYear(e.target.value)}
            inputMode="numeric"
            placeholder="e.g. 2018"
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={endYId}>
            End year
          </label>
          <input
            id={endYId}
            value={endYear}
            onChange={(e) => setEndYear(e.target.value)}
            inputMode="numeric"
            placeholder="e.g. 2024"
            autoComplete="off"
          />
        </div>
      </div>

      <div className="field">
        <label className="field-label" htmlFor={extraId}>
          Extra filters (JSON object, optional)
        </label>
        <textarea
          id={extraId}
          value={extraFiltersJson}
          onChange={(e) => setExtraFiltersJson(e.target.value)}
          rows={2}
          className="mono"
          placeholder='{"comparison_drug": "other"} merges with comparison drug field'
          aria-invalid={jsonError != null}
          aria-describedby={jsonError != null ? `${uid}-json-err` : undefined}
          autoComplete="off"
        />
      </div>

      <button type="submit" className="primary" disabled={loading}>
        {loading ? 'Running query…' : 'Run query'}
      </button>
    </form>
  )
}
