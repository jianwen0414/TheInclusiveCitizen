"use client"

import { Globe } from "lucide-react"

interface LanguageDisplayProps {
  detectedLanguage: string
}

export function LanguageDisplay({ detectedLanguage }: LanguageDisplayProps) {
  return (
    <div className="flex flex-col gap-2 px-4">
      <div className="flex items-center gap-2">
        <Globe className="w-4 h-4 text-primary" />
        <span className="text-sm text-text-secondary">
          Detected: <span className="font-medium text-text-primary">{detectedLanguage}</span>
        </span>
      </div>
      <p className="text-xs text-text-secondary leading-relaxed">
        Source documents: Bahasa Malaysia
      </p>
    </div>
  )
}
