"use client"

import { useState, useCallback, useRef } from "react"
import { Menu, Search, PenLine, Settings, HelpCircle, Building2, Briefcase, Heart, CreditCard } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PersonaSelector, Persona } from "@/components/PersonaSelector"
import { LanguageDisplay } from "@/components/LanguageDisplay"
import { ChatPanel } from "@/components/ChatPanel"
import { SourcePanel } from "@/components/SourcePanel"
import { ShareModal } from "@/components/ShareModal"
import { Message } from "@/components/MessageBubble"
import { cn } from "@/lib/utils"
import { queryBackend, extractStepsApi } from "@/lib/api"
import { getLanguageName } from "@/components/MessageBubble"

const PROCESSING_STEPS = [
  "Detecting Language...",
  "Searching Documents...",
  "Generating Answer...",
  "Translating...",
  "Simplifying...",
  "Validating Accuracy..."
]

const recentConversations = [
  "BSH eligibility requirements",
  "Work permit renewal process",
  "Healthcare subsidies info"
]

export default function Home() {
  const [persona, setPersona] = useState<Persona>("elderly")
  const [messages, setMessages] = useState<Message[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStep, setProcessingStep] = useState("")
  const [detectedLanguage, setDetectedLanguage] = useState("English")
  const [sourceMessage, setSourceMessage] = useState<Message | null>(null)
  const [shareMessage, setShareMessage] = useState<Message | null>(null)
  const [shareQuery, setShareQuery] = useState("")
  const [showSourcePanel, setShowSourcePanel] = useState(false)
  const [showShareModal, setShowShareModal] = useState(false)
  const [showMobileSidebar, setShowMobileSidebar] = useState(false)
  const stepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const startProgressAnimation = useCallback(() => {
    let stepIdx = 0
    setIsProcessing(true)
    setProcessingStep(PROCESSING_STEPS[0])

    stepTimerRef.current = setInterval(() => {
      stepIdx++
      if (stepIdx < PROCESSING_STEPS.length) {
        setProcessingStep(PROCESSING_STEPS[stepIdx])
      }
    }, 1200)
  }, [])

  const stopProgressAnimation = useCallback(() => {
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current)
      stepTimerRef.current = null
    }
    setIsProcessing(false)
    setProcessingStep("")
  }, [])

  const handleSendMessage = useCallback(async (content: string, voiceDetectedLang?: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content,
    }
    setMessages((prev) => [...prev, userMessage])

    startProgressAnimation()

    try {
      const response = await queryBackend({
        query: content,
        persona,
        language: voiceDetectedLang || null,
      })

      stopProgressAnimation()

      const langCode = response.detected_language || "en"
      const langName = getLanguageName(langCode)
      setDetectedLanguage(langName)

      const translationModel: "google_tllm" | "nllb_200" | undefined =
        response.translation_model === "google_tllm" ? "google_tllm"
        : response.translation_model === "nllb200" ? "nllb_200"
        : undefined

      const msgId = (Date.now() + 1).toString()
      const aiMessage: Message = {
        id: msgId,
        type: "ai",
        content: response.answer,
        // Keep the full detected language code (e.g. ms-kelantanese)
        // so UI can render dialect-level details reliably.
        detectedLanguage: langCode,
        readabilityGrade: response.readability_grade,
        semanticScore: response.semantic_score,
        translationModel,
        sourceDoc: response.sources[0]?.doc_name || undefined,
        sourcePage: response.sources[0]?.page_number
          ? `Page ${response.sources[0].page_number}`
          : undefined,
        sourceExcerpt: response.sources[0]?.excerpt || response.original_text?.slice(0, 300),
        confidence: response.confidence,
        steps: undefined,
        stepIcons: undefined,
        stepsLoading: true,
        audioUrl: response.audio_url || undefined,
        disclaimer: response.disclaimer || undefined,
        persona,
      }
      setMessages((prev) => [...prev, aiMessage])

      // Fetch steps asynchronously — message is already displayed above.
      extractStepsApi({ answer: response.answer, language: langName }).then((stepsData) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  steps: stepsData.steps.length > 0 ? stepsData.steps : undefined,
                  stepIcons: stepsData.step_icons.length > 0 ? stepsData.step_icons : undefined,
                  stepsLoading: false,
                }
              : m
          )
        )
      }).catch(() => {
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, stepsLoading: false } : m))
        )
      })
    } catch (err) {
      stopProgressAnimation()
      console.error("Query failed:", err)

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: "Sorry, something went wrong while processing your request. Please try again.",
        disclaimer: String(err),
      }
      setMessages((prev) => [...prev, errorMessage])
    }
  }, [persona, startProgressAnimation, stopProgressAnimation])

  const handleViewSource = useCallback((message: Message) => {
    setSourceMessage(message)
    setShowSourcePanel(true)
  }, [])

  const handleShare = useCallback((message: Message) => {
    const messageIndex = messages.findIndex((m) => m.id === message.id)
    const userQuery = messageIndex > 0 ? messages[messageIndex - 1].content : ""
    setShareMessage(message)
    setShareQuery(userQuery)
    setShowShareModal(true)
  }, [messages])

  const handleNewConversation = () => {
    setMessages([])
  }

  return (
    <div className={cn(
      "h-screen flex flex-col",
      persona === "elderly" && "mode-elderly"
    )}>
      <div className="flex-1 flex overflow-hidden">
        {/* Mobile header */}
        <div className="lg:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3 bg-sidebar-bg border-b border-border-subtle">
          <Button
            variant="ghost"
            size="icon"
            className="text-text-primary hover:bg-border-subtle"
            onClick={() => setShowMobileSidebar(!showMobileSidebar)}
          >
            <Menu className="w-5 h-5" />
          </Button>
          <span className="font-heading font-medium text-primary text-lg">
            The Inclusive Citizen
          </span>
          <Button variant="ghost" size="icon" className="text-text-primary hover:bg-border-subtle">
            <Search className="w-5 h-5" />
          </Button>
        </div>

        {/* Left Sidebar - Gemini style */}
        <aside className={cn(
          "w-64 shrink-0 bg-sidebar-bg flex flex-col border-r border-border-subtle",
          "fixed lg:relative inset-y-0 left-0 z-40 transition-transform duration-200 ease-out",
          "pt-14 lg:pt-0",
          showMobileSidebar ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}>
          {/* Top row - Menu + Search */}
          <div className="hidden lg:flex items-center justify-between p-4">
            <Button variant="ghost" size="icon" className="text-text-primary hover:bg-border-subtle rounded-full">
              <Menu className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon" className="text-text-primary hover:bg-border-subtle rounded-full">
              <Search className="w-5 h-5" />
            </Button>
          </div>

          {/* New conversation button */}
          <div className="px-3 pb-4">
            <button
              onClick={handleNewConversation}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-full hover:bg-border-subtle transition-colors duration-150"
            >
              <PenLine className="w-5 h-5 text-text-primary" />
              <span className="text-sm font-medium text-text-primary">New conversation</span>
            </button>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto px-3">
            {/* Personas section */}
            <div className="mb-6">
              <h3 className="px-4 mb-2 text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Personas
              </h3>
              <PersonaSelector
                selectedPersona={persona}
                onSelectPersona={(p) => {
                  setPersona(p)
                  setShowMobileSidebar(false)
                }}
              />
            </div>

            {/* Recent section */}
            <div className="mb-6">
              <h3 className="px-4 mb-2 text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Recent
              </h3>
              <div className="flex flex-col">
                {recentConversations.map((title, i) => (
                  <button
                    key={i}
                    className="px-4 py-2.5 text-left text-sm text-text-secondary hover:bg-border-subtle rounded-lg transition-colors duration-150 truncate"
                  >
                    {title}
                  </button>
                ))}
              </div>
            </div>

            {/* Language display */}
            <div className="mb-6">
              <h3 className="px-4 mb-2 text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Language
              </h3>
              <LanguageDisplay detectedLanguage={detectedLanguage} />
            </div>
          </div>

          {/* Bottom - Settings */}
          <div className="shrink-0 p-3 border-t border-border-subtle">
            <button className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-text-secondary hover:bg-border-subtle rounded-lg transition-colors duration-150">
              <Settings className="w-5 h-5" />
              <span>Settings & help</span>
            </button>
          </div>
        </aside>

        {/* Main content area */}
        <main className="flex-1 flex flex-col min-w-0 pt-14 lg:pt-0">
          {messages.length === 0 ? (
            /* Welcome screen - Gemini style */
            <div className="flex-1 flex flex-col items-center justify-center px-6 pb-32">
              <div className="max-w-2xl w-full flex flex-col items-center text-center">
                {/* Greeting - Gemini gradient style */}
                <h1 className="text-[44px] font-normal font-heading mb-2 gemini-gradient">
                  Hello, there
                </h1>
                <p className="text-[28px] font-normal text-text-secondary font-heading mb-12">
                  Want to try out a few things?
                </p>

                {/* Suggestion cards grid - Gemini style with images */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full max-w-3xl">
                  {/* Card 1 - Tall left */}
                  <button
                    onClick={() => handleSendMessage("Am I eligible for BSH financial aid?")}
                    className="relative flex flex-col justify-between p-4 bg-blue-tint rounded-2xl hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left md:row-span-2 min-h-[180px] overflow-hidden"
                  >
                    <span className="text-sm font-medium text-text-primary pr-12">Check BSH eligibility</span>
                    <Building2 className="absolute bottom-4 right-4 w-14 h-14 text-google-blue/30" />
                  </button>

                  {/* Card 2 - Top center (tall) */}
                  <button
                    onClick={() => handleSendMessage("How do I renew my work permit?")}
                    className="relative flex flex-col justify-between p-4 bg-green-tint rounded-2xl hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left md:row-span-2 min-h-[180px] overflow-hidden"
                  >
                    <span className="text-sm font-medium text-text-primary pr-12">Renew work permit</span>
                    <Briefcase className="absolute bottom-4 right-4 w-14 h-14 text-teal/30" />
                  </button>

                  {/* Card 3 - Top right */}
                  <button
                    onClick={() => handleSendMessage("What healthcare subsidies am I entitled to?")}
                    className="relative flex flex-col justify-start p-4 bg-red-tint rounded-2xl hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left min-h-[85px] overflow-hidden"
                  >
                    <span className="text-sm font-medium text-text-primary pr-10">Find healthcare subsidies</span>
                    <Heart className="absolute bottom-3 right-3 w-10 h-10 text-gemini-coral/30" />
                  </button>

                  {/* Card 4 - Bottom right */}
                  <button
                    onClick={() => handleSendMessage("What is the MyKad renewal process?")}
                    className="relative flex flex-col justify-start p-4 bg-pill-bg rounded-2xl hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left min-h-[85px] overflow-hidden"
                  >
                    <span className="text-sm font-medium text-text-primary pr-10">MyKad renewal process</span>
                    <CreditCard className="absolute bottom-3 right-3 w-10 h-10 text-text-secondary/30" />
                  </button>
                </div>
              </div>

              {/* Input box at bottom of welcome */}
              <div className="absolute bottom-24 left-0 right-0 px-6">
                <div className="max-w-3xl mx-auto">
                  <ChatPanel
                    messages={[]}
                    isProcessing={isProcessing}
                    processingStep={processingStep}
                    onSendMessage={handleSendMessage}
                    onViewSource={handleViewSource}
                    onShare={handleShare}
                    persona={persona}
                    isWelcomeMode
                  />
                </div>
              </div>
            </div>
          ) : (
            /* Chat mode */
            <ChatPanel
              messages={messages}
              isProcessing={isProcessing}
              processingStep={processingStep}
              onSendMessage={handleSendMessage}
              onViewSource={handleViewSource}
              onShare={handleShare}
              persona={persona}
            />
          )}
        </main>

        {/* Right source panel */}
        <aside className={cn(
          "w-80 shrink-0 bg-surface",
          "fixed lg:relative inset-y-0 right-0 z-50 transition-transform duration-200 ease-out",
          "shadow-elevation-3 lg:shadow-none",
          showSourcePanel ? "translate-x-0" : "translate-x-full"
        )}>
          <SourcePanel
            message={sourceMessage}
            onClose={() => setShowSourcePanel(false)}
          />
        </aside>
      </div>

      {/* Share modal */}
      <ShareModal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        message={shareMessage}
        userQuery={shareQuery}
      />

      {/* Mobile sidebar overlay */}
      {showMobileSidebar && (
        <div
          className="fixed inset-0 bg-black/30 z-30 lg:hidden"
          onClick={() => setShowMobileSidebar(false)}
        />
      )}
    </div>
  )
}
