/**
 * GET /api/flood-alerts
 * Server-side proxy for Malaysia's official flood data from data.gov.my.
 * Cached for 5 minutes (revalidate: 300). Fails silently — always returns JSON.
 */
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const upstream = await fetch(
      "https://api.data.gov.my/data-catalogue?id=today_flood",
      { next: { revalidate: 300 } }
    );
    if (!upstream.ok) {
      return NextResponse.json({ alerts: [], source: null });
    }
    const data = await upstream.json();
    // data.gov.my wraps results in a top-level `data` array
    const raw: Record<string, unknown>[] = Array.isArray(data?.data)
      ? data.data
      : Array.isArray(data)
      ? data
      : [];
    const alerts = raw.map((r) => ({
      district: String(r.district ?? r.Daerah ?? r.daerah ?? ""),
      state: String(r.state ?? r.Negeri ?? r.negeri ?? ""),
      level: String(r.level ?? r.Tahap ?? r.tahap ?? ""),
    }));
    return NextResponse.json({
      alerts,
      fetched_at: new Date().toISOString(),
      source: "data.gov.my",
    });
  } catch {
    return NextResponse.json({ alerts: [], source: null });
  }
}
