"use client"

import * as LucideIcons from "lucide-react"
import { LucideIcon } from "lucide-react"

interface StepCardsProps {
  steps: string[]
  stepIcons: string[]
}

export function StepCards({ steps, stepIcons }: StepCardsProps) {
  const getIcon = (iconName: string): LucideIcon => {
    const icons = LucideIcons as Record<string, LucideIcon>
    return icons[iconName] || LucideIcons.Circle
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2 -mx-2 px-2 scrollbar-hide">
      {steps.map((step, index) => {
        const Icon = getIcon(stepIcons[index])
        return (
          <div
            key={index}
            className="flex flex-col gap-2 min-w-[140px] max-w-[140px] p-3 bg-surface rounded-2xl shadow-elevation-1 shrink-0"
          >
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-white text-xs font-bold">
                {index + 1}
              </div>
              <Icon className="w-4 h-4 text-primary" />
            </div>
            <p className="text-sm text-text-primary leading-snug">
              {step}
            </p>
          </div>
        )
      })}
    </div>
  )
}
