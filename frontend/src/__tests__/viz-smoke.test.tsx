import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { render } from '@testing-library/react'

import { VizRenderer } from '../components/VizRenderer'
import type { VisualizationResponse } from '../types/api'

const here = dirname(fileURLToPath(import.meta.url))

function loadExample(filename: string): VisualizationResponse {
  const p = join(here, '..', '..', '..', 'examples', filename)
  return JSON.parse(readFileSync(p, 'utf-8')) as VisualizationResponse
}

const EXAMPLE_FILES = [
  'example_01_bar_chart_phase.json',
  'example_02_time_series.json',
  'example_03_histogram_start_year.json',
  'example_04_network_sponsor_drug.json',
  'example_05_grouped_bar_two_drugs.json',
  'example_06_scatter_enrollment_vs_year.json',
  'example_07_geographic_country_recruiting.json',
]

describe('VizRenderer + fixture examples', () => {
  for (const file of EXAMPLE_FILES) {
    it(`renders ${file} without throwing`, () => {
      const payload = loadExample(file)
      expect(payload.visualization.type).toBeTruthy()
      expect(Array.isArray(payload.visualization.data)).toBe(true)
      const { container } = render(
        <VizRenderer
          spec={payload.visualization}
          onDataFocus={() => {
            /* noop */
          }}
        />,
      )
      expect(container.querySelector('.viz-chart')).toBeTruthy()
    })
  }
})
