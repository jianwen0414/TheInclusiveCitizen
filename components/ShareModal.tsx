"use client"

import { Download, MessageCircle, QrCode, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Message } from "./MessageBubble"

interface ShareModalProps {
  isOpen: boolean
  onClose: () => void
  message: Message | null
  userQuery: string
}

export function ShareModal({ isOpen, onClose, message, userQuery }: ShareModalProps) {
  if (!message) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md bg-surface p-0 overflow-hidden rounded-2xl shadow-elevation-3 border-0">
        <DialogHeader className="p-4 border-b border-border-subtle">
          <div className="flex items-center justify-between">
            <DialogTitle className="font-heading font-medium text-text-primary">
              Share Summary Card
            </DialogTitle>
          </div>
        </DialogHeader>

        {/* Shareable card preview */}
        <div className="p-4">
          <div className="bg-surface border border-primary rounded-2xl p-4 shadow-elevation-2">
            {/* Logo */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <span className="font-heading font-medium text-primary text-sm">
                The Inclusive Citizen
              </span>
            </div>

            {/* Title */}
            <h3 className="font-heading font-medium text-text-primary mb-3">
              Government Services Summary
            </h3>

            {/* User question */}
            <div className="mb-3">
              <span className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Your Question:
              </span>
              <p className="text-sm text-text-primary mt-1">
                {userQuery}
              </p>
            </div>

            {/* Answer */}
            <div className="mb-3">
              <span className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                Answer:
              </span>
              <p className="text-sm text-text-primary mt-1 leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Steps/Documents */}
            {message.steps && (
              <div className="mb-3">
                <span className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                  Required Documents:
                </span>
                <ul className="mt-1 space-y-1">
                  {message.steps.slice(0, 3).map((step, i) => (
                    <li key={i} className="text-sm text-text-primary flex items-start gap-2">
                      <span className="text-primary">•</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Source attribution */}
            <div className="flex items-center justify-between pt-3 border-t border-border-subtle">
              <p className="text-xs text-text-secondary">
                Source: {message.sourceDoc}
              </p>
              <div className="flex items-center justify-center w-12 h-12 bg-pill-bg rounded-lg">
                <QrCode className="w-8 h-8 text-text-secondary" />
              </div>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3 p-4 border-t border-border-subtle">
          <Button
            variant="outline"
            className="flex-1 gap-2 text-primary hover:bg-blue-tint border-border-subtle rounded-full"
          >
            <Download className="w-4 h-4" />
            Download PNG
          </Button>
          <Button
            className="flex-1 gap-2 bg-[#25D366] hover:bg-[#1da851] text-white rounded-full"
          >
            <MessageCircle className="w-4 h-4" />
            Share via WhatsApp
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
