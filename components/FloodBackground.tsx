"use client"

/**
 * FloodBackground — CSS + SVG animated water waves.
 *
 * No WebGL, no canvas, no useEffect. Three SVG wave layers translate
 * horizontally via CSS keyframes defined in globals.css. The containing
 * div uses overflow:hidden so only one period is visible at a time.
 *
 * The parent (app/chat/page.tsx) must have `position: relative` so that
 * `absolute inset-0` correctly fills it.
 */

interface FloodBackgroundProps {
  onUnmount?: () => void
}

// Wave SVG path — one full sine cycle at 200% width so the seamless
// loop (translateX 0 → -50%) looks continuous.
const WAVE_PATH_A =
  "M0 60 C150 20 350 100 500 60 C650 20 850 100 1000 60 C1150 20 1350 100 1500 60 C1650 20 1850 100 2000 60 L2000 200 L0 200 Z"

const WAVE_PATH_B =
  "M0 80 C120 40 280 120 500 80 C720 40 880 120 1000 80 C1120 40 1280 120 1500 80 C1720 40 1880 120 2000 80 L2000 200 L0 200 Z"

const WAVE_PATH_C =
  "M0 50 C200 10 300 90 500 50 C700 10 800 90 1000 50 C1200 10 1300 90 1500 50 C1700 10 1800 90 2000 50 L2000 200 L0 200 Z"

export function FloodBackground({ onUnmount: _onUnmount }: FloodBackgroundProps) {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      style={{ zIndex: 1 }}
      aria-hidden
    >
      {/* Deep ocean gradient base */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, #020b18 0%, #03163a 40%, #042a5c 70%, #063370 100%)",
        }}
      />

      {/* Wave layer 1 — deep navy, slowest */}
      <div
        className="absolute bottom-0 left-0"
        style={{
          width: "200%",
          height: "35%",
          animation: "flood-wave-fwd 14s linear infinite",
        }}
      >
        <svg
          viewBox="0 0 2000 200"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <path d={WAVE_PATH_A} fill="rgba(3,22,66,0.9)" />
        </svg>
      </div>

      {/* Wave layer 2 — ocean blue, medium */}
      <div
        className="absolute bottom-0 left-0"
        style={{
          width: "200%",
          height: "28%",
          animation: "flood-wave-rev 10s linear infinite",
        }}
      >
        <svg
          viewBox="0 0 2000 200"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <path d={WAVE_PATH_B} fill="rgba(5,38,92,0.85)" />
        </svg>
      </div>

      {/* Wave layer 3 — mid blue with foam tint, fastest */}
      <div
        className="absolute bottom-0 left-0"
        style={{
          width: "200%",
          height: "20%",
          animation: "flood-wave-fwd 7s linear infinite, flood-swell 5s ease-in-out infinite",
        }}
      >
        <svg
          viewBox="0 0 2000 200"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <path d={WAVE_PATH_C} fill="rgba(10,70,160,0.75)" />
        </svg>
      </div>

      {/* Foam highlight layer */}
      <div
        className="absolute bottom-0 left-0"
        style={{
          width: "200%",
          height: "12%",
          animation: "flood-wave-rev 5s linear infinite",
          opacity: 0.45,
        }}
      >
        <svg
          viewBox="0 0 2000 200"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <path d={WAVE_PATH_A} fill="rgba(80,160,230,0.6)" />
        </svg>
      </div>

      {/* Top vignette to blend with the dark header */}
      <div
        className="absolute inset-x-0 top-0"
        style={{
          height: "30%",
          background:
            "linear-gradient(180deg, rgba(2,11,24,0.85) 0%, transparent 100%)",
        }}
      />
    </div>
  )
}
