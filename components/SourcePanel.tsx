"use client"

import { X, FileText, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Message } from "./MessageBubble"

interface SourcePanelProps {
  message: Message | null
  onClose: () => void
}

export function SourcePanel({ message, onClose }: SourcePanelProps) {
  if (!message) return null

  return (
    <div className="flex flex-col h-full bg-surface">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          <h2 className="text-base font-medium text-text-primary">
            Official Source
          </h2>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="text-text-secondary hover:text-text-primary hover:bg-border-subtle rounded-full"
        >
          <X className="w-5 h-5" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-4">
          {/* Language note */}
          <p className="text-sm text-text-secondary leading-relaxed">
            This answer was translated from the official Bahasa Malaysia government document below.
          </p>

          {/* Source document card */}
          <div className="flex flex-col gap-4 p-4 bg-sidebar-bg rounded-2xl">
            {/* Document name */}
            <div className="flex flex-col gap-1">
              <h3 className="font-medium text-text-primary">
                {message.sourceDoc}
              </h3>
              <span className="text-sm text-text-secondary">
                {message.sourcePage}
              </span>
            </div>

            {/* What this says */}
            <div className="flex flex-col gap-2">
              <span className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                In plain {message.detectedLanguage}:
              </span>
              <p className="text-sm text-text-primary leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Original BM excerpt */}
            <div className="flex flex-col gap-2">
              <span className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Original (Bahasa Malaysia):
              </span>
              <blockquote className="pl-3 border-l-[3px] border-primary bg-sidebar-bg p-3 rounded-r-lg">
                <p className="text-sm text-text-primary italic leading-relaxed">
                  {message.sourceExcerpt}
                </p>
              </blockquote>
            </div>

            {/* Confidence score */}
            {message.confidence !== undefined && (
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">Retrieval Confidence</span>
                  <span className="text-sm font-medium text-primary">
                    {Math.round(message.confidence * 100)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-border-subtle overflow-hidden">
                  <div 
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${message.confidence * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Open PDF button */}
            <Button
              variant="ghost"
              className="w-full gap-2 text-primary hover:text-primary hover:bg-blue-tint justify-center"
            >
              <ExternalLink className="w-4 h-4" />
              Open Original PDF
            </Button>
          </div>

          {/* Disclaimer */}
          <p className="text-xs text-text-secondary leading-relaxed">
            Information sourced from official government documents. Please verify with the relevant officer if needed.
          </p>
        </div>
      </div>
    </div>
  )
}
