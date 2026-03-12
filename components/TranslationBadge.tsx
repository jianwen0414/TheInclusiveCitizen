"use client"

import { Badge } from "@/components/ui/badge"

interface TranslationBadgeProps {
  model: "google_tllm" | "nllb_200"
}

export function TranslationBadge({ model }: TranslationBadgeProps) {
  const modelInfo = {
    google_tllm: {
      label: "Google Cloud TLLM",
      className: "bg-indigo text-primary"
    },
    nllb_200: {
      label: "NLLB-200 (offline)",
      className: "bg-amber-100 text-amber-800"
    }
  }

  const info = modelInfo[model]

  return (
    <Badge variant="outline" className={`text-xs ${info.className} border-0`}>
      Translated by {info.label}
    </Badge>
  )
}
