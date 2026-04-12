import type { GovernmentOffice } from '@/data/government-offices'

// ---------------------------------------------------------------------------
// isOfficeOpen
// ---------------------------------------------------------------------------

export function isOfficeOpen(
  office: GovernmentOffice
): 'open' | 'closed' | 'unknown' {
  try {
    const tz = 'Asia/Kuala_Lumpur'
    const now = new Date()

    // Extract current weekday abbreviation (MON, TUE, …) in Malaysia time.
    const dayStr = new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      weekday: 'short',
    })
      .format(now)
      .toUpperCase()
      .slice(0, 3) as
      | 'MON'
      | 'TUE'
      | 'WED'
      | 'THU'
      | 'FRI'
      | 'SAT'
      | 'SUN'

    // Build a zero-padded HH:MM string for the current local time.
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: tz,
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(now)

    const hour = parts.find((p) => p.type === 'hour')?.value ?? '00'
    const minute = parts.find((p) => p.type === 'minute')?.value ?? '00'
    const currentTime = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`

    const { schedule, lunch_break } = office.operating_hours

    if (!schedule || schedule.length === 0) return 'unknown'

    // Find a schedule entry that covers today.
    const todayEntry = schedule.find((entry) => entry.days.includes(dayStr))
    if (!todayEntry) return 'closed' // not a working day

    // Check if within opening window.
    if (currentTime < todayEntry.open || currentTime >= todayEntry.close) {
      return 'closed'
    }

    // Check if currently in a lunch break that covers today.
    if (lunch_break && lunch_break.days.includes(dayStr)) {
      if (
        currentTime >= lunch_break.start &&
        currentTime < lunch_break.end
      ) {
        return 'closed'
      }
    }

    return 'open'
  } catch {
    return 'unknown'
  }
}

// ---------------------------------------------------------------------------
// getStatusLabel
// ---------------------------------------------------------------------------

const STATUS_LABELS: Record<string, Record<'open' | 'closed' | 'unknown', string>> = {
  en: { open: 'Open now', closed: 'Closed', unknown: 'Check hours' },
  ms: { open: 'Buka sekarang', closed: 'Tutup', unknown: 'Semak waktu' },
  id: { open: 'Buka sekarang', closed: 'Tutup', unknown: 'Periksa jam' },
}

export function getStatusLabel(
  status: 'open' | 'closed' | 'unknown',
  lang: string
): string {
  const base = lang.split('-')[0]
  const labels = STATUS_LABELS[base] ?? STATUS_LABELS['en']
  return labels[status]
}

// ---------------------------------------------------------------------------
// buildGoogleMapsUrl
// ---------------------------------------------------------------------------

export function buildGoogleMapsUrl(office: GovernmentOffice): string {
  const { lat, lng } = office.coordinates
  const params = new URLSearchParams({
    api: '1',
    destination: `${lat},${lng}`,
    travelmode: 'driving',
  })
  if (office.maps_place_id) {
    params.set('destination_place_id', office.maps_place_id)
  }
  return `https://www.google.com/maps/dir/?${params.toString()}`
}

// ---------------------------------------------------------------------------
// buildStaticMapUrl
// Routes through the Next.js /api/static-map proxy so the Google Maps API
// key stays server-side and never reaches the browser.
// ---------------------------------------------------------------------------

export function buildStaticMapUrl(
  office: GovernmentOffice,
  width: number,
  height: number
): string {
  const { lat, lng } = office.coordinates
  const params = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    width: String(width),
    height: String(height),
  })
  return `/api/static-map?${params.toString()}`
}
