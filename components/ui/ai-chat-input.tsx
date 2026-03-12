"use client"

import * as React from "react"
import { useState, useEffect, useRef } from "react"
import { Globe, Mic, Paperclip, Send } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { cn } from "@/lib/utils"

const PLACEHOLDERS = [
  "Am I eligible for BSH financial aid?",
  "How do I renew my work permit?",
  "What documents do I need for MyKad renewal?",
  "Can I withdraw from KWSP early?",
  "How do I register for MySejahtera?",
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
  const [isActive, setIsActive] = useState(false)
  const [translateActive, setTranslateActive] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Cycle placeholder text when input is inactive
  useEffect(() => {
    if (isActive || inputValue) return

    const interval = setInterval(() => {
      setShowPlaceholder(false)
      setTimeout(() => {
        setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDERS.length)
        setShowPlaceholder(true)
      }, 400)
    }, 3000)

    return () => clearInterval(interval)
  }, [isActive, inputValue])

  // Close expanded state when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        if (!inputValue) setIsActive(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [inputValue])

  const handleActivate = () => {
    setIsActive(true)
    inputRef.current?.focus()
  }

  const containerVariants = {
    collapsed: {
      height: 68,
      boxShadow: "0 2px 8px 0 rgba(26,58,143,0.08)",
      transition: { type: "spring", stiffness: 120, damping: 18 },
    },
    expanded: {
      height: 128,
      boxShadow: "0 8px 32px 0 rgba(26,58,143,0.14)",
      transition: { type: "spring", stiffness: 120, damping: 18 },
    },
  }

  const placeholderContainerVariants = {
    initial: {},
    animate: { transition: { staggerChildren: 0.025 } },
    exit: { transition: { staggerChildren: 0.015, staggerDirection: -1 } },
  }

  const letterVariants = {
    initial: { opacity: 0, filter: "blur(12px)", y: 10 },
    animate: {
      opacity: 1,
      filter: "blur(0px)",
      y: 0,
      transition: {
        opacity: { duration: 0.25 },
        filter: { duration: 0.4 },
        y: { type: "spring", stiffness: 80, damping: 20 },
      },
    },
    exit: {
      opacity: 0,
      filter: "blur(12px)",
      y: -10,
      transition: {
        opacity: { duration: 0.2 },
        filter: { duration: 0.3 },
        y: { type: "spring", stiffness: 80, damping: 20 },
      },
    },
  }

  const translateLabel = translateActive && detectedLanguage
    ? `${detectedLanguage} Detected`
    : "Translate"

  return (
    <motion.div
      ref={wrapperRef}
      className={cn("w-full", className)}
      variants={containerVariants}
      animate={isActive || inputValue ? "expanded" : "collapsed"}
      initial="collapsed"
      style={{ overflow: "hidden", borderRadius: 32, background: "#FAFAF7" }}
      onClick={handleActivate}
    >
      <div className="flex flex-col items-stretch w-full h-full">
        {/* Input Row */}
        <div className="flex items-center gap-2 p-3 rounded-full bg-[#FAFAF7] w-full">
          {/* Paperclip — hidden per requirements */}
          <button
            className="p-3 rounded-full transition"
            title="Attach file"
            type="button"
            tabIndex={-1}
            style={{ display: "none" }}
            aria-hidden="true"
          >
            <Paperclip size={20} />
          </button>

          {/* Text Input & Animated Placeholder */}
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={onKeyDown}
              onFocus={handleActivate}
              className={cn(
                "border-0 outline-none rounded-md py-2 text-base bg-transparent w-full font-body text-foreground",
                persona === "elderly" && "text-lg",
              )}
              style={{ position: "relative", zIndex: 1 }}
              aria-label="Chat input"
            />
            <div className="absolute left-0 top-0 w-full h-full pointer-events-none flex items-center py-2">
              <AnimatePresence mode="wait">
                {showPlaceholder && !isActive && !inputValue && (
                  <motion.span
                    key={placeholderIndex}
                    className="absolute left-0 top-1/2 -translate-y-1/2 text-muted-foreground select-none pointer-events-none text-base"
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

          {/* Voice toggle button */}
          <div className="relative">
            {isRecording && (
              <span className="absolute inset-0 rounded-full bg-teal/40 animate-pulse-ring" />
            )}
            <button
              className={cn(
                "p-3 rounded-full transition-all",
                isRecording
                  ? "bg-[#00C9A7] text-white"
                  : "hover:bg-indigo text-foreground"
              )}
              title="Voice input"
              type="button"
              tabIndex={-1}
              onClick={(e) => {
                e.stopPropagation()
                onToggleVoice()
              }}
            >
              <Mic size={20} />
            </button>
          </div>

          {/* Send button */}
          <button
            className="flex items-center gap-1 bg-[#1A3A8F] hover:bg-[#1A3A8F]/90 text-white p-3 rounded-full font-medium justify-center transition-colors disabled:opacity-40"
            title="Send"
            type="button"
            tabIndex={-1}
            disabled={!inputValue.trim()}
            onClick={(e) => {
              e.stopPropagation()
              onSend()
            }}
          >
            <Send size={18} />
          </button>
        </div>

        {/* Expanded Controls */}
        <motion.div
          className="w-full flex justify-start px-4 items-center text-sm"
          variants={{
            hidden: {
              opacity: 0,
              y: 20,
              pointerEvents: "none" as const,
              transition: { duration: 0.25 },
            },
            visible: {
              opacity: 1,
              y: 0,
              pointerEvents: "auto" as const,
              transition: { duration: 0.35, delay: 0.08 },
            },
          }}
          initial="hidden"
          animate={isActive || inputValue ? "visible" : "hidden"}
          style={{ marginTop: 8 }}
        >
          <div className="flex gap-3 items-center">
            {/* Translate Toggle */}
            <motion.button
              className={cn(
                "flex items-center px-4 gap-1.5 py-2 rounded-full transition font-medium whitespace-nowrap overflow-hidden justify-start font-body",
                translateActive
                  ? "bg-[#00C9A7]/10 outline outline-[#00C9A7]/60 text-[#1A3A8F]"
                  : "bg-indigo text-foreground hover:bg-indigo/80"
              )}
              title="Translate"
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setTranslateActive((a) => !a)
              }}
              initial={false}
              animate={{
                width: translateActive ? "auto" : 40,
                paddingLeft: translateActive ? 16 : 10,
              }}
            >
              <Globe size={16} className="shrink-0" />
              <motion.span
                className="pb-[1px] text-sm"
                initial={false}
                animate={{ opacity: translateActive ? 1 : 0, width: translateActive ? "auto" : 0 }}
              >
                {translateLabel}
              </motion.span>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

export { AIChatInput }
