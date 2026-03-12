"use client"

import { useState, useCallback } from "react"
import { Menu, Search, PenLine, Settings, HelpCircle, Building2, Briefcase, Heart, CreditCard } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PersonaSelector, Persona } from "@/components/PersonaSelector"
import { LanguageDisplay } from "@/components/LanguageDisplay"
import { ChatPanel } from "@/components/ChatPanel"
import { SourcePanel } from "@/components/SourcePanel"
import { ShareModal } from "@/components/ShareModal"
import { Message } from "@/components/MessageBubble"
import { cn } from "@/lib/utils"

// Mock data for initial demo state
const mockMessages: Message[] = []

const processingSteps = [
  "Transcribing...",
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
  const [messages, setMessages] = useState<Message[]>(mockMessages)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStep, setProcessingStep] = useState("")
  const [detectedLanguage, setDetectedLanguage] = useState("English")
  const [sourceMessage, setSourceMessage] = useState<Message | null>(null)
  const [shareMessage, setShareMessage] = useState<Message | null>(null)
  const [shareQuery, setShareQuery] = useState("")
  const [showSourcePanel, setShowSourcePanel] = useState(false)
  const [showShareModal, setShowShareModal] = useState(false)
  const [showMobileSidebar, setShowMobileSidebar] = useState(false)

  const simulateProcessing = useCallback(async () => {
    setIsProcessing(true)
    for (const step of processingSteps) {
      setProcessingStep(step)
      await new Promise((resolve) => setTimeout(resolve, 500))
    }
    setIsProcessing(false)
  }, [])

  const handleSendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content
    }
    setMessages((prev) => [...prev, userMessage])

    await simulateProcessing()

    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: "ai",
      content: "Based on the official government documents, here is the information you requested. Please visit your nearest government office for verification.",
      detectedLanguage: detectedLanguage,
      readabilityGrade: 5.0,
      semanticScore: 0.89,
      translationModel: "google_tllm",
      sourceDoc: "Government Services Guide 2025 — (Bahasa Malaysia)",
      sourcePage: "Page 1, Section 1.1",
      sourceExcerpt: "Maklumat yang diperlukan untuk permohonan...",
      confidence: 0.85,
      steps: ["Prepare required documents", "Visit government office", "Submit application", "Wait for processing"],
      stepIcons: ["FileText", "Building2", "Send", "Clock"]
    }
    setMessages((prev) => [...prev, aiMessage])
  }, [detectedLanguage, simulateProcessing])

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
                {/* Greeting */}
                <h1 className="text-[40px] font-normal text-primary font-heading mb-2">
                  Hello, there
                </h1>
                <p className="text-[32px] font-normal text-text-secondary font-heading mb-12">
                  Ask about government services in any language
                </p>

                {/* Suggestion cards grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-xl">
                  {/* Card 1 - Wide left */}
                  <button
                    onClick={() => handleSendMessage("Am I eligible for BSH financial aid?")}
                    className="group relative flex flex-col items-start p-5 bg-surface rounded-2xl shadow-elevation-1 hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left md:row-span-2"
                  >
                    <span className="text-sm font-medium text-text-primary mb-2">Check BSH eligibility</span>
                    <span className="text-xs text-text-secondary">Find out if you qualify for government financial assistance</span>
                    <Building2 className="absolute bottom-4 right-4 w-16 h-16 text-border-subtle group-hover:text-border opacity-60" />
                  </button>

                  {/* Card 2 - Top right */}
                  <button
                    onClick={() => handleSendMessage("How do I renew my work permit?")}
                    className="group flex flex-col items-start p-5 bg-surface rounded-2xl shadow-elevation-1 hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left"
                  >
                    <span className="text-sm font-medium text-text-primary mb-1">Renew work permit</span>
                    <Briefcase className="absolute bottom-3 right-3 w-8 h-8 text-border-subtle opacity-60" />
                  </button>

                  {/* Card 3 - Bottom right */}
                  <button
                    onClick={() => handleSendMessage("What healthcare subsidies am I entitled to?")}
                    className="group flex flex-col items-start p-5 bg-surface rounded-2xl shadow-elevation-1 hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left"
                  >
                    <span className="text-sm font-medium text-text-primary mb-1">Find healthcare subsidies</span>
                    <Heart className="absolute bottom-3 right-3 w-8 h-8 text-border-subtle opacity-60" />
                  </button>

                  {/* Card 4 */}
                  <button
                    onClick={() => handleSendMessage("What is the MyKad renewal process?")}
                    className="group flex flex-col items-start p-5 bg-surface rounded-2xl shadow-elevation-1 hover:shadow-elevation-2 hover:-translate-y-0.5 transition-all duration-200 text-left md:col-span-2"
                  >
                    <span className="text-sm font-medium text-text-primary mb-1">MyKad renewal process</span>
                    <CreditCard className="absolute bottom-3 right-3 w-8 h-8 text-border-subtle opacity-60" />
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

      {/* Bottom branding bar */}
      <footer className="shrink-0 h-12 bg-footer-bg flex items-center justify-between px-6">
        <span className="text-sm font-medium text-white font-heading">
          The Inclusive Citizen
        </span>
        <span className="text-sm text-text-placeholder">
          V Hack 2026 — USM
        </span>
      </footer>

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
