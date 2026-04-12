import { GOVERNMENT_OFFICES, type GovernmentOffice } from '@/data/government-offices'

/**
 * Scans responseText for mentions of known government offices.
 * Uses case-insensitive substring matching against each office's
 * department_codes. Returns deduplicated offices ordered by first
 * appearance position in the text.
 *
 * Complexity: O(responseText.length × total_department_codes_across_all_offices)
 * — acceptable for 10 offices with ~10 codes each and typical response lengths.
 */
export function detectOfficesInResponse(responseText: string): GovernmentOffice[] {
  if (!responseText) return []

  const lower = responseText.toLowerCase()
  const results: { office: GovernmentOffice; pos: number }[] = []

  for (const office of GOVERNMENT_OFFICES) {
    let firstPos = -1

    for (const code of office.department_codes) {
      const pos = lower.indexOf(code.toLowerCase())
      if (pos !== -1 && (firstPos === -1 || pos < firstPos)) {
        firstPos = pos
      }
    }

    if (firstPos !== -1) {
      results.push({ office, pos: firstPos })
    }
  }

  // Sort by order of first appearance in the response text.
  results.sort((a, b) => a.pos - b.pos)

  return results.map((r) => r.office)
}
