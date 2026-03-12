"use client"

import { Volume2, FileText, Share2, BookOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { StepCards } from "./StepCards"
import { TranslationBadge } from "./TranslationBadge"

export interface Message {
  id: string
  type: "user" | "ai"
  content: string
  detectedLanguage?: string
  readabilityGrade?: number
  semanticScore?: number
  translationModel?: "google_tllm" | "nllb_200"
  sourceDoc?: string
  sourcePage?: string
  sourceExcerpt?: string
  confidence?: number
  steps?: string[]
  stepIcons?: string[]
}

interface MessageBubbleProps {
  message: Message
  onViewSource: () => void
  onShare: () => void
}

export function MessageBubble({ message, onViewSource, onShare }: MessageBubbleProps) {
  const isUser = message.type === "user"

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] px-4 py-3 rounded-3xl bg-pill-bg">
          <p className="text-base text-text-primary leading-relaxed">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="max-w-[90%] bg-surface rounded-2xl shadow-elevation-1 overflow-hidden">
        <div className="p-5 flex flex-col gap-4">
          {/* Main answer */}
          <p className="text-base text-text-primary leading-relaxed">
            {message.content}
          </p>

          {/* Language tag pill */}
          {message.detectedLanguage && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex px-3 py-1 rounded-full text-sm font-medium bg-blue-tint text-primary">
                {message.detectedLanguage} → Plain {message.detectedLanguage}
              </span>
            </div>
          )}

          {/* Readability badge */}
          {message.readabilityGrade && (
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-text-secondary" />
              <span className="text-sm text-text-secondary">
                Reading Level: Grade {message.readabilityGrade}
              </span>
            </div>
          )}

          {/* Semantic Accuracy bar */}
          {message.semanticScore !== undefined && (
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Meaning Accuracy</span>
                <span className="text-sm font-medium text-primary">
                  {Math.round(message.semanticScore * 100)}%
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-border-subtle overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${message.semanticScore * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Translation model badge */}
          {message.translationModel && (
            <TranslationBadge model={message.translationModel} />
          )}

          {/* Action buttons - text style */}
          <div className="flex flex-wrap gap-1 pt-2 border-t border-border-subtle">
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-text-secondary hover:text-primary hover:bg-transparent"
            >
              <Volume2 className="w-4 h-4" />
              Play Voice
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-text-secondary hover:text-primary hover:bg-transparent"
              onClick={onViewSource}
            >
              <FileText className="w-4 h-4" />
              View Source
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-text-secondary hover:text-primary hover:bg-transparent"
              onClick={onShare}
            >
              <Share2 className="w-4 h-4" />
              Share Card
            </Button>
          </div>
        </div>
      </div>

      {/* Step cards */}
      {message.steps && message.stepIcons && (
        <StepCards steps={message.steps} stepIcons={message.stepIcons} />
      )}
    </div>
  )
}

export function TypingIndicator({ step }: { step: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="bg-surface rounded-2xl p-4 shadow-elevation-1">
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-teal rounded-full typing-dot" />
            <span className="w-2 h-2 bg-teal rounded-full typing-dot" />
            <span className="w-2 h-2 bg-teal rounded-full typing-dot" />
          </div>
          <span className="text-sm text-text-secondary">{step}</span>
        </div>
      </div>
    </div>
  )
}
