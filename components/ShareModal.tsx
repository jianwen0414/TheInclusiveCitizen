"use client"

import { X, Download, MessageCircle, QrCode, MessageSquare } from "lucide-react"
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
      <DialogContent className="max-w-md bg-card p-0 overflow-hidden">
        <DialogHeader className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <DialogTitle className="font-heading font-bold text-primary">
              Share Summary Card
            </DialogTitle>
          </div>
        </DialogHeader>

        {/* Shareable card preview */}
        <div className="p-4">
          <div className="bg-card border-2 border-primary rounded-xl p-4 shadow-lg">
            {/* Logo */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
                <MessageSquare className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-heading font-bold text-primary text-sm">
                The Inclusive Citizen
              </span>
            </div>

            {/* Title */}
            <h3 className="font-heading font-bold text-primary mb-3">
              Government Services Summary
            </h3>

            {/* User question */}
            <div className="mb-3">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Your Question:
              </span>
              <p className="text-sm text-primary mt-1">
                {userQuery}
              </p>
            </div>

            {/* Answer */}
            <div className="mb-3">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Answer:
              </span>
              <p className="text-sm text-primary mt-1 leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Steps/Documents */}
            {message.steps && (
              <div className="mb-3">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Required Documents:
                </span>
                <ul className="mt-1 space-y-1">
                  {message.steps.slice(0, 3).map((step, i) => (
                    <li key={i} className="text-sm text-primary flex items-start gap-2">
                      <span className="text-accent">•</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Source attribution */}
            <div className="flex items-center justify-between pt-3 border-t border-border">
              <p className="text-xs text-muted-foreground">
                Source: {message.sourceDoc}
              </p>
              <div className="flex items-center justify-center w-12 h-12 bg-muted rounded-lg">
                <QrCode className="w-8 h-8 text-muted-foreground" />
              </div>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3 p-4 border-t border-border">
          <Button
            variant="outline"
            className="flex-1 gap-2 text-primary hover:bg-indigo"
          >
            <Download className="w-4 h-4" />
            Download PNG
          </Button>
          <Button
            className="flex-1 gap-2 bg-[#25D366] hover:bg-[#1da851] text-white"
          >
            <MessageCircle className="w-4 h-4" />
            Share via WhatsApp
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
