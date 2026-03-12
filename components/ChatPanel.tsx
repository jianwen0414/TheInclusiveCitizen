"use client"

import { useState, useRef, useEffect } from "react"
import { AlertTriangle, RefreshCw, Users } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { AIChatInput } from "@/components/ui/ai-chat-input"
import { MessageBubble, TypingIndicator, Message } from "./MessageBubble"
import { WaveformVisualizer } from "./WaveformVisualizer"
import { Persona } from "./PersonaSelector"

interface ChatPanelProps {
  messages: Message[]
  isProcessing: boolean
  processingStep: string
  onSendMessage: (message: string) => void
  onViewSource: (message: Message) => void
  onShare: (message: Message) => void
  persona: Persona
  showBackupAI?: boolean
  showOfflineTranslation?: boolean
}

const exampleQueries = [
  { text: "Am I eligible for BSH aid?", lang: "English" },
  { text: "Bagaimana cara perpanjang permit kerja?", lang: "Indonesian" },
  { text: "ฉันมีสิทธิ์ได้รับความช่วยเหลือจากรัฐบาลไหม?", lang: "Thai" }
]

export function ChatPanel({
  messages,
  isProcessing,
  processingStep,
  onSendMessage,
  onViewSource,
  onShare,
  persona,
  showBackupAI = false,
  showOfflineTranslation = false
}: ChatPanelProps) {
  const [inputValue, setInputValue] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [detectedLanguage, setDetectedLanguage] = useState("English")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isProcessing])

  const handleSend = () => {
    if (inputValue.trim()) {
      // Simple heuristic for detected language display
      const hasMalay = /\b(bagaimana|apa|saya|boleh|untuk)\b/i.test(inputValue)
      const hasThai = /[\u0E00-\u0E7F]/.test(inputValue)
      const hasChinese = /[\u4E00-\u9FFF]/.test(inputValue)
      if (hasThai) setDetectedLanguage("Thai")
      else if (hasChinese) setDetectedLanguage("Chinese")
      else if (hasMalay) setDetectedLanguage("Bahasa Melayu")
      else setDetectedLanguage("English")
      onSendMessage(inputValue.trim())
      setInputValue("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // In a real app, this would use MediaRecorder API
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full bg-cream">
      {/* Header */}
      <div className="shrink-0 p-4 border-b border-border bg-card">
        <div className="flex flex-col gap-2">
          <h1 className="font-heading text-xl font-bold text-primary">
            The Inclusive Citizen
          </h1>
          <p className="text-sm text-muted-foreground">
            Ask about Malaysian government services in any language
          </p>
          
          {/* Status badges */}
          {(showBackupAI || showOfflineTranslation) && (
            <div className="flex flex-wrap gap-2 mt-2">
              {showBackupAI && (
                <Badge variant="secondary" className="gap-1 bg-amber-100 text-amber-800 border-0">
                  <AlertTriangle className="w-3 h-3" />
                  Backup AI Model Active
                </Badge>
              )}
              {showOfflineTranslation && (
                <Badge variant="secondary" className="gap-1 bg-blue-100 text-blue-800 border-0">
                  <RefreshCw className="w-3 h-3" />
                  Offline Translation Active
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center px-4">
            {/* Illustration placeholder */}
            <div className="flex items-center justify-center w-24 h-24 bg-indigo rounded-full">
              <Users className="w-12 h-12 text-primary" />
            </div>
            
            <div className="flex flex-col gap-2">
              <h2 className="font-heading text-lg font-semibold text-primary">
                Ask me about government services
              </h2>
              <p className="text-sm text-muted-foreground max-w-md">
                Ask in any language - I'll find the answer from official documents and translate it for you.
              </p>
            </div>

            {/* Example query chips */}
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {exampleQueries.map((query, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(query.text)}
                  className="px-4 py-2 bg-card border border-border rounded-full text-sm text-primary hover:bg-indigo hover:border-accent transition-colors"
                >
                  <span className="text-muted-foreground text-xs mr-1">
                    ({query.lang})
                  </span>
                  {query.text}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onViewSource={() => onViewSource(message)}
                onShare={() => onShare(message)}
              />
            ))}
            {isProcessing && <TypingIndicator step={processingStep} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="shrink-0 p-4 bg-card border-t border-border">
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

        {/* Hint text */}
        <p className="text-xs text-muted-foreground text-center mt-2">
          {persona === "rural"
            ? "Tap the microphone to speak"
            : "Speak in your language — we'll handle the rest"
          }
        </p>
      </div>
    </div>
  )
}
