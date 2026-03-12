"use client"

interface TranslationBadgeProps {
  model: "google_tllm" | "nllb_200"
}

export function TranslationBadge({ model }: TranslationBadgeProps) {
  const modelInfo = {
    google_tllm: {
      label: "Google Cloud TLLM",
      className: "bg-blue-tint text-primary"
    },
    nllb_200: {
      label: "NLLB-200 (offline)",
      className: "bg-pill-bg text-text-secondary"
    }
  }

  const info = modelInfo[model]

  return (
    <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${info.className}`}>
      Translated by {info.label}
    </span>
  )
}
