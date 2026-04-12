import { NextRequest, NextResponse } from 'next/server'

/**
 * Proxy for Google Maps Static API images.
 *
 * Accepts: GET /api/static-map?lat=<lat>&lng=<lng>&width=<w>&height=<h>
 *
 * The GOOGLE_MAPS_API_KEY environment variable is resolved server-side and
 * never exposed to the browser. Images are cached for 24 hours at the CDN
 * / reverse proxy layer.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)

  const lat = searchParams.get('lat')
  const lng = searchParams.get('lng')
  const width = searchParams.get('width') ?? '400'
  const height = searchParams.get('height') ?? '160'

  if (!lat || !lng) {
    return NextResponse.json(
      { error: 'lat and lng query parameters are required' },
      { status: 400 }
    )
  }

  const apiKey = process.env.GOOGLE_MAPS_API_KEY
  if (!apiKey) {
    return NextResponse.json(
      { error: 'Google Maps API key is not configured on this server' },
      { status: 503 }
    )
  }

  const mapsUrl = new URL('https://maps.googleapis.com/maps/api/staticmap')
  mapsUrl.searchParams.set('center', `${lat},${lng}`)
  mapsUrl.searchParams.set('zoom', '15')
  mapsUrl.searchParams.set('size', `${width}x${height}`)
  mapsUrl.searchParams.set('markers', `color:red|${lat},${lng}`)
  mapsUrl.searchParams.set('key', apiKey)

  let upstream: Response
  try {
    upstream = await fetch(mapsUrl.toString())
  } catch {
    return NextResponse.json(
      { error: 'Failed to reach Google Maps API' },
      { status: 502 }
    )
  }

  if (!upstream.ok) {
    return NextResponse.json(
      { error: `Google Maps API returned ${upstream.status}` },
      { status: upstream.status }
    )
  }

  const imageBuffer = await upstream.arrayBuffer()
  const contentType = upstream.headers.get('content-type') ?? 'image/png'

  return new NextResponse(imageBuffer, {
    status: 200,
    headers: {
      'Content-Type': contentType,
      // Cache at CDN / reverse proxy for 24 h; browsers may cache for 1 h.
      'Cache-Control': 'public, max-age=3600, s-maxage=86400',
    },
  })
}
