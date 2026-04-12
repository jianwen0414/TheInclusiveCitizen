"use client"

import { useState } from 'react'
import { MapPin, Clock, ExternalLink, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { GovernmentOffice } from '@/data/government-offices'
import {
  isOfficeOpen,
  getStatusLabel,
  buildGoogleMapsUrl,
  buildStaticMapUrl,
} from '@/lib/office-hours'

// ---------------------------------------------------------------------------
// Day-range formatting helper
// ---------------------------------------------------------------------------

const DAY_SHORT: Record<string, string> = {
  MON: 'Mon',
  TUE: 'Tue',
  WED: 'Wed',
  THU: 'Thu',
  FRI: 'Fri',
  SAT: 'Sat',
  SUN: 'Sun',
}
const DAY_ORDER = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

function formatDays(days: string[]): string {
  if (days.length === 7) return 'Daily'
  if (
    days.length === 5 &&
    days.every((d, i) => d === ['MON', 'TUE', 'WED', 'THU', 'FRI'][i])
  )
    return 'Mon–Fri'
  if (days.length === 1) return DAY_SHORT[days[0]] ?? days[0]

  const indices = days
    .map((d) => DAY_ORDER.indexOf(d))
    .filter((i) => i !== -1)
    .sort((a, b) => a - b)

  const isConsecutive = indices.every(
    (idx, i) => i === 0 || idx === indices[i - 1] + 1
  )

  if (isConsecutive && indices.length > 1) {
    return `${DAY_SHORT[DAY_ORDER[indices[0]]]}–${DAY_SHORT[DAY_ORDER[indices[indices.length - 1]]]}`
  }

  return days.map((d) => DAY_SHORT[d] ?? d).join(', ')
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface GovernmentOfficeCardProps {
  office: GovernmentOffice
  detectedLanguage: string // ISO code from the pipeline response
}

export function GovernmentOfficeCard({
  office,
  detectedLanguage,
}: GovernmentOfficeCardProps) {
  const [mapError, setMapError] = useState(false)

  const status = isOfficeOpen(office)
  const statusLabel = getStatusLabel(status, detectedLanguage)

  // Resolve office name: prefer detectedLanguage base code, fall back to 'en'.
  const baseLang = detectedLanguage.split('-')[0]
  const officeName =
    office.names[baseLang] ?? office.names['en'] ?? Object.values(office.names)[0]

  const mapUrl = buildStaticMapUrl(office, 400, 160)
  const directionsUrl = buildGoogleMapsUrl(office)

  const statusDotClass =
    status === 'open'
      ? 'bg-green-500'
      : status === 'closed'
        ? 'bg-red-500'
        : 'bg-gray-400'

  return (
    <Card className="overflow-hidden py-0 gap-0 text-sm">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2 px-4 pt-4 pb-3">
        <span
          className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${statusDotClass}`}
          aria-hidden="true"
        />
        <span className="font-semibold text-text-primary leading-snug">
          {officeName}
        </span>
        <span className="ml-auto text-xs text-text-secondary whitespace-nowrap">
          {statusLabel}
        </span>
      </div>

      {/* ── Static map ─────────────────────────────────────── */}
      {!mapError ? (
        <img
          src={mapUrl}
          alt={`Map showing location of ${officeName}`}
          width={400}
          height={160}
          loading="lazy"
          className="w-full h-40 object-cover"
          onError={() => setMapError(true)}
        />
      ) : (
        <div className="w-full h-40 bg-border-subtle flex items-center justify-center">
          <p className="text-xs text-text-secondary">
            {office.coordinates.lat.toFixed(4)}°N,{' '}
            {office.coordinates.lng.toFixed(4)}°E
          </p>
        </div>
      )}

      <CardContent className="px-4 pt-3 pb-4 flex flex-col gap-3">
        {/* ── Operating hours ──────────────────────────────── */}
        <div className="flex gap-3">
          <Clock className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex flex-col gap-0.5 text-text-secondary">
            {office.operating_hours.schedule.map((entry, i) => (
              <span key={i}>
                {formatDays(entry.days)}: {entry.open}–{entry.close}
              </span>
            ))}
            {office.operating_hours.lunch_break && (
              <span>
                Lunch break ({formatDays(office.operating_hours.lunch_break.days)}):{' '}
                {office.operating_hours.lunch_break.start}–
                {office.operating_hours.lunch_break.end}
              </span>
            )}
          </div>
        </div>

        {/* ── Address ──────────────────────────────────────── */}
        <div className="flex gap-3">
          <MapPin className="w-4 h-4 text-text-secondary mt-0.5 shrink-0" aria-hidden="true" />
          <span className="text-text-secondary">{office.address}</span>
        </div>

        {/* ── Disclaimer ───────────────────────────────────── */}
        <div className="flex gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" aria-hidden="true" />
          <p className="text-xs text-amber-700 leading-snug">
            Hours shown are standard operating hours and may differ on public
            holidays or special schedules.
          </p>
        </div>

        {/* ── Get directions button ─────────────────────────── */}
        <Button
          asChild
          className="w-full gap-2"
          variant="outline"
        >
          <a
            href={directionsUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="w-4 h-4" aria-hidden="true" />
            Get directions
          </a>
        </Button>
      </CardContent>
    </Card>
  )
}
