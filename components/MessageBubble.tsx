"use client"

import { useState, useEffect, useRef } from "react"
import { Volume2, Loader2, FileText, Share2, BookOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { StepCards } from "./StepCards"
import { TranslationBadge } from "./TranslationBadge"
import { synthesiseSpeech } from "@/lib/api"

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
  audioUrl?: string
  disclaimer?: string
  persona?: string
}

interface MessageBubbleProps {
  message: Message
  onViewSource: () => void
  onShare: () => void
}

export function MessageBubble({ message, onViewSource, onShare }: MessageBubbleProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isLoadingAudio, setIsLoadingAudio] = useState(false)
  const isUser = message.type === "user"

  const handlePlayVoice = async () => {
    if (isPlaying || isLoadingAudio) return

    try {
      let audioSrc = message.audioUrl

      if (!audioSrc) {
        setIsLoadingAudio(true)
        const speed = message.persona === "elderly" ? 0.75 : 1.0
        const lang = message.detectedLanguage?.split("-")[0] || "en"
        const res = await synthesiseSpeech(message.content, lang, speed)
        audioSrc = `data:${res.content_type};base64,${res.audio_base64}`
      }

      setIsLoadingAudio(false)
      setIsPlaying(true)
      const audio = new Audio(audioSrc)
      audio.onended = () => setIsPlaying(false)
      audio.onerror = () => setIsPlaying(false)
      await audio.play()
    } catch {
      setIsLoadingAudio(false)
      setIsPlaying(false)
    }
  }

  // PRD F07/F08: Auto-play voice response for Warga Emas (elderly) persona
  const hasAutoPlayed = useRef(false)
  useEffect(() => {
    if (
      message.persona === "elderly" &&
      message.type === "ai" &&
      message.audioUrl &&
      !hasAutoPlayed.current
    ) {
      hasAutoPlayed.current = true
      handlePlayVoice()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message.audioUrl])

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

          {/* Disclaimer if present */}
          {message.disclaimer && (
            <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-xl">
              <p className="text-xs text-amber-700">{message.disclaimer}</p>
            </div>
          )}

          {/* Action buttons - text style */}
          <div className="flex flex-wrap gap-1 pt-2 border-t border-border-subtle">
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-text-secondary hover:text-primary hover:bg-transparent"
              onClick={handlePlayVoice}
              disabled={isPlaying || isLoadingAudio}
            >
              {isLoadingAudio ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
              {isPlaying ? "Playing..." : isLoadingAudio ? "Loading..." : "Play Voice"}
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
