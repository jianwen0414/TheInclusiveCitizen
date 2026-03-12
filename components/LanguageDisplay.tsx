"use client"

import { Globe } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface LanguageDisplayProps {
  detectedLanguage: string
}

export function LanguageDisplay({ detectedLanguage }: LanguageDisplayProps) {
  return (
    <div className="flex flex-col gap-3 p-4 bg-card rounded-xl border border-border">
      <div className="flex items-center gap-2">
        <Globe className="w-4 h-4 text-accent" />
        <span className="text-sm font-medium text-muted-foreground">
          Detected Language
        </span>
      </div>
      <Badge 
        variant="secondary" 
        className="w-fit text-sm font-medium bg-indigo text-primary border-0"
      >
        {detectedLanguage}
      </Badge>
      <p className="text-xs text-muted-foreground leading-relaxed">
        Source documents: Bahasa Malaysia (official)
      </p>
    </div>
  )
}
