"use client"

import { useState, useCallback } from "react"
import { MessageSquare, Info, Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PersonaSelector, Persona } from "@/components/PersonaSelector"
import { LanguageDisplay } from "@/components/LanguageDisplay"
import { ChatPanel } from "@/components/ChatPanel"
import { SourcePanel } from "@/components/SourcePanel"
import { ShareModal } from "@/components/ShareModal"
import { Message } from "@/components/MessageBubble"
import { cn } from "@/lib/utils"

// Mock data for initial demo state
const mockMessages: Message[] = [
  {
    id: "1",
    type: "user",
    content: "Am I eligible for BSH government financial aid?"
  },
  {
    id: "2",
    type: "ai",
    content: "You may be eligible for BSH if your household income is below RM2,000 per month. You need to register at your nearest JKM office with your IC and income documents.",
    detectedLanguage: "English",
    readabilityGrade: 5.2,
    semanticScore: 0.94,
    translationModel: "google_tllm",
    sourceDoc: "BSH Eligibility Guide 2025 — JKM (Bahasa Malaysia)",
    sourcePage: "Page 3, Section 2.1",
    sourceExcerpt: "Pemohon mestilah warganegara Malaysia yang mempunyai pendapatan isi rumah tidak melebihi RM2,000 sebulan...",
    confidence: 0.87,
    steps: ["Prepare your IC (MyKad)", "Get income proof or statutory declaration", "Visit your nearest JKM office", "Fill in application form BSH-01", "Wait for confirmation within 14 working days"],
    stepIcons: ["CreditCard", "FileText", "Building2", "ClipboardList", "Clock"]
  },
  {
    id: "3",
    type: "user",
    content: "Bagaimana cara perpanjang permit kerja saya?"
  },
  {
    id: "4",
    type: "ai",
    content: "Untuk perpanjang permit kerja, Anda perlu mengunjungi pejabat JTK bersama majikan Anda. Bawa pasport, permit kerja lama, dan surat dari majikan.",
    detectedLanguage: "Bahasa Indonesia",
    readabilityGrade: 4.8,
    semanticScore: 0.91,
    translationModel: "google_tllm",
    sourceDoc: "Panduan Permit Kerja Asing — JTK (Bahasa Malaysia)",
    sourcePage: "Halaman 5, Seksyen 3.2",
    sourceExcerpt: "Pembaharuan permit kerja hendaklah dibuat sebelum tarikh tamat tempoh...",
    confidence: 0.82,
    steps: ["Siapkan pasport dan permit lama", "Minta surat dari majikan", "Kunjungi pejabat JTK bersama majikan", "Isi borang permohonan", "Bayar yuran pembaharuan"],
    stepIcons: ["FileText", "FileText", "Building2", "ClipboardList", "CreditCard"]
  }
]

const processingSteps = [
  "Transcribing...",
  "Detecting Language...",
  "Searching Documents...",
  "Generating Answer...",
  "Translating...",
  "Simplifying...",
  "Validating Accuracy..."
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
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content
    }
    setMessages((prev) => [...prev, userMessage])

    // Simulate processing
    await simulateProcessing()

    // Add mock AI response
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
    // Find the user query that preceded this AI message
    const messageIndex = messages.findIndex((m) => m.id === message.id)
    const userQuery = messageIndex > 0 ? messages[messageIndex - 1].content : ""
    setShareMessage(message)
    setShareQuery(userQuery)
    setShowShareModal(true)
  }, [messages])

  return (
    <div className={cn(
      "h-screen flex flex-col lg:flex-row overflow-hidden",
      persona === "elderly" && "mode-elderly"
    )}>
      {/* Mobile header */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-card border-b border-border">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
            <MessageSquare className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-heading font-bold text-primary">
            The Inclusive Citizen
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setShowMobileSidebar(!showMobileSidebar)}
        >
          {showMobileSidebar ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
      </div>

      {/* Left Sidebar */}
      <aside className={cn(
        "w-full lg:w-72 shrink-0 bg-card border-r border-border flex flex-col",
        "fixed lg:relative inset-0 top-14 lg:top-0 z-40 lg:z-0 transition-transform duration-300",
        showMobileSidebar ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        {/* Logo section - hidden on mobile */}
        <div className="hidden lg:flex flex-col gap-1 p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary rounded-xl">
              <MessageSquare className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="font-heading font-bold text-primary leading-tight">
                The Inclusive Citizen
              </span>
              <span className="text-xs text-accent font-medium">
                AI-Powered Public Services
              </span>
            </div>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex flex-col gap-6">
            <PersonaSelector
              selectedPersona={persona}
              onSelectPersona={(p) => {
                setPersona(p)
                setShowMobileSidebar(false)
              }}
            />
            
            <LanguageDisplay detectedLanguage={detectedLanguage} />
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 p-4 border-t border-border">
          <div className="flex flex-col gap-2">
            <button className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors">
              <Info className="w-4 h-4" />
              About this project
            </button>
            <p className="text-xs text-muted-foreground">
              USM | V Hack 2026
            </p>
          </div>
        </div>
      </aside>

      {/* Main chat panel */}
      <main className="flex-1 flex flex-col min-w-0 h-[calc(100vh-56px)] lg:h-screen">
        <ChatPanel
          messages={messages}
          isProcessing={isProcessing}
          processingStep={processingStep}
          onSendMessage={handleSendMessage}
          onViewSource={handleViewSource}
          onShare={handleShare}
          persona={persona}
        />
      </main>

      {/* Right source panel */}
      <aside className={cn(
        "w-full lg:w-80 shrink-0 bg-card",
        "fixed lg:relative inset-y-0 right-0 z-50 lg:z-0 transition-transform duration-300",
        showSourcePanel ? "translate-x-0" : "translate-x-full lg:translate-x-full",
        showSourcePanel && "lg:translate-x-0"
      )}>
        <SourcePanel
          message={sourceMessage}
          onClose={() => setShowSourcePanel(false)}
        />
      </aside>

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
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setShowMobileSidebar(false)}
        />
      )}
    </div>
  )
}
