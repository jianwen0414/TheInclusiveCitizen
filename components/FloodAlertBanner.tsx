"use client"

import { useState, useEffect } from "react"
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react"

interface FloodAlert {
  district: string
  state: string
  level: string
}

interface FloodAlertData {
  alerts: FloodAlert[]
  fetched_at?: string
  source: string | null
}

export function FloodAlertBanner() {
  const [data, setData] = useState<FloodAlertData | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    fetch("/api/flood-alerts")
      .then((r) => r.json())
      .then((d: FloodAlertData) => setData(d))
      .catch(() => setData({ alerts: [], source: null }))
  }, [])

  if (!data || data.alerts.length === 0) return null

  const shown = expanded ? data.alerts : data.alerts.slice(0, 5)
  const remaining = data.alerts.length - 5

  return (
    <div className="mx-4 mt-3 mb-1 rounded-xl border border-amber-500 bg-amber-950 px-4 py-3 text-amber-200 shrink-0">
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-semibold text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            LIVE FLOOD ALERTS ACTIVE —{" "}
            {data.alerts.length} district{data.alerts.length !== 1 ? "s" : ""} affected
          </span>
        </div>
        {data.alerts.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300 transition-colors shrink-0"
          >
            View districts
            {expanded ? (
              <ChevronUp className="w-3 h-3" />
            ) : (
              <ChevronDown className="w-3 h-3" />
            )}
          </button>
        )}
      </div>

      {/* District list */}
      {expanded && (
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-amber-300">
          {shown.map((a, i) => (
            <span key={i}>
              {a.district}{a.state ? `, ${a.state}` : ""}
            </span>
          ))}
          {!expanded && remaining > 0 && (
            <span className="text-amber-500">+{remaining} more</span>
          )}
        </div>
      )}

      {/* Source line */}
      {data.source && data.fetched_at && (
        <p className="mt-1.5 text-[11px] text-amber-500/70">
          Source: {data.source} · Updated {new Date(data.fetched_at).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}
