import type { QueryRequest, VisualizationResponse } from '../types/api'

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, detail: unknown) {
    super(`API error ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function apiBase(): string {
  const env = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (env != null && env.trim() !== '') {
    return env.replace(/\/$/, '')
  }
  return '/api'
}

export async function postQuery(
  body: QueryRequest,
): Promise<VisualizationResponse> {
  const base = apiBase()
  const res = await fetch(`${base}/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail: unknown
    const text = await res.text()
    try {
      detail = JSON.parse(text) as unknown
    } catch {
      detail = text
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<VisualizationResponse>
}

export function formatValidationMessage(detail: unknown): string {
  if (detail == null) return 'Request failed'
  if (typeof detail === 'string') return detail
  if (typeof detail === 'object' && detail !== null && 'detail' in detail) {
    const d = (detail as { detail: unknown }).detail
    if (Array.isArray(d)) {
      return d
        .map((item) => {
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg: unknown }).msg)
          }
          return JSON.stringify(item)
        })
        .join('; ')
    }
  }
  try {
    return JSON.stringify(detail)
  } catch {
    return String(detail)
  }
}
