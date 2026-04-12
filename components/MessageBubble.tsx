"use client"

import { useState } from "react"
import { Volume2, Loader2, FileText, Share2, BookOpen, Waves } from "lucide-react"
import ReactMarkdown from "react-markdown"

const LANGUAGE_NAMES: Record<string, string> = {
  ms: "Bahasa Malaysia",
  "ms-kelantanese": "Bahasa Malaysia - Kelantanese",
  "ms-kedah": "Bahasa Malaysia - Kedah Malay",
  "ms-sabah": "Bahasa Malaysia - Sabah Malay",
  "ms-sarawak": "Bahasa Malaysia - Sarawak Malay",
  id: "Bahasa Indonesia",
  jv: "Javanese",
  en: "English",
  zh: "Chinese",
  ta: "Tamil",
  hi: "Hindi",
  th: "Thai",
  vi: "Vietnamese",
  tl: "Filipino",
  bn: "Bengali",
  ja: "Japanese",
  ko: "Korean",
  iba: "Iban",
  dtp: "Kadazan-Dusun",
  bdr: "Bajau",
}

export function getLanguageName(code: string): string {
  if (!code) return "English"
  const normalized = code.trim()
  // If the full dialect code exists, prefer that.
  if (LANGUAGE_NAMES[normalized]) return LANGUAGE_NAMES[normalized]

  // Otherwise fall back to the base language family (ms/en/tl/etc.)
  const base = normalized.split("-")[0]
  return LANGUAGE_NAMES[base] || normalized
}
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { StepCards } from "./StepCards"
import { TranslationBadge } from "./TranslationBadge"
import { synthesiseSpeech } from "@/lib/api"
import { GovernmentOfficeCardList } from "./GovernmentOfficeCardList"
import { detectOfficesInResponse } from "@/lib/detect-offices"

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
  stepsLoading?: boolean
  audioUrl?: string
  disclaimer?: string
  persona?: string
  isTriageQuestion?: boolean
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

  if (message.isTriageQuestion) {
    return (
      <div className="flex flex-col gap-2">
        <div className="max-w-[90%] border-l-4 border-amber-500 bg-amber-950/60 rounded-r-2xl px-4 py-3">
          <div className="flex items-center gap-2 mb-1.5">
            <Waves className="w-4 h-4 text-amber-400 shrink-0" />
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
              Flood Response
            </span>
          </div>
          <p className="text-sm text-amber-200 leading-relaxed">{message.content}</p>
        </div>
      </div>
    )
  }

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
          {/* Main answer — render markdown so **bold** and * bullets display properly */}
          <div className="text-base text-text-primary leading-relaxed prose prose-sm max-w-none
            prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5
            prose-strong:text-text-primary prose-headings:text-text-primary">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {/* Language tag pill */}
          {message.detectedLanguage && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex px-3 py-1 rounded-full text-sm font-medium bg-blue-tint text-primary">
                {getLanguageName(message.detectedLanguage)} · Simplified
              </span>
            </div>
          )}

          {/* Readability badge */}
          {message.readabilityGrade !== undefined && message.readabilityGrade > 0 && (
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-text-secondary" />
              <span className="text-sm text-text-secondary">
                Reading Level: Grade {message.readabilityGrade.toFixed(1)}
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

      {/* Step cards — shown when ready; skeleton while extracting */}
      {message.steps && message.stepIcons && (
        <StepCards steps={message.steps} stepIcons={message.stepIcons} />
      )}
      {message.stepsLoading && !message.steps && (
        <div className="flex gap-3 overflow-x-hidden pb-2 -mx-2 px-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="flex flex-col gap-2 min-w-[140px] max-w-[140px] p-3 bg-surface rounded-2xl shadow-elevation-1 shrink-0 animate-pulse"
            >
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-border-subtle" />
                <div className="w-4 h-4 rounded bg-border-subtle" />
              </div>
              <div className="h-3 rounded bg-border-subtle w-full" />
              <div className="h-3 rounded bg-border-subtle w-3/4" />
            </div>
          ))}
        </div>
      )}

      {/* Government Office Cards — rendered outside the response bubble */}
      <GovernmentOfficeCardList
        offices={detectOfficesInResponse(message.content)}
        detectedLanguage={message.detectedLanguage || "en"}
      />
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
