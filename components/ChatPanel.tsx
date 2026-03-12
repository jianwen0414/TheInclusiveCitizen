"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Check } from "lucide-react"
import { AIChatInput } from "@/components/ui/ai-chat-input"
import { MessageBubble, TypingIndicator, Message } from "./MessageBubble"
import { WaveformVisualizer } from "./WaveformVisualizer"
import { Persona } from "./PersonaSelector"
import { cn } from "@/lib/utils"
import { transcribeAudio } from "@/lib/api"

interface ChatPanelProps {
  messages: Message[]
  isProcessing: boolean
  processingStep: string
  onSendMessage: (message: string, detectedLang?: string) => void
  onViewSource: (message: Message) => void
  onShare: (message: Message) => void
  persona: Persona
  showBackupAI?: boolean
  showOfflineTranslation?: boolean
  isWelcomeMode?: boolean
}

const processingSteps = [
  "Transcribing",
  "Detecting Language",
  "Searching Documents",
  "Generating Answer",
  "Translating",
  "Simplifying",
  "Validating"
]

export function ChatPanel({
  messages,
  isProcessing,
  processingStep,
  onSendMessage,
  onViewSource,
  onShare,
  persona,
  isWelcomeMode = false
}: ChatPanelProps) {
  const [inputValue, setInputValue] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [detectedLanguage, setDetectedLanguage] = useState("English")
  const [isTranscribing, setIsTranscribing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const voiceLangRef = useRef<string | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isProcessing])

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim(), voiceLangRef.current || undefined)
      setInputValue("")
      voiceLangRef.current = null
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" })
      audioChunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })

        setIsTranscribing(true)
        try {
          const result = await transcribeAudio(audioBlob)
          setInputValue(result.text)
          setDetectedLanguage(result.detected_language)
          voiceLangRef.current = result.detected_language
        } catch (err) {
          console.error("Transcription failed:", err)
        } finally {
          setIsTranscribing(false)
        }
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
    } catch (err) {
      console.error("Microphone access denied:", err)
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }, [])

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopRecording])

  // Welcome mode - just show input
  if (isWelcomeMode) {
    return (
      <div className="w-full">
        <WaveformVisualizer isRecording={isRecording} />
        <AIChatInput
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSend={handleSend}
          onKeyDown={handleKeyDown}
          isRecording={isRecording}
          onToggleVoice={toggleRecording}
          detectedLanguage={detectedLanguage}
          persona={persona}
        />
      </div>
    )
  }

  // Get current step index for progress display
  const currentStepIndex = processingSteps.findIndex(s => 
    processingStep.toLowerCase().includes(s.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full bg-page-bg">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6">
          <div className="flex flex-col gap-6">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onViewSource={() => onViewSource(message)}
                onShare={() => onShare(message)}
              />
            ))}
            
            {/* Processing indicator with step pills */}
            {isProcessing && (
              <div className="flex flex-col gap-3">
                <TypingIndicator step={processingStep} />
                <div className="flex flex-wrap gap-2 ml-4">
                  {processingSteps.map((step, i) => (
                    <span
                      key={step}
                      className={cn(
                        "inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium transition-colors",
                        i < currentStepIndex
                          ? "bg-pill-bg text-text-secondary"
                          : i === currentStepIndex
                          ? "bg-blue-tint text-primary"
                          : "bg-pill-bg text-text-placeholder"
                      )}
                    >
                      {i < currentStepIndex && <Check className="w-3 h-3" />}
                      {step}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Input bar */}
      <div className="shrink-0 pb-6 px-4">
        <div className="max-w-3xl mx-auto">
          <WaveformVisualizer isRecording={isRecording} />
          <AIChatInput
            inputValue={inputValue}
            onInputChange={setInputValue}
            onSend={handleSend}
            onKeyDown={handleKeyDown}
            isRecording={isRecording}
            onToggleVoice={toggleRecording}
            detectedLanguage={detectedLanguage}
            persona={persona}
          />
        </div>
      </div>
    </div>
  )
}
