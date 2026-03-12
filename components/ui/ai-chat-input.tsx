"use client"

import * as React from "react"
import { useState, useEffect, useRef } from "react"
import { Globe, Mic, Plus, Send } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { cn } from "@/lib/utils"

const PLACEHOLDERS = [
  "Ask about government services...",
  "Am I eligible for BSH financial aid?",
  "How do I renew my work permit?",
  "What documents do I need for MyKad renewal?",
  "Can I withdraw from KWSP early?",
  "What healthcare subsidies am I entitled to?",
]

interface AIChatInputProps {
  inputValue: string
  onInputChange: (value: string) => void
  onSend: () => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void
  isRecording: boolean
  onToggleVoice: () => void
  detectedLanguage?: string
  className?: string
  persona?: string
}

const AIChatInput = ({
  inputValue,
  onInputChange,
  onSend,
  onKeyDown,
  isRecording,
  onToggleVoice,
  detectedLanguage,
  className,
  persona,
}: AIChatInputProps) => {
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [showPlaceholder, setShowPlaceholder] = useState(true)
  const [isFocused, setIsFocused] = useState(false)
  const [translateActive, setTranslateActive] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Cycle placeholder text when input is inactive
  useEffect(() => {
    if (isFocused || inputValue) return

    const interval = setInterval(() => {
      setShowPlaceholder(false)
      setTimeout(() => {
        setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDERS.length)
        setShowPlaceholder(true)
      }, 400)
    }, 3000)

    return () => clearInterval(interval)
  }, [isFocused, inputValue])

  // Close expanded state when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        if (!inputValue) setIsFocused(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [inputValue])

  const handleActivate = () => {
    setIsFocused(true)
    inputRef.current?.focus()
  }

  const placeholderContainerVariants = {
    initial: {},
    animate: { transition: { staggerChildren: 0.02 } },
    exit: { transition: { staggerChildren: 0.01, staggerDirection: -1 } },
  }

  const letterVariants = {
    initial: { opacity: 0, filter: "blur(8px)", y: 6 },
    animate: {
      opacity: 1,
      filter: "blur(0px)",
      y: 0,
      transition: {
        opacity: { duration: 0.2 },
        filter: { duration: 0.3 },
        y: { type: "spring", stiffness: 100, damping: 20 },
      },
    },
    exit: {
      opacity: 0,
      filter: "blur(8px)",
      y: -6,
      transition: {
        opacity: { duration: 0.15 },
        filter: { duration: 0.2 },
        y: { type: "spring", stiffness: 100, damping: 20 },
      },
    },
  }

  const translateLabel = translateActive && detectedLanguage
    ? `${detectedLanguage} Detected`
    : "Translate"

  const showSendButton = inputValue.trim().length > 0

  return (
    <div
      ref={wrapperRef}
      className={cn(
        "w-full bg-surface border rounded-3xl transition-all duration-200",
        isFocused || inputValue ? "border-primary shadow-elevation-2" : "border-border-subtle shadow-elevation-1",
        className
      )}
      onClick={handleActivate}
    >
      <div className="flex flex-col">
        {/* Input Row */}
        <div className="flex items-center gap-2 px-4 py-3">
          {/* Text Input & Animated Placeholder */}
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={onKeyDown}
              onFocus={handleActivate}
              onBlur={() => !inputValue && setIsFocused(false)}
              className={cn(
                "border-0 outline-none py-2 text-base bg-transparent w-full font-body text-text-primary placeholder:text-text-placeholder",
                persona === "elderly" && "text-lg",
              )}
              aria-label="Chat input"
            />
            <div className="absolute left-0 top-0 w-full h-full pointer-events-none flex items-center py-2">
              <AnimatePresence mode="wait">
                {showPlaceholder && !isFocused && !inputValue && (
                  <motion.span
                    key={placeholderIndex}
                    className="absolute left-0 top-1/2 -translate-y-1/2 text-text-placeholder select-none pointer-events-none text-base"
                    style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", zIndex: 0 }}
                    variants={placeholderContainerVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                  >
                    {PLACEHOLDERS[placeholderIndex].split("").map((char, i) => (
                      <motion.span
                        key={i}
                        variants={letterVariants}
                        style={{ display: "inline-block" }}
                      >
                        {char === " " ? "\u00A0" : char}
                      </motion.span>
                    ))}
                  </motion.span>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Send button - only visible when there's input */}
          <AnimatePresence>
            {showSendButton && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center justify-center w-10 h-10 bg-primary hover:bg-primary/90 text-white rounded-full transition-colors"
                title="Send"
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onSend()
                }}
              >
                <Send size={18} />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom toolbar row */}
        <div className="flex items-center justify-between px-4 pb-3">
          <div className="flex items-center gap-2">
            {/* Plus button */}
            <button
              className="flex items-center justify-center w-9 h-9 rounded-full text-text-secondary hover:bg-border-subtle transition-colors"
              title="Add attachment"
              type="button"
            >
              <Plus size={20} />
            </button>

            {/* Translate toggle chip */}
            <motion.button
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors",
                translateActive
                  ? "bg-blue-tint text-primary"
                  : "bg-pill-bg text-text-secondary hover:bg-border-subtle"
              )}
              title="Translate"
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setTranslateActive((a) => !a)
              }}
            >
              <Globe size={16} />
              <span>{translateLabel}</span>
            </motion.button>
          </div>

          {/* Mic button */}
          <div className="relative">
            {isRecording && (
              <span className="absolute inset-0 rounded-full bg-teal/40 animate-pulse-ring" />
            )}
            <button
              className={cn(
                "flex items-center justify-center w-9 h-9 rounded-full transition-all",
                isRecording
                  ? "bg-teal text-white"
                  : "text-text-secondary hover:bg-border-subtle"
              )}
              title="Voice input"
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                onToggleVoice()
              }}
            >
              <Mic size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export { AIChatInput }
