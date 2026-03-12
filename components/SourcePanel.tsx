"use client"

import { X, FileText, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Message } from "./MessageBubble"

interface SourcePanelProps {
  message: Message | null
  onClose: () => void
}

export function SourcePanel({ message, onClose }: SourcePanelProps) {
  if (!message) return null

  return (
    <div className="flex flex-col h-full bg-card border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          <h2 className="font-heading font-bold text-primary">
            Official Source (Bahasa Malaysia)
          </h2>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="text-muted-foreground hover:text-primary"
        >
          <X className="w-5 h-5" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-4">
          {/* Language note */}
          <p className="text-sm text-muted-foreground leading-relaxed">
            This answer was translated from the official Bahasa Malaysia government document below.
          </p>

          {/* Source document card */}
          <div className="flex flex-col gap-3 p-4 bg-cream rounded-xl border border-border">
            {/* Document name */}
            <div className="flex flex-col gap-1">
              <h3 className="font-heading font-semibold text-primary">
                {message.sourceDoc}
              </h3>
              <span className="text-sm text-muted-foreground">
                {message.sourcePage}
              </span>
            </div>

            {/* What this says */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                In plain {message.detectedLanguage}:
              </span>
              <p className="text-sm text-primary leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Original BM excerpt */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Original (Bahasa Malaysia):
              </span>
              <blockquote className="pl-3 border-l-4 border-primary bg-indigo/50 p-3 rounded-r-lg">
                <p className="text-sm text-primary italic leading-relaxed">
                  {message.sourceExcerpt}
                </p>
              </blockquote>
            </div>

            {/* Confidence score */}
            {message.confidence !== undefined && (
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Retrieval Confidence</span>
                  <span className="text-sm font-medium text-primary">
                    {Math.round(message.confidence * 100)}%
                  </span>
                </div>
                <Progress 
                  value={message.confidence * 100} 
                  className="h-2 bg-muted"
                />
              </div>
            )}

            {/* Open PDF button */}
            <Button
              variant="outline"
              className="w-full gap-2 text-primary hover:bg-indigo"
            >
              <ExternalLink className="w-4 h-4" />
              Open Original PDF
            </Button>
          </div>

          {/* Disclaimer */}
          <p className="text-xs text-muted-foreground leading-relaxed">
            Information sourced from official government documents. Please verify with the relevant officer if needed.
          </p>
        </div>
      </div>
    </div>
  )
}
