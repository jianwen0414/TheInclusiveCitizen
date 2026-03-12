"use client"

import { Volume2, FileText, Share2, BookOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { StepCards } from "./StepCards"
import { TranslationBadge } from "./TranslationBadge"
import { cn } from "@/lib/utils"

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
        <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-br-md bg-accent text-accent-foreground">
          <p className="text-base leading-relaxed">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="max-w-[90%] bg-card border-l-4 border-l-primary rounded-2xl rounded-tl-md shadow-sm overflow-hidden">
        <div className="p-4 flex flex-col gap-3">
          {/* Main answer */}
          <p className="text-base text-primary leading-relaxed">
            {message.content}
          </p>

          {/* Language tag pill */}
          {message.detectedLanguage && (
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="bg-indigo text-primary border-0">
                {message.detectedLanguage} → Plain {message.detectedLanguage}
              </Badge>
            </div>
          )}

          {/* Readability badge */}
          {message.readabilityGrade && (
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Reading Level: Grade {message.readabilityGrade}
              </span>
            </div>
          )}

          {/* Semantic Accuracy bar */}
          {message.semanticScore !== undefined && (
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Meaning Accuracy</span>
                <span className="text-sm font-medium text-primary">
                  {Math.round(message.semanticScore * 100)}%
                </span>
              </div>
              <Progress 
                value={message.semanticScore * 100} 
                className="h-2 bg-muted"
              />
            </div>
          )}

          {/* Translation model badge */}
          {message.translationModel && (
            <TranslationBadge model={message.translationModel} />
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-primary hover:bg-indigo hover:text-primary"
            >
              <Volume2 className="w-4 h-4" />
              Play Voice
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-primary hover:bg-indigo hover:text-primary"
              onClick={onViewSource}
            >
              <FileText className="w-4 h-4" />
              View Source
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-primary hover:bg-indigo hover:text-primary"
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
      <div className="bg-card border-l-4 border-l-primary rounded-2xl rounded-tl-md p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-accent rounded-full typing-dot" />
            <span className="w-2 h-2 bg-accent rounded-full typing-dot" />
            <span className="w-2 h-2 bg-accent rounded-full typing-dot" />
          </div>
          <span className="text-sm text-muted-foreground">{step}</span>
        </div>
      </div>
    </div>
  )
}
