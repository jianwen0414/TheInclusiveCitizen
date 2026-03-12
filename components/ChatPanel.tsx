"use client"

import { useState, useRef, useEffect } from "react"
import { Mic, Send, AlertTriangle, RefreshCw, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { MessageBubble, TypingIndicator, Message } from "./MessageBubble"
import { WaveformVisualizer } from "./WaveformVisualizer"
import { Persona } from "./PersonaSelector"
import { cn } from "@/lib/utils"

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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isProcessing])

  const handleSend = () => {
    if (inputValue.trim()) {
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
        
        <div className="flex items-center gap-3">
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type or speak in any language..."
            className={cn(
              "flex-1 h-12 bg-cream border-border",
              persona === "elderly" && "text-lg"
            )}
          />
          
          {/* Mic button */}
          <div className="relative">
            {isRecording && (
              <span className="absolute inset-0 rounded-full bg-accent animate-pulse-ring" />
            )}
            <Button
              size="icon"
              onClick={toggleRecording}
              className={cn(
                "w-14 h-14 rounded-full shrink-0 transition-all",
                isRecording
                  ? "bg-red-500 hover:bg-red-600 text-white"
                  : "bg-accent hover:bg-accent/90 text-accent-foreground",
                persona === "rural" && "ring-4 ring-accent/30"
              )}
            >
              <Mic className="w-6 h-6" />
            </Button>
          </div>

          {/* Send button */}
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="w-12 h-12 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground shrink-0"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>

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
